"""
Optimización de hiperparámetros para máxima rentabilidad

Prueba diferentes combinaciones de:
- Edge thresholds
- Kelly fractions
- Filtros de odds
"""

import pandas as pd
import numpy as np
from pathlib import Path
from itertools import product

from src.models.poisson_dc import DixonColes
from src.models.calibration import ProbabilityCalibrator
from src.features.ratings import add_elo
from src.features.rolling import add_form
from src.utils.odds import market_probs_1x2, implied_probs_from_odds, remove_overround
from src.backtest.bankroll import kelly_fraction, bet_decision
from src.backtest.settle import settle_1x2, settle_ou, settle_ah

PROC = Path("data/processed")

# Grid de parámetros a probar
PARAM_GRID_OU = {
    'edge_threshold': [0.03, 0.04, 0.05, 0.06],
    'min_odds': [1.70, 1.75, 1.80],
    'kelly_frac': [0.05, 0.06, 0.07, 0.08]
}

PARAM_GRID_AH = {
    'ev_threshold': [0.03, 0.04, 0.05, 0.06],
    'min_odds': [1.75, 1.80, 1.85, 1.90],
    'kelly_frac': [0.03, 0.04, 0.05, 0.06]
}

def backtest_with_params(df, params_ou, params_ah):
    """
    Ejecuta backtest con parámetros específicos
    
    Returns:
        dict con métricas
    """
    df = add_elo(df)
    df = add_form(df)
    split = df['Date'].quantile(0.7)
    train = df[df['Date']<=split].copy()
    test  = df[df['Date']> split].copy()
    
    dc = DixonColes().fit(train)
    
    # Calibración
    p1x2_train = dc.predict_1x2(train)
    calibrator = ProbabilityCalibrator()
    calibrator.fit(train['y'].values, p1x2_train)
    
    log = []
    bankroll = 100.0
    
    for i, row in test.reset_index(drop=True).iterrows():
        cands = []
        
        # OU 2.5
        if 'B365>2.5' in row.index and 'B365<2.5' in row.index:
            probs = dc.prob_over_under(row, line=2.5)
            p_ou = np.array([probs['pOver'], probs['pUnder']], float)
            odds_ou = np.array([row['B365>2.5'], row['B365<2.5']], float)
            q_ou = remove_overround(implied_probs_from_odds(odds_ou))
            idx2 = int(np.argmax(p_ou - q_ou))
            edge2 = (p_ou - q_ou)[idx2]
            
            if edge2 >= params_ou['edge_threshold'] and odds_ou[idx2] >= params_ou['min_odds']:
                frac = kelly_fraction(p_ou[idx2], odds_ou[idx2], params_ou['kelly_frac'])
                cands.append(dict(market='OU2.5', selection=['Over','Under'][idx2], line=2.5, 
                                 odds=float(odds_ou[idx2]), frac=float(frac),
                                 p_model=float(p_ou[idx2]), p_mkt=float(q_ou[idx2])))
        
        # AH
        if all(c in row.index for c in ['AHh','B365AHH','B365AHA']):
            h = float(row['AHh'])
            oh = float(row['B365AHH'])
            oa = float(row['B365AHA'])
            
            ph = dc.ah_probabilities(row, line=h, side='home')['win']
            pa = dc.ah_probabilities(row, line=h, side='away')['win']
            ev_h = ph*(oh-1.0) - (1-ph)
            ev_a = pa*(oa-1.0) - (1-pa)
            
            if max(ev_h, ev_a) > params_ah['ev_threshold'] and oh >= params_ah['min_odds'] and oa >= params_ah['min_odds']:
                if ev_h >= ev_a:
                    p = max(0.51, ph)
                    frac = kelly_fraction(p, oh, params_ah['kelly_frac'])
                    cands.append(dict(market='AH', selection='Home', line=h, odds=oh, frac=float(frac),
                                     p_model=float(p), p_mkt=float('nan')))
                else:
                    p = max(0.51, pa)
                    frac = kelly_fraction(p, oa, params_ah['kelly_frac'])
                    cands.append(dict(market='AH', selection='Away', line=h, odds=oa, frac=float(frac),
                                     p_model=float(p), p_mkt=float('nan')))
        
        if not cands:
            continue
        
        # Tomar mejor
        def key(x):
            return x['p_model'] - (x['p_mkt'] if isinstance(x['p_mkt'], float) and x['p_mkt']==x['p_mkt'] else 0.5)
        best = max(cands, key=key)
        
        stake = bankroll * max(0.0, best['frac'])
        if stake <= 0:
            continue
        
        # Settle
        if best['market'] == 'OU2.5':
            pnl, res = settle_ou(best['selection'], row['FTHG'], row['FTAG'], stake, best['odds'], 2.5)
        else:  # AH
            pnl, res = settle_ah(best['selection'], best['line'], row['FTHG'], row['FTAG'], stake, best['odds'])
        
        bankroll += pnl
        log.append(dict(date=row['Date'], market=best['market'], result=res, pnl=pnl, 
                       stake=stake, equity=bankroll))
    
    if not log:
        return {'roi': 0, 'sharpe': 0, 'bets': 0, 'hitrate': 0}
    
    log_df = pd.DataFrame(log)
    roi = (log_df['pnl'].sum() / log_df['stake'].sum()) * 100 if log_df['stake'].sum() > 0 else 0
    sharpe = log_df['pnl'].mean() / log_df['pnl'].std() if log_df['pnl'].std() > 0 else 0
    hitrate = (log_df['result'] == 'WIN').mean() * 100
    
    return {
        'roi': roi,
        'sharpe': sharpe,
        'bets': len(log_df),
        'hitrate': hitrate,
        'pnl': log_df['pnl'].sum()
    }

