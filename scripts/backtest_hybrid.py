"""
BACKTEST HÍBRIDO - Combina lo mejor de Fase 1 y Fase 2

Fase 1 (Estabilidad):
- Split estático 70/30
- Kelly fractions conservadores
- Filtros estrictos

Fase 2 (Innovación):
- Calibración isotónica
- 1X2 reactivado
- Gestión de drawdown

Objetivo: ROI +55-65%, Sharpe 0.30-0.35, Drawdown <40%
"""

import pandas as pd
import numpy as np
from pathlib import Path

from src.models.poisson_dc import DixonColes
from src.models.calibration import ProbabilityCalibrator
from src.features.ratings import add_elo
from src.features.rolling import add_form
from src.utils.odds import market_probs_1x2, implied_probs_from_odds, remove_overround
from src.backtest.bankroll import kelly_fraction, bet_decision
from src.backtest.settle import settle_1x2, settle_ou, settle_ah

PROC = Path("data/processed")
REPORTS = Path("reports"); REPORTS.mkdir(parents=True, exist_ok=True)

def main():
    print("=" * 70)
    print(" BACKTEST HÍBRIDO - FASE 1 + FASE 2")
    print("=" * 70)
    print("\nConfiguracion:")
    print("  - Split: Estático 70/30 (Fase 1)")
    print("  - Calibración: Isotónica (Fase 2)")
    print("  - 1X2: Reactivado con filtros MUY estrictos")
    print("  - Kelly: Conservadores (Fase 1)")
    print("  - Drawdown: Gestión activa (Fase 2)")
    print("=" * 70)
    
    df0 = pd.read_parquet(PROC / "matches.parquet")
    
    # Features
    df = add_elo(df0)
    df = add_form(df)
    
    # Split estático 70/30 (FASE 1)
    split = df['Date'].quantile(0.7)
    train = df[df['Date']<=split].copy()
    test  = df[df['Date']> split].copy()
    
    print(f"\nDatos:")
    print(f"  Train: {len(train)} partidos")
    print(f"  Test:  {len(test)} partidos")
    
    # Entrenar modelo
    print("\nEntrenando modelo Dixon-Coles...")
    dc = DixonColes().fit(train)
    
    # FASE 2: Calibración Isotónica
    print("Aplicando calibración isotónica...")
    p1x2_train = dc.predict_1x2(train)
    calibrator = ProbabilityCalibrator()
    calibrator.fit(train['y'].values, p1x2_train)
    print("  OK - Calibracion completada")
    
    # Predecir probabilidades calibradas para test
    p1x2_test = dc.predict_1x2(test)
    p1x2 = calibrator.transform(p1x2_test)
    
    # Probabilidades del mercado
    mkt = test.apply(market_probs_1x2, axis=1, result_type='expand')
    mkt.columns = ['pH_mkt','pD_mkt','pA_mkt']

    log = []
    bankroll = 100.0
    peak_equity = 100.0
    
    print("\n" + "=" * 70)
    print("EJECUTANDO BACKTEST...")
    print("=" * 70)

    for i, row in test.reset_index(drop=True).iterrows():
        cands = []
        
        # Gestión de drawdown (FASE 2)
        if bankroll > peak_equity:
            peak_equity = bankroll
        drawdown_pct = (peak_equity - bankroll) / peak_equity if peak_equity > 0 else 0.0

        # ============================================================
        # MERCADO 1X2 - REACTIVADO CON CALIBRACIÓN
        # Filtros MUY ESTRICTOS: edge 10%, odds >=2.50, prob >=0.55
        # ============================================================
        p_row = p1x2.iloc[i][['pH','pD','pA']].to_numpy(float)
        q_row = mkt.iloc[i][['pH_mkt','pD_mkt','pA_mkt']].to_numpy(float)
        odds1 = row[['B365H','B365D','B365A']].to_numpy(float)
        idx = int(np.argmax(p_row - q_row))
        edge = (p_row - q_row)[idx]
        
        # HÍBRIDO: edge 10%, odds 2.50+, prob 0.55+, Kelly 3%
        if bet_decision(edge, 0.10) and odds1[idx]>=2.50 and p_row[idx]>=0.55:
            kelly_frac = 0.03  # Conservador (Fase 1)
            if drawdown_pct > 0.10:  # Gestión drawdown (Fase 2)
                kelly_frac *= 0.5
            frac = kelly_fraction(p_row[idx], odds1[idx], kelly_frac)
            cands.append(dict(
                market='1X2', 
                selection=['H','D','A'][idx], 
                line=None, 
                odds=float(odds1[idx]), 
                frac=float(frac),
                p_model=float(p_row[idx]), 
                p_mkt=float(q_row[idx])
            ))

        # ============================================================
        # MERCADO OU 2.5
        # HÍBRIDO: edge 5%, odds 1.85+, Kelly 5%
        # ============================================================
        if 'B365>2.5' in row.index and 'B365<2.5' in row.index:
            probs = dc.prob_over_under(row, line=2.5)
            p_ou = np.array([probs['pOver'], probs['pUnder']], float)
            odds_ou = np.array([row['B365>2.5'], row['B365<2.5']], float)
            q_ou = remove_overround(implied_probs_from_odds(odds_ou))
            idx2 = int(np.argmax(p_ou - q_ou))
            edge2 = (p_ou - q_ou)[idx2]
            
            # HÍBRIDO: edge 5%, odds 1.85, Kelly 5%
            if bet_decision(edge2, 0.05) and odds_ou[idx2]>=1.85:
                kelly_frac = 0.05  # Fase 1
                if drawdown_pct > 0.10:
                    kelly_frac *= 0.5
                frac = kelly_fraction(p_ou[idx2], odds_ou[idx2], kelly_frac)
                cands.append(dict(
                    market='OU2.5', 
                    selection=['Over','Under'][idx2], 
                    line=2.5, 
                    odds=float(odds_ou[idx2]), 
                    frac=float(frac),
                    p_model=float(p_ou[idx2]), 
                    p_mkt=float(q_ou[idx2])
                ))

        # ============================================================
        # MERCADO ASIAN HANDICAP
        # HÍBRIDO: EV 6%, odds 1.90+, Kelly 2.5%
        # ============================================================
        if all(c in row.index for c in ['AHh','B365AHH','B365AHA']):
            h = float(row['AHh'])
            oh = float(row['B365AHH'])
            oa = float(row['B365AHA'])
            
            ph = dc.ah_probabilities(row, line=h, side='home')['win']
            pa = dc.ah_probabilities(row, line=h, side='away')['win']
            ev_h = ph*(oh-1.0) - (1-ph)
            ev_a = pa*(oa-1.0) - (1-pa)
            
            # HÍBRIDO: EV 6%, odds 1.90, Kelly 2.5%
            if max(ev_h, ev_a) > 0.06 and oh >= 1.90 and oa >= 1.90:
                kelly_frac = 0.025  # Fase 1
                if drawdown_pct > 0.10:
                    kelly_frac *= 0.5
                    
                if ev_h >= ev_a:
                    p = max(0.51, ph)
                    frac = kelly_fraction(p, oh, kelly_frac)
                    cands.append(dict(
                        market='AH', 
                        selection='Home', 
                        line=h, 
                        odds=oh, 
                        frac=float(frac), 
                        p_model=float(p), 
                        p_mkt=float('nan')
                    ))
                else:
                    p = max(0.51, pa)
                    frac = kelly_fraction(p, oa, kelly_frac)
                    cands.append(dict(
                        market='AH', 
                        selection='Away', 
                        line=h, 
                        odds=oa, 
                        frac=float(frac), 
                        p_model=float(p), 
                        p_mkt=float('nan')
                    ))

        if not cands:
            continue

        # Seleccionar mejor apuesta
        def key(x):
            return x['p_model'] - (x['p_mkt'] if isinstance(x['p_mkt'], float) and x['p_mkt']==x['p_mkt'] else 0.5)
        best = max(cands, key=key)

        stake = bankroll * max(0.0, best['frac'])
        if stake <= 0: 
            continue

        # Liquidar apuesta
        if best['market']=='1X2':
            pnl, res = settle_1x2({'H':0,'D':1,'A':2}[best['selection']], int(row['y']), stake, best['odds'])
        elif best['market']=='OU2.5':
            pnl, res = settle_ou(best['selection'], row['FTHG'], row['FTAG'], stake, best['odds'], 2.5)
        else:
            pnl, res = settle_ah(best['selection'], best['line'], row['FTHG'], row['FTAG'], stake, best['odds'])

        bankroll += pnl
        log.append(dict(
            date=row['Date'], 
            league=row.get('League',''), 
            home=row['HomeTeam'], 
            away=row['AwayTeam'],
            market=best['market'], 
            selection=best['selection'], 
            line=best['line'], 
            odds_open=best['odds'],
            stake=stake, 
            result=res, 
            pnl=pnl, 
            equity=bankroll, 
            p_model=best['p_model'], 
            p_mkt=best['p_mkt']
        ))

    print("\n" + "=" * 70)
    print("BACKTEST HÍBRIDO COMPLETADO")
    print("=" * 70)
    print(f"\nResumen:")
    print(f"  Apuestas realizadas: {len(log)}")
    print(f"  Bankroll final: {bankroll:.2f}")
    print(f"  ROI: {((bankroll/100.0)-1)*100:.2f}%")
    print("=" * 70)
    
    log_df = pd.DataFrame(log)
    out = REPORTS / "backtest_log.csv"
    log_df.to_csv(out, index=False)
    print(f"\nOK - Log guardado: {out}")

if __name__ == "__main__":
    main()

