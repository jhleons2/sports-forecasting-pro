import numpy as np
import pandas as pd

def clv_from_open_close(open_odds: pd.Series, close_odds: pd.Series, selection_idx: int) -> float:
    """
    CLV = (close_implied / open_implied) - 1   on the selected outcome
    Equivalent to (open_price / close_price) - 1 in decimal odds when comparing prices on same outcome.
    Positive CLV means you beat the closing line (got a better price).
    """
    def implied(o): return 1.0 / np.clip(o.astype(float), 1e-9, None)
    if selection_idx is None or selection_idx<0: return np.nan
    if open_odds.isna().any() or close_odds.isna().any(): return np.nan
    io = implied(open_odds); ic = implied(close_odds)
    try:
        return float(ic.iloc[selection_idx] / io.iloc[selection_idx] - 1.0)
    except Exception:
        return np.nan

def choose_close_row(row):
    """
    Return closing odds vector if present in Football-Data columns (PSC*, B365C*, AvgC*).
    Preference: Pinnacle closing (PSC*), then Bet365 closing (B365C*), then average (AvgC*), else NaN.
    """
    prefs = ('PSC','B365C','AvgC','PS')
    for pref in prefs:
        cols = [f"{pref}H", f"{pref}D", f"{pref}A"]
        if all(c in row.index for c in cols) and row[cols].notna().all():
            return row[cols].astype(float).values
    return np.array([np.nan, np.nan, np.nan], dtype=float)