def main():
    print("\n" + "="*70)
    print("  OPTIMIZACIÓN DE HIPERPARÁMETROS")
    print("="*70 + "\n")
    
    print("Cargando datos...")
    df0 = pd.read_parquet(PROC / "matches.parquet")
    
    print("Probando combinaciones de parámetros...\n")
    print("(Esto puede tomar 3-5 minutos)\n")
    
    results = []
    total_combos = len(list(product(*PARAM_GRID_OU.values()))) * len(list(product(*PARAM_GRID_AH.values())))
    tested = 0
    
    best_roi = -999
    best_params = None
    
    # Probar combinaciones
    for ou_combo in product(*PARAM_GRID_OU.values()):
        params_ou = dict(zip(PARAM_GRID_OU.keys(), ou_combo))
        
        for ah_combo in product(*PARAM_GRID_AH.values()):
            params_ah = dict(zip(PARAM_GRID_AH.keys(), ah_combo))
            
            tested += 1
            if tested % 20 == 0:
                print(f"  Progreso: {tested}/{total_combos} combinaciones probadas...")
            
            metrics = backtest_with_params(df0, params_ou, params_ah)
            
            if metrics['roi'] > best_roi and metrics['bets'] >= 300:  # Mínimo 300 apuestas
                best_roi = metrics['roi']
                best_params = {
                    'OU': params_ou,
                    'AH': params_ah,
                    'metrics': metrics
                }
            
            results.append({
                **params_ou,
                **params_ah,
                **metrics
            })
    
    print(f"\n✓ {tested} combinaciones probadas\n")
    
    # Mostrar mejor configuración
    print("="*70)
    print("  MEJOR CONFIGURACIÓN ENCONTRADA")
    print("="*70 + "\n")
    
    if best_params:
        print("OVER/UNDER 2.5:")
        for k, v in best_params['OU'].items():
            print(f"  {k}: {v}")
        
        print("\nASIAN HANDICAP:")
        for k, v in best_params['AH'].items():
            print(f"  {k}: {v}")
        
        print("\nMÉTRICAS:")
        for k, v in best_params['metrics'].items():
            if k == 'roi':
                print(f"  {k}: {v:+.2f}%")
            elif k in ['sharpe', 'hitrate']:
                print(f"  {k}: {v:.2f}")
            else:
                print(f"  {k}: {v}")
    
    # Guardar resultados completos
    results_df = pd.DataFrame(results)
    results_df = results_df.sort_values('roi', ascending=False)
    results_df.to_csv("reports/optimization_results.csv", index=False)
    print(f"\n✓ Resultados completos guardados en: reports/optimization_results.csv")
    print("="*70)

if __name__ == "__main__":
    main()

