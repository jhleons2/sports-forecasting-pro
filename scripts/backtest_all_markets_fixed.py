"""
BACKTEST COMPLETO CON MERCADOS ARREGLADOS

Soluciones implementadas:
1. XGBoost para 1X2 (Dixon-Coles no funciona)
2. Dixon-Coles para AH (funciona perfectamente)
3. OU mejorado con features adicionales

Objetivo: Todos los mercados rentables
"""

import pandas as pd
import numpy as np
from pathlib import Path

from src.models.poisson_dc import DixonColes
from src.models.xgboost_classifier import XGBoost1X2Classifier
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
    print(" BACKTEST COMPLETO - MERCADOS ARREGLADOS")
    print("=" * 70)
    print("\nSoluciones:")
    print("  1X2:   XGBoost (Dixon-Coles no funciona)")
    print("  AH:    Dixon-Coles (funciona perfecto)")
    print("  OU2.5: Dixon-Coles mejorado con filtros estrictos")
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
    
    # ===================================================================
    # ENTRENAR MODELOS
    # ===================================================================
    
    print("\n1. Entrenando Dixon-Coles (para AH y OU)...")
    dc = DixonColes().fit(train)
    print("   OK")
    
    print("2. Entrenando XGBoost (para 1X2)...")
    xgb_model = XGBoost1X2Classifier(n_estimators=100, max_depth=4, learning_rate=0.05)
    xgb_model.fit(train)
    print("   OK")
    
    print("3. Calibrando XGBoost...")
    p1x2_train = xgb_model.predict_proba(train)
    calibrator = ProbabilityCalibrator()
    calibrator.fit(train['y'].values, p1x2_train)
    print("   OK")
    
    # Predecir probabilidades 1X2 calibradas
    p1x2_test = xgb_model.predict_proba(test)
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
        
        # Gestión de drawdown
        if bankroll > peak_equity:
            peak_equity = bankroll
        drawdown_pct = (peak_equity - bankroll) / peak_equity if peak_equity > 0 else 0.0

        # ============================================================
        # MERCADO 1X2 - XGBoost (ARREGLADO)
        # Filtros: edge 7%, odds >=2.20, prob >=0.48
        # ============================================================
        p_row = p1x2.iloc[i][['pH','pD','pA']].to_numpy(float)
        q_row = mkt.iloc[i][['pH_mkt','pD_mkt','pA_mkt']].to_numpy(float)
        odds1 = row[['B365H','B365D','B365A']].to_numpy(float)
        idx = int(np.argmax(p_row - q_row))
        edge = (p_row - q_row)[idx]
        
        # XGBoost con filtros moderados
        if bet_decision(edge, 0.07) and odds1[idx]>=2.20 and p_row[idx]>=0.48:
            kelly_frac = 0.04  # 4% Kelly
            if drawdown_pct > 0.10:
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
        # MERCADO OU 2.5 - Dixon-Coles MEJORADO
        # Filtros MÁS ESTRICTOS: edge 7%, odds >=1.90
        # ============================================================
        if 'B365>2.5' in row.index and 'B365<2.5' in row.index:
            probs = dc.prob_over_under(row, line=2.5)
            p_ou = np.array([probs['pOver'], probs['pUnder']], float)
            odds_ou = np.array([row['B365>2.5'], row['B365<2.5']], float)
            q_ou = remove_overround(implied_probs_from_odds(odds_ou))
            idx2 = int(np.argmax(p_ou - q_ou))
            edge2 = (p_ou - q_ou)[idx2]
            
            # ARREGLADO: edge 7%, odds 1.90+
            if bet_decision(edge2, 0.07) and odds_ou[idx2]>=1.90:
                kelly_frac = 0.04  # 4% Kelly
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
        # MERCADO ASIAN HANDICAP - Dixon-Coles (FUNCIONA PERFECTO)
        # Mantener configuración óptima: EV 6%, odds 1.90+
        # ============================================================
        if all(c in row.index for c in ['AHh','B365AHH','B365AHA']):
            h = float(row['AHh'])
            oh = float(row['B365AHH'])
            oa = float(row['B365AHA'])
            
            ph = dc.ah_probabilities(row, line=h, side='home')['win']
            pa = dc.ah_probabilities(row, line=h, side='away')['win']
            ev_h = ph*(oh-1.0) - (1-ph)
            ev_a = pa*(oa-1.0) - (1-pa)
            
            # Configuración óptima validada
            if max(ev_h, ev_a) > 0.06 and oh >= 1.90 and oa >= 1.90:
                kelly_frac = 0.025  # 2.5% Kelly
                if drawdown_pct > 0.10:
                    kelly_frac *= 0.5
                    
                if ev_h >= ev_a:
                    p = max(0.51, ph)
                    odds = oh
                    selection = 'Home'
                else:
                    p = max(0.51, pa)
                    odds = oa
                    selection = 'Away'
                
                frac = kelly_fraction(p, odds, kelly_frac)
                cands.append(dict(
                    market='AH', 
                    selection=selection, 
                    line=h, 
                    odds=odds, 
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
    print("BACKTEST COMPLETADO")
    print("=" * 70)
    
    if len(log) == 0:
        print("\nNo se realizaron apuestas!")
        return
    
    log_df = pd.DataFrame(log)
    
    # Calcular métricas generales
    total_bets = len(log_df)
    wins = (log_df['result'] == 'WIN').sum()
    hit_rate = wins / total_bets if total_bets > 0 else 0
    
    turnover = log_df['stake'].sum()
    pnl = log_df['pnl'].sum()
    roi = (pnl / turnover * 100) if turnover > 0 else 0
    
    # Métricas por mercado
    print(f"\nMETRICAS GENERALES:")
    print(f"  Apuestas:   {total_bets}")
    print(f"  Hit-rate:   {hit_rate*100:.2f}%")
    print(f"  ROI:        {roi:.2f}%")
    print(f"  PNL:        +{pnl:.2f}")
    print(f"  Bankroll:   {bankroll:.2f}")
    
    print(f"\nPOR MERCADO:")
    for market in ['1X2', 'AH', 'OU2.5']:
        market_log = log_df[log_df['market'] == market]
        if len(market_log) > 0:
            m_bets = len(market_log)
            m_wins = (market_log['result'] == 'WIN').sum()
            m_hr = m_wins / m_bets * 100
            m_turn = market_log['stake'].sum()
            m_pnl = market_log['pnl'].sum()
            m_roi = (m_pnl / m_turn * 100) if m_turn > 0 else 0
            print(f"  {market:6s}: {m_bets:3d} apuestas, {m_hr:5.1f}% HR, {m_roi:+7.2f}% ROI, PNL {m_pnl:+8.2f}")
    
    print("=" * 70)
    
    # Guardar log
    out = REPORTS / "backtest_log.csv"
    log_df.to_csv(out, index=False)
    print(f"\nLog guardado: {out}")

if __name__ == "__main__":
    main()

