from pathlib import Path
import pandas as pd
from src.reporting.clv import clv_from_open_close, choose_close_row

REPORTS = Path("reports")
PROC    = Path("data/processed")

def main():
    log_fp = REPORTS / "backtest_log.csv"
    ds_fp  = PROC / "matches.parquet"
    if not log_fp.exists() or not ds_fp.exists():
        raise SystemExit("Faltan archivos: reports/backtest_log.csv o data/processed/matches.parquet")
    log = pd.read_csv(log_fp, parse_dates=['date'])
    ds  = pd.read_parquet(ds_fp)

    # Join back test rows to dataset to fetch closing odds columns (PSC*, B365C*, AvgC*)
    key_cols = ['Date','HomeTeam','AwayTeam']
    merged = log.merge(ds, left_on=['date','home','away'], right_on=key_cols, how='left', suffixes=('','_ds'))

    clv_vals = []
    for _, r in merged.iterrows():
        if r['market'] != '1X2':
            clv_vals.append(pd.NA); continue
        open_odds = pd.Series([r.get('odds_open'), None, None], index=['H','D','A'])  # we only know placed selection price
        # get full opening odds from dataset if present; else leave others NaN
        try:
            open_series = pd.Series([r.get('B365H'), r.get('B365D'), r.get('B365A')], index=['H','D','A'])
            if open_series.notna().all():
                open_odds = open_series
        except Exception:
            pass
        close_vec = choose_close_row(r)
        close_series = pd.Series(close_vec, index=['H','D','A'])
        idx_pick = {'H':0,'D':1,'A':2}.get(r['selection'], None)
        clv = clv_from_open_close(open_series, close_series, idx_pick) if idx_pick is not None else pd.NA
        clv_vals.append(clv)

    merged['clv'] = clv_vals
    out = REPORTS / "backtest_log_with_clv.csv"
    merged.to_csv(out, index=False)
    print("CLV añadido en:", out)

if __name__ == "__main__":
    main()
