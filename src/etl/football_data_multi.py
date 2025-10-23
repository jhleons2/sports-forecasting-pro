import argparse
from pathlib import Path
import requests
from datetime import datetime
from tqdm import tqdm

BASE_URL = "https://www.football-data.co.uk/mmz4281/{season}/{league}.csv"

def season_codes_last_years(n_seasons=2):
    today = datetime.utcnow()
    year = today.year % 100
    start_year = year - 1 if today.month < 7 else year
    codes = []
    for i in range(n_seasons):
        y1 = start_year - i
        y2 = (start_year - i + 1) % 100
        codes.append(f"{y1:02d}{y2:02d}")
    return list(reversed(codes))

def download_league(league: str, season: str, out_dir: Path):
    url = BASE_URL.format(season=season, league=league)
    out_dir.mkdir(parents=True, exist_ok=True)
    fp = out_dir / f"{league}_{season}.csv"
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    fp.write_bytes(r.content)
    return fp

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--leagues", nargs="+", required=True, help="Ej: E0 SP1 D1 I1 F1")
    ap.add_argument("--n_seasons", type=int, default=2, help="Últimas N temporadas (default: 2)")
    ap.add_argument("--out_dir", default="data/raw")
    args = ap.parse_args()

    out = Path(args.out_dir)
    seasons = season_codes_last_years(args.n_seasons)
    print("Temporadas:", seasons)

    for lg in args.leagues:
        for ss in tqdm(seasons, desc=f"Liga {lg}"):
            try:
                fp = download_league(lg, ss, out)
                print("OK:", fp.name)
            except Exception as e:
                print("ERROR:", lg, ss, e)

if __name__ == "__main__":
    main()
