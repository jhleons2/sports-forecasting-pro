import argparse, json, re, time
from pathlib import Path
import requests
from tqdm import tqdm

LEAGUE_MAP = {
    "EPL": "EPL",
    "La_Liga": "La_Liga",
    "Bundesliga": "Bundesliga",
    "Serie_A": "Serie_A",
    "Ligue_1": "Ligue_1"
}

def fetch_league_matches(league_key: str, start_year: int):
    url = f"https://understat.com/league/{league_key}/{start_year}"
    html = requests.get(url, timeout=30, headers={"User-Agent":"Mozilla/5.0"}).text
    m = re.search(r"var\\s+matchesData\\s*=\\s*(\\[.*?\\]);", html, re.S)
    if not m:
        raise RuntimeError("No se encontró matchesData en Understat (estructura cambió?).")
    matches = json.loads(m.group(1))
    return matches

def fetch_match_xg(match_id: int):
    url = f"https://understat.com/match/{match_id}"
    html = requests.get(url, timeout=30, headers={"User-Agent":"Mozilla/5.0"}).text
    m_h = re.search(r"var\\s+shotsData\\s*=\\s*(\\{.*?\\});", html, re.S)
    if not m_h:
        raise RuntimeError("No se encontró shotsData en match page.")
    data = json.loads(m_h.group(1))
    def sum_xg(arr):
        return sum(float(s.get("xG", 0.0)) for s in arr)
    xg_home = sum_xg(data.get("h", []))
    xg_away = sum_xg(data.get("a", []))
    return xg_home, xg_away

def season_start_year_auto():
    import datetime
    today = datetime.datetime.utcnow()
    return today.year if today.month >= 7 else today.year - 1

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--leagues", nargs="+", required=True, help="EPL La_Liga Bundesliga Serie_A Ligue_1")
    ap.add_argument("--start_year", default="auto", help="Ej: 2024; 'auto' usa temporada actual")
    ap.add_argument("--out_dir", default="data/raw")
    args = ap.parse_args()

    out = Path(args.out_dir) / "understat"
    out.mkdir(parents=True, exist_ok=True)

    start_year = season_start_year_auto() if args.start_year == "auto" else int(args.start_year)

    for lg in args.leagues:
        key = LEAGUE_MAP.get(lg, lg)
        print(f"Descargando Understat: {key} {start_year}")
        matches = fetch_league_matches(key, start_year)
        rows = []
        for m in tqdm(matches, desc=f"{key} {start_year}"):
            mid = int(m["id"])
            try:
                xg_h, xg_a = fetch_match_xg(mid)
                rows.append(dict(id=mid, league=key, start_year=start_year,
                                 date=m.get("datetime"), home=m.get("h",{{}}).get("title"),
                                 away=m.get("a",{{}}).get("title"), xG_home=xg_h, xG_away=xg_a))
                time.sleep(0.4)
            except Exception as e:
                rows.append(dict(id=mid, league=key, start_year=start_year,
                                 date=m.get("datetime"), home=m.get("h",{{}}).get("title"),
                                 away=m.get("a",{{}}).get("title"), xG_home=None, xG_away=None, error=str(e)))
        import pandas as pd
        df = pd.DataFrame(rows)
        fp = out / f"{key}_{start_year}_xg.csv"
        df.to_csv(fp, index=False)
        print("Guardado:", fp)

if __name__ == "__main__":
    main()
