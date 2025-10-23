import numpy as np
import pandas as pd

def implied_probs_from_odds(odds):
    odds = np.asarray(odds, dtype=float)
    return 1.0 / odds

def remove_overround(implied_probs):
    s = implied_probs.sum()
    return implied_probs / s if s>0 else implied_probs

def market_probs_1x2(row, cols=('B365H','B365D','B365A')) -> np.ndarray:
    odds = row.loc[list(cols)].to_numpy(dtype=float)
    ip = implied_probs_from_odds(odds)
    return remove_overround(ip)

def closing_odds_1x2(row):
    # Prefer Pinnacle closing (PSCH/PSCD/PSCA), luego Bet365 closing (B365CH/B365CD/B365CA), luego promedio (AvgCH/D/A)
    for pref in ('PSC','B365C','AvgC','PS'):
        cols = [f'{pref}H', f'{pref}D', f'{pref}A']
        if all(c in row.index for c in cols):
            return row[cols].to_numpy(dtype=float)
    return np.array([np.nan, np.nan, np.nan])
