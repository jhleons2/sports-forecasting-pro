import os, time
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import requests

from src.features.ratings import add_elo
from src.models.poisson_dc import DixonColes
from src.utils.odds import remove_overround, implied_probs_from_odds

API_HOST = os.getenv("API_FOOTBALL_HOST", "api-football-v1.p.rapidapi.com")
API_KEY  = os.getenv("API_FOOTBALL_KEY", "")
BASE_URL = f"https://{API_HOST}/v3"

TELEGRAM_BOT = os.getenv("TELEGRAM_BOT_TOKEN","")
TELEGRAM_CHAT= os.getenv("TELEGRAM_CHAT_ID","")

def req(path, params):
    headers = {"x-rapidapi-key": API_KEY, "x-rapidapi-host": API_HOST}
    r = requests.get(BASE_URL + path, headers=headers, params=params, timeout=30)
    r.raise_for_status()
    return r.json()

def colombia_league_id():
    data = req("/leagues", {"country":"Colombia"})
    for L in data.get("response", []):
        lg = L.get("league",{})
        name = (lg.get("name") or "").lower()
        if "primera a" in name or "categoria primera a" in name:
            return int(lg.get("id"))
    raise SystemExit("No encuentro liga Colombia Primera A — verifica cobertura/plan en API-FOOTBALL.")

def upcoming_fixtures(league_id: int, days_ahead: int = 7) -> pd.DataFrame:
    today = datetime.utcnow().date()
    to = (today + timedelta(days=days_ahead)).isoformat()
    frm = today.isoformat()
    data = req("/fixtures", {"league": league_id, "from": frm, "to": to})
    rows = []
    for item in data.get("response", []):
        fx = item.get("fixture", {}); tm = item.get("teams", {})
        rows.append(dict(
            Date=pd.to_datetime(fx.get("date"), utc=True).tz_convert("America/Bogota").tz_localize(None),
            HomeTeam=tm.get("home",{}).get("name"),
            AwayTeam=tm.get("away",{}).get("name"),
            fixture_id=item.get("fixture",{}).get("id")
        ))
    return pd.DataFrame(rows)

def odds_1x2_for_fixtures(fixture_ids):
    rows = []
    for fid in fixture_ids:
        data = req("/odds", {"fixture": fid, "bookmaker": "Bet365"})
        resp = data.get("response", [])
        if not resp: 
            continue
        mkts = resp[0].get("bookmakers", [])
        for bk in mkts:
            if "bet365" not in (bk.get("name","").lower()):
                continue
            for mkt in bk.get("bets", []):
                name = (mkt.get("name") or "").lower()
                if "match winner" in name or "1x2" in name:
                    v = {o["value"]: o["odd"] for o in mkt.get("values", [])}
                    rows.append(dict(fixture_id=fid, B365H=float(v.get("Home","nan")), B365D=float(v.get("Draw","nan")), B365A=float(v.get("Away","nan"))))
    return pd.DataFrame(rows)

def telegram_send(msg: str):
    if not TELEGRAM_BOT or not TELEGRAM_CHAT:
        return
    requests.get(f"https://api.telegram.org/bot{TELEGRAM_BOT}/sendMessage", params={
        "chat_id": TELEGRAM_CHAT, "text": msg
    }, timeout=15)

def main():
    PROC = Path("data/processed"); REPORTS = Path("reports"); REPORTS.mkdir(parents=True, exist_ok=True)
    hist = pd.read_parquet(PROC / "matches.parquet")
    hist = add_elo(hist)

    # Train on all historical for Elo params in DC
    dc = DixonColes().fit(hist.sort_values("Date"))

    lg_id = colombia_league_id()
    up = upcoming_fixtures(lg_id, days_ahead=7)
    if up.empty:
        print("No hay próximos partidos en ventana seleccionada."); return
    odds = odds_1x2_for_fixtures(up['fixture_id'].tolist())
    df = up.merge(odds, on="fixture_id", how="left")

    picks = []
    for _, r in df.iterrows():
        # Build a feature row using latest Elo
        row = dict(EloHome=1500.0, EloAway=1500.0, FTHG=0, FTAG=0)
        # Approx Elo from last known table (hist last ratings)
        # We reuse the last Elo numbers from hist (already computed per match). Take last known ratings per team.
        # For a quick approach, we compute team average Elo from tail.
        eH = hist[hist['HomeTeam']==r['HomeTeam']]['EloHome'].tail(1)
        eA = hist[hist['AwayTeam']==r['AwayTeam']]['EloAway'].tail(1)
        row['EloHome'] = float(eH.values[0]) if len(eH)>0 else 1500.0
        row['EloAway'] = float(eA.values[0]) if len(eA)>0 else 1500.0
        pr = dc.predict_1x2(pd.DataFrame([row]))
        p = pr.loc[0, ['pH','pD','pA']].to_numpy(float)
        # market
        if not np.isfinite([r.get('B365H'), r.get('B365D'), r.get('B365A')]).all():
            continue
        q = remove_overround(implied_probs_from_odds([r['B365H'], r['B365D'], r['B365A']]))
        idx = int(np.argmax(p - q))
        sel = ['H','D','A'][idx]; edge = (p - q)[idx]
        if edge >= 0.03:
            picks.append(dict(date=r['Date'], home=r['HomeTeam'], away=r['AwayTeam'], selection=sel,
                              p_model=p[idx], p_mkt=q[idx], odds= [r['B365H'], r['B365D'], r['B365A']][idx], edge=edge))

    out = pd.DataFrame(picks).sort_values("date")
    fp = REPORTS / "alerts_picks.csv"; out.to_csv(fp, index=False)
    print("Picks guardados en:", fp, "(", len(out), "picks )")

    if len(out)>0:
        for _, r in out.iterrows():
            msg = f"VALUE PICK {r['date']:%Y-%m-%d %H:%M} {r['home']} vs {r['away']} — {r['selection']}  edge={r['edge']:.2%}  odds={r['odds']}"
            telegram_send(msg)

if __name__ == "__main__":
    main()
