from pathlib import Path
import pandas as pd

RAW_API = Path("data/raw/api_football")
PROC    = Path("data/processed")

def main():
    fp = RAW_API / "colombia_primera_a_fixtures_odds.csv"
    if not fp.exists():
        raise SystemExit("No existe data/raw/api_football/colombia_primera_a_fixtures_odds.csv. Corre: python -m src.etl.api_football_colombia")
    df = pd.read_csv(fp, parse_dates=["Date"])
    # Map minimal columns expected downstream
    needed = ["Date","HomeTeam","AwayTeam","FTHG","FTAG","B365H","B365D","B365A","B365>2.5","B365<2.5","AHh","B365AHH","B365AHA","League"]
    for c in needed:
        if c not in df.columns:
            df[c] = pd.NA
    # Label y
    def lab(r):
        if r["FTHG"] > r["FTAG"]: return 0
        if r["FTHG"] == r["FTAG"]: return 1
        return 2
    df["y"] = df.apply(lab, axis=1)
    PROC.mkdir(parents=True, exist_ok=True)
    df.to_parquet(PROC / "matches.parquet", index=False)
    print("Dataset listo con Colombia Primera A:", PROC / "matches.parquet")

if __name__ == "__main__":
    main()
