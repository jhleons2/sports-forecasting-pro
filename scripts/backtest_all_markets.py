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
    df0 = pd.read_parquet(PROC / "matches.parquet")
    # features antes de split
    df = add_elo(df0); df = add_form(df)
    
    # FASE 2: Walk-Forward Validation
    # En lugar de split estático 70/30, usamos rolling window
    print("=" * 60)
    print("BACKTEST CON WALK-FORWARD VALIDATION + CALIBRACIÓN")
    print("=" * 60)
    
    WINDOW_SIZE = 400  # Partidos para entrenar
    MIN_TRAIN = 300     # Mínimo de datos históricos
    
    log = []
    bankroll = 100.0
    peak_equity = 100.0
    
    # Ordenar por fecha
    df = df.sort_values('Date').reset_index(drop=True)
    
    # Walk-forward: entrenar con ventana móvil
    for test_idx in range(MIN_TRAIN, len(df)):
        # Definir ventana de entrenamiento
        train_start = max(0, test_idx - WINDOW_SIZE)
        train = df.iloc[train_start:test_idx].copy()
        row = df.iloc[test_idx]
        
        # Re-entrenar modelo cada 50 partidos (o al inicio)
        if test_idx == MIN_TRAIN or (test_idx - MIN_TRAIN) % 50 == 0:
            dc = DixonColes().fit(train)
            
            # Calibrar probabilidades 1X2
            p1x2_train = dc.predict_1x2(train)
            calibrator = ProbabilityCalibrator()
            calibrator.fit(train['y'].values, p1x2_train)
            print(f"  Re-entrenado en partido {test_idx}/{len(df)} (train: {len(train)} partidos)")
        
        # Predecir para este partido
        row_df = pd.DataFrame([row])
        p1x2 = calibrator.transform(dc.predict_1x2(row_df))
        mkt = pd.DataFrame([market_probs_1x2(row)], columns=['pH_mkt','pD_mkt','pA_mkt'])
        cands = []
        
        # Actualizar peak equity para gestión de drawdown
        if bankroll > peak_equity:
            peak_equity = bankroll
        
        # Calcular drawdown actual
        drawdown_pct = (peak_equity - bankroll) / peak_equity if peak_equity > 0 else 0.0

        # 1X2 - REACTIVADO CON CALIBRACIÓN FASE 2
        # Filtros MUY estrictos: edge 8%, odds >=2.20, prob >=0.50
        p_row = p1x2.iloc[0][['pH','pD','pA']].to_numpy(float)
        q_row = mkt.iloc[0][['pH_mkt','pD_mkt','pA_mkt']].to_numpy(float)
        odds1 = row[['B365H','B365D','B365A']].to_numpy(float)
        idx = int(np.argmax(p_row - q_row))
        edge = (p_row - q_row)[idx]
        # FASE 2: edge 8%, odds >=2.20, prob >=0.50, Kelly 4%
        if bet_decision(edge, 0.08) and odds1[idx]>=2.20 and p_row[idx]>=0.50:
            # Ajustar Kelly por drawdown
            kelly_frac = 0.04
            if drawdown_pct > 0.15:  # Si drawdown >15%, reducir Kelly a la mitad
                kelly_frac *= 0.5
            frac = kelly_fraction(p_row[idx], odds1[idx], kelly_frac)
            cands.append(dict(market='1X2', selection=['H','D','A'][idx], line=None, odds=float(odds1[idx]), frac=float(frac),
                              p_model=float(p_row[idx]), p_mkt=float(q_row[idx])))

        # OU 2.5 - FASE 2: edge 6%, odds >=1.85, Kelly 5% (más conservador)
        if 'B365>2.5' in row.index and 'B365<2.5' in row.index:
            probs = dc.prob_over_under(row, line=2.5)
            p_ou = np.array([probs['pOver'], probs['pUnder']], float)
            odds_ou = np.array([row['B365>2.5'], row['B365<2.5']], float)
            q_ou = remove_overround(implied_probs_from_odds(odds_ou))
            idx2 = int(np.argmax(p_ou - q_ou))
            edge2 = (p_ou - q_ou)[idx2]
            # FASE 2: edge 6%, odds >=1.85, Kelly 5%
            if bet_decision(edge2, 0.06) and odds_ou[idx2]>=1.85:
                kelly_frac = 0.05
                if drawdown_pct > 0.15:
                    kelly_frac *= 0.5
                frac = kelly_fraction(p_ou[idx2], odds_ou[idx2], kelly_frac)
                cands.append(dict(market='OU2.5', selection=['Over','Under'][idx2], line=2.5, odds=float(odds_ou[idx2]), frac=float(frac),
                                  p_model=float(p_ou[idx2]), p_mkt=float(q_ou[idx2])))

        # AH - FASE 2: EV >7%, odds >=1.90, Kelly 2.5% (ultra-conservador)
        if all(c in row.index for c in ['AHh','B365AHH','B365AHA']):
            h = float(row['AHh']); oh=float(row['B365AHH']); oa=float(row['B365AHA'])
            # proxy EV simple con prob win del lado correspondiente
            ph = dc.ah_probabilities(row, line=h, side='home')['win']
            pa = dc.ah_probabilities(row, line=h, side='away')['win']
            ev_h = ph*(oh-1.0) - (1-ph)
            ev_a = pa*(oa-1.0) - (1-pa)
            # FASE 2: EV mínimo 7%, odds mínimas 1.90, Kelly 2.5%
            if max(ev_h, ev_a) > 0.07 and oh >= 1.90 and oa >= 1.90:
                kelly_frac = 0.025
                if drawdown_pct > 0.15:
                    kelly_frac *= 0.5
                if ev_h>=ev_a:
                    p = max(0.51, ph); frac = kelly_fraction(p, oh, kelly_frac)
                    cands.append(dict(market='AH', selection='Home', line=h, odds=oh, frac=float(frac), p_model=float(p), p_mkt=float('nan')))
                else:
                    p = max(0.51, pa); frac = kelly_fraction(p, oa, kelly_frac)
                    cands.append(dict(market='AH', selection='Away', line=h, odds=oa, frac=float(frac), p_model=float(p), p_mkt=float('nan')))

        if not cands:
            continue

        def key(x):
            return x['p_model'] - (x['p_mkt'] if isinstance(x['p_mkt'], float) and x['p_mkt']==x['p_mkt'] else 0.5)
        best = max(cands, key=key)

        stake = bankroll * max(0.0, best['frac'])
        if stake <= 0: 
            continue

        if best['market']=='1X2':
            pnl, res = settle_1x2({'H':0,'D':1,'A':2}[best['selection']], int(row['y']), stake, best['odds'])
        elif best['market']=='OU2.5':
            pnl, res = settle_ou(best['selection'], row['FTHG'], row['FTAG'], stake, best['odds'], 2.5)
        else:
            pnl, res = settle_ah(best['selection'], best['line'], row['FTHG'], row['FTAG'], stake, best['odds'])

        bankroll += pnl
        log.append(dict(date=row['Date'], league=row.get('League',''), home=row['HomeTeam'], away=row['AwayTeam'],
                        market=best['market'], selection=best['selection'], line=best['line'], odds_open=best['odds'],
                        stake=stake, result=res, pnl=pnl, equity=bankroll, p_model=best['p_model'], p_mkt=best['p_mkt']))

    print("=" * 60)
    print(f"WALK-FORWARD COMPLETADO")
    print(f"Total partidos evaluados: {len(df) - MIN_TRAIN}")
    print(f"Apuestas realizadas: {len(log)}")
    print("=" * 60)
    
    log_df = pd.DataFrame(log)
    out = REPORTS / "backtest_log.csv"
    log_df.to_csv(out, index=False)
    print("Log guardado:", out)

if __name__ == "__main__":
    main()
