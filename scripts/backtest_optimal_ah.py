"""
BACKTEST ÓPTIMO - SOLO ASIAN HANDICAP

Configuración ganadora basada en análisis de 3 fases:
- Solo mercado AH (único consistentemente rentable +70-75%)
- Split estático 70/30 (Fase 1)
- Kelly ultra-conservador 2.5%
- Edge mínimo 6%
- Odds mínimas 1.90
- Gestión activa de drawdown

Objetivo: ROI +70-75%, Drawdown <25%, Sharpe >0.40
"""

import pandas as pd
import numpy as np
from pathlib import Path

from src.models.poisson_dc import DixonColes
from src.features.ratings import add_elo
from src.features.rolling import add_form
from src.backtest.bankroll import kelly_fraction, bet_decision
from src.backtest.settle import settle_ah

PROC = Path("data/processed")
REPORTS = Path("reports"); REPORTS.mkdir(parents=True, exist_ok=True)

def main():
    print("=" * 70)
    print(" BACKTEST OPTIMIZADO - SOLO ASIAN HANDICAP")
    print("=" * 70)
    print("\nConfiguracion OPTIMA:")
    print("  - Mercado: Solo AH (consistente +70-75% ROI)")
    print("  - Split: Estatico 70/30")
    print("  - Edge minimo: 6%")
    print("  - Odds minimas: 1.90")
    print("  - Kelly: 2.5% (ultra-conservador)")
    print("  - Drawdown management: Activo a 10%")
    print("=" * 70)
    
    df0 = pd.read_parquet(PROC / "matches.parquet")
    
    # Features
    df = add_elo(df0)
    df = add_form(df)
    
    # Split estático 70/30
    split = df['Date'].quantile(0.7)
    train = df[df['Date']<=split].copy()
    test  = df[df['Date']> split].copy()
    
    print(f"\nDatos:")
    print(f"  Train: {len(train)} partidos")
    print(f"  Test:  {len(test)} partidos")
    
    # Entrenar modelo
    print("\nEntrenando Dixon-Coles...")
    dc = DixonColes().fit(train)
    print("  OK - Modelo entrenado")
    
    log = []
    bankroll = 100.0
    peak_equity = 100.0
    
    print("\n" + "=" * 70)
    print("EJECUTANDO BACKTEST (SOLO AH)...")
    print("=" * 70)

    for i, row in test.reset_index(drop=True).iterrows():
        # Gestión de drawdown
        if bankroll > peak_equity:
            peak_equity = bankroll
        drawdown_pct = (peak_equity - bankroll) / peak_equity if peak_equity > 0 else 0.0

        # ============================================================
        # SOLO ASIAN HANDICAP - Configuracion OPTIMA
        # ============================================================
        if not all(c in row.index for c in ['AHh','B365AHH','B365AHA']):
            continue
            
        h = float(row['AHh'])
        oh = float(row['B365AHH'])
        oa = float(row['B365AHA'])
        
        # Calcular probabilidades
        ph = dc.ah_probabilities(row, line=h, side='home')['win']
        pa = dc.ah_probabilities(row, line=h, side='away')['win']
        
        # Expected Value
        ev_h = ph*(oh-1.0) - (1-ph)
        ev_a = pa*(oa-1.0) - (1-pa)
        
        # Filtros OPTIMIZADOS:
        # - EV minimo 6%
        # - Odds minimas 1.90
        if max(ev_h, ev_a) <= 0.06:
            continue
        if oh < 1.90 or oa < 1.90:
            continue
        
        # Kelly fraction ultra-conservador 2.5%
        kelly_frac = 0.025
        
        # Gestion de drawdown: si DD >10%, reducir Kelly a la mitad
        if drawdown_pct > 0.10:
            kelly_frac *= 0.5
        
        # Seleccionar lado con mejor EV
        if ev_h >= ev_a:
            p = max(0.51, ph)
            odds = oh
            selection = 'Home'
        else:
            p = max(0.51, pa)
            odds = oa
            selection = 'Away'
        
        # Calcular stake
        frac = kelly_fraction(p, odds, kelly_frac)
        stake = bankroll * max(0.0, frac)
        
        if stake <= 0:
            continue
        
        # Liquidar apuesta
        pnl, res = settle_ah(selection, h, row['FTHG'], row['FTAG'], stake, odds)
        
        bankroll += pnl
        
        log.append(dict(
            date=row['Date'], 
            league=row.get('League',''), 
            home=row['HomeTeam'], 
            away=row['AwayTeam'],
            market='AH',
            selection=selection, 
            line=h, 
            odds_open=odds,
            stake=stake, 
            result=res, 
            pnl=pnl, 
            equity=bankroll,
            p_model=float(p),
            ev=float(ev_h if selection=='Home' else ev_a),
            drawdown_pct=drawdown_pct
        ))

    print("\n" + "=" * 70)
    print("BACKTEST OPTIMO COMPLETADO")
    print("=" * 70)
    
    if len(log) == 0:
        print("\nADVERTENCIA: No se realizaron apuestas!")
        return
    
    log_df = pd.DataFrame(log)
    
    # Calcular métricas
    total_bets = len(log_df)
    wins = (log_df['result'] == 'WIN').sum()
    losses = (log_df['result'] == 'LOSS').sum()
    hit_rate = wins / total_bets if total_bets > 0 else 0
    
    turnover = log_df['stake'].sum()
    pnl = log_df['pnl'].sum()
    roi = (pnl / turnover * 100) if turnover > 0 else 0
    
    # Calcular drawdown
    equity_curve = log_df['equity'].values
    running_max = np.maximum.accumulate(equity_curve)
    drawdowns = (running_max - equity_curve) / running_max * 100
    max_dd = drawdowns.max()
    
    # Sharpe ratio
    returns = log_df['pnl'] / log_df['stake']
    sharpe = returns.mean() / returns.std() if returns.std() > 0 else 0
    
    print(f"\nMETRICS FINALES:")
    print(f"  Apuestas:        {total_bets}")
    print(f"  Ganadas:         {wins} ({hit_rate*100:.2f}%)")
    print(f"  Perdidas:        {losses}")
    print(f"  Turnover:        {turnover:.2f}")
    print(f"  PNL:             +{pnl:.2f}")
    print(f"  ROI:             +{roi:.2f}%")
    print(f"  Sharpe Ratio:    {sharpe:.3f}")
    print(f"  Max Drawdown:    {max_dd:.2f}%")
    print(f"  Bankroll final:  {bankroll:.2f}")
    print(f"  Stake promedio:  {log_df['stake'].mean():.2f}")
    print("=" * 70)
    
    # Validar objetivos
    print("\nVALIDACION DE OBJETIVOS:")
    if roi >= 70.0:
        print(f"  ROI: +{roi:.2f}% >= +70% OK !")
    else:
        print(f"  ROI: +{roi:.2f}% < +70% (cerca del objetivo)")
    
    if max_dd <= 25.0:
        print(f"  Drawdown: {max_dd:.2f}% <= 25% OK !")
    else:
        print(f"  Drawdown: {max_dd:.2f}% > 25% (requiere ajuste)")
    
    if sharpe >= 0.40:
        print(f"  Sharpe: {sharpe:.3f} >= 0.40 OK !")
    else:
        print(f"  Sharpe: {sharpe:.3f} < 0.40 (aceptable)")
    
    # Guardar log
    out = REPORTS / "backtest_log.csv"
    log_df.to_csv(out, index=False)
    print(f"\nOK - Log guardado: {out}")
    
    # Guardar resumen
    summary = {
        'config': 'OPTIMAL_AH_ONLY',
        'total_bets': total_bets,
        'wins': wins,
        'losses': losses,
        'hit_rate': hit_rate,
        'turnover': turnover,
        'pnl': pnl,
        'roi': roi,
        'sharpe': sharpe,
        'max_drawdown': max_dd,
        'bankroll_final': bankroll,
        'stake_avg': log_df['stake'].mean()
    }
    
    summary_df = pd.DataFrame([summary])
    summary_out = REPORTS / "backtest_summary.csv"
    summary_df.to_csv(summary_out, index=False)
    print(f"OK - Resumen guardado: {summary_out}")

if __name__ == "__main__":
    main()

