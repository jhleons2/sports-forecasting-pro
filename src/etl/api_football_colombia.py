import os, time, requests, math
from pathlib import Path
from typing import Dict, Any, List
import pandas as pd

API_HOST = os.getenv("API_FOOTBALL_HOST", "api-football-v1.p.rapidapi.com")
API_KEY  = os.getenv("API_FOOTBALL_KEY", "")
BASE_URL = f"https://{API_HOST}/v3"

def _req(path: str, params: Dict[str, Any]) -> Dict[str, Any]:
    headers = {
        "x-rapidapi-key": API_KEY,
        "x-rapidapi-host": API_HOST
    }
    r = requests.get(BASE_URL + path, headers=headers, params=params, timeout=30)
    r.raise_for_status()
    return r.json()

def find_colombia_primera_a_league_id() -> int:
    # Robust search via /leagues endpoint
    data = _req("/leagues", {"country":"Colombia"})
    leagues = data.get("response", [])
    cand = []
    for L in leagues:
        lg = L.get("league", {})
        name = (lg.get("name") or "").lower()
        if "primera a" in name or "categoria primera a" in name:
            cand.append(lg.get("id"))
    if not cand:
        raise SystemExit("No se encontró la liga 'Primera A' para Colombia via /leagues. Verifica tu plan o tráfico.")
    # devuelve el primero (IDs son estables por API-FOOTBALL)
    return int(cand[0])

def fixtures_last_seasons(league_id: int, seasons: List[int]) -> pd.DataFrame:
    rows = []
    for season in seasons:
        data = _req("/fixtures", {"league": league_id, "season": season})
        for item in data.get("response", []):
            fx = item.get("fixture", {}); tm = item.get("teams", {}); go = item.get("goals", {})
            rows.append(dict(
                Date=fx.get("date"),
                HomeTeam=tm.get("home",{}).get("name"),
                AwayTeam=tm.get("away",{}).get("name"),
                FTHG=go.get("home"),
                FTAG=go.get("away"),
                League="CO1",
                Season=season,
                fixture_id=item.get("fixture",{}).get("id")
            ))
        time.sleep(0.2)
    df = pd.DataFrame(rows)
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce", utc=True).dt.tz_convert("America/Bogota").dt.tz_localize(None)
    return df

def odds_for_fixture_ids(fixture_ids: List[int], bookmaker="Bet365") -> pd.DataFrame:
    # Pull odds per fixture, pick Bet365 when available
    rows = []
    for fid in fixture_ids:
        data = _req("/odds", {"fixture": fid, "bookmaker": bookmaker})
        resp = data.get("response", [])
        if not resp: 
            continue
        # Normalize: we need 1X2, Over/Under 2.5, AH line odds
        markets = resp[0].get("bookmakers", [])
        for bk in markets:
            if bookmaker.lower() not in (bk.get("name","").lower()):
                continue
            for mkt in bk.get("bets", []):
                name = (mkt.get("name") or "").lower()
                # 1X2
                if "match winner" in name or "1x2" in name:
                    v = {o["value"]: o["odd"] for o in mkt.get("values", [])}
                    rows.append(dict(fixture_id=fid, B365H=float(v.get("Home", "nan")), B365D=float(v.get("Draw","nan")), B365A=float(v.get("Away","nan"))))
                # OU 2.5
                if "over/under" in name:
                    for v in mkt.get("values", []):
                        if v.get("value") in ("Over 2.5","Under 2.5"):
                            key = "B365>2.5" if "Over" in v["value"] else "B365<2.5"
                            rows.append(dict(fixture_id=fid, **{key: float(v.get("odd","nan"))}))
                # Asian Handicap main line (use 0.0 or listed AHh)
                if "asian handicap" in name:
                    # pick the closest to 0.0 line
                    best = None; best_abs = 1e9
                    for v in mkt.get("values", []):
                        try:
                            ln = float(v.get("handicap"))
                        except Exception:
                            continue
                        if abs(ln) < best_abs:
                            best_abs = abs(ln); best = v
                    if best:
                        # odds presented often as "Home" and "Away" at the handicap
                        try:
                            ln = float(best.get("handicap"))
                            oh = float(best.get("odd"))  # this may not be structured; fallback below
                        except Exception:
                            ln = 0.0; oh = float("nan")
                    # Fallback: build from full list if possible
                    # (APIs vary; keeping minimal workable scaffold)
    # Merge rows by fixture_id (wide)
    if not rows:
        return pd.DataFrame(columns=["fixture_id","B365H","B365D","B365A","B365>2.5","B365<2.5","AHh","B365AHH","B365AHA"])
    df = pd.DataFrame(rows).groupby("fixture_id").agg("first").reset_index()
    # Prepare AH columns if present (left as NaN by default since many feeds structure differently)
    for c in ["B365>2.5","B365<2.5","AHh","B365AHH","B365AHA"]:
        if c not in df.columns: df[c] = float("nan")
    return df

def seasons_last_two():
    import datetime
    today = datetime.datetime.utcnow()
    # for Colombia split season, we'll just use calendar year
    y = today.year
    return [y-1, y]

def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="Colombia")
    ap.add_argument("--out_dir", default="data/raw/api_football")
    args = ap.parse_args()
    out = Path(args.out_dir); out.mkdir(parents=True, exist_ok=True)

    lg_id = find_colombia_primera_a_league_id()
    seasons = seasons_last_two()
    fixtures = fixtures_last_seasons(lg_id, seasons)
    odds = odds_for_fixture_ids(fixtures["fixture_id"].dropna().astype(int).tolist(), bookmaker="Bet365")

    df = fixtures.merge(odds, on="fixture_id", how="left")
    fp = out / "colombia_primera_a_fixtures_odds.csv"
    df.to_csv(fp, index=False)
    print("Guardado:", fp)

if __name__ == "__main__":
    main()
