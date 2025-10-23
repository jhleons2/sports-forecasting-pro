import pandas as pd
import yaml
from pathlib import Path
from src.utils.names import normalize_name

RAW = Path("data/raw")
PROC = Path("data/processed")
CFG  = Path("config")

def load_football_data():
    files = sorted(RAW.glob("*.csv"))
    if not files:
        raise SystemExit("No hay CSVs de Football-Data (ejecuta football_data_multi).")
    dfs = []
    for fp in files:
        df = pd.read_csv(fp)
        needed = ['Date','HomeTeam','AwayTeam','FTHG','FTAG','B365H','B365D','B365A']
        miss = [c for c in needed if c not in df.columns]
        if miss:
            print("Omitiendo por columnas faltantes:", fp.name, miss)
            continue
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce', dayfirst=True)
        def lab(r):
            if r['FTHG'] > r['FTAG']: return 0
            if r['FTHG'] == r['FTAG']: return 1
            return 2
        df['y'] = df.apply(lab, axis=1)
        df['League'] = fp.stem.split('_')[0]
        dfs.append(df)
    if not dfs:
        raise SystemExit("No se pudieron leer CSVs con columnas mínimas.")
    out = pd.concat(dfs, ignore_index=True).sort_values('Date')
    return out

def load_understat_xg():
    udir = RAW / "understat"
    files = sorted(udir.glob("*_xg.csv"))
    if not files:
        print("No hay archivos Understat (xG). Continuando sin xG.")
        return None
    udfs = [pd.read_csv(fp, parse_dates=['date']) for fp in files]
    u = pd.concat(udfs, ignore_index=True)
    for col in ['home','away']:
        u[col+'_norm'] = u[col].astype(str).map(normalize_name)
    u = u.rename(columns={'date':'Date'})
    return u

def merge_xg(fd: pd.DataFrame, uxg: pd.DataFrame):
    if uxg is None:
        fd['xG_home'] = pd.NA
        fd['xG_away'] = pd.NA
        return fd
    map_fp = CFG / "team_mapping.yaml"
    mapping = {}
    if map_fp.exists():
        mapping = yaml.safe_load(map_fp.read_text()) or {}
    def map_name(s):
        s_norm = normalize_name(str(s))
        for k,v in mapping.items():
            if normalize_name(k)==s_norm:
                return normalize_name(v)
        return s_norm
    fd = fd.copy()
    fd['Home_norm'] = fd['HomeTeam'].map(map_name)
    fd['Away_norm'] = fd['AwayTeam'].map(map_name)
    uxg2 = uxg.copy()
    uxg2['Date_d-1'] = uxg2['Date'] - pd.Timedelta(days=1)
    uxg2['Date_d+1'] = uxg2['Date'] + pd.Timedelta(days=1)
    m = fd.merge(uxg2, left_on=['Date','Home_norm','Away_norm'], right_on=['Date','home_norm','away_norm'], how='left')
    m2 = fd.merge(uxg2, left_on=['Date','Home_norm','Away_norm'], right_on=['Date_d-1','home_norm','away_norm'], how='left', suffixes=('','_m2'))
    m3 = fd.merge(uxg2, left_on=['Date','Home_norm','Away_norm'], right_on=['Date_d+1','home_norm','away_norm'], how='left', suffixes=('','_m3'))
    base = fd.copy()
    base['xG_home'] = pd.NA; base['xG_away'] = pd.NA
    key = ['Date','Home_norm','Away_norm']
    m.set_index(key, inplace=True, drop=False)
    m2.set_index(key, inplace=True, drop=False)
    m3.set_index(key, inplace=True, drop=False)
    for idx in base.index:
        k = tuple(base.loc[idx, key])
        for col_out in ['xG_home','xG_away']:
            val = pd.NA
            for dfc in (m, m2, m3):
                if k in dfc.index:
                    vv = dfc.loc[k, col_out]
                    if hasattr(vv, 'iloc'):
                        vv = vv.iloc[0]
                    if pd.notna(vv):
                        val = vv; break
            base.at[idx, col_out] = val
    return base

def main():
    PROC.mkdir(parents=True, exist_ok=True)
    fd = load_football_data()
    uxg = load_understat_xg()
    df = merge_xg(fd, uxg)
    df.to_parquet(PROC / "matches.parquet", index=False)
    print("Dataset listo:", PROC / "matches.parquet")

if __name__ == "__main__":
    main()
