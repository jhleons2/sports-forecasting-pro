import os, time, requests
from pathlib import Path
from typing import List, Dict, Any
import pandas as pd

BASE = "https://api.the-odds-api.com/v4"
API_KEY = os.getenv("THE_ODDS_API_KEY","")

def list_sports():
    r = requests.get(f"{BASE}/sports", params={"apiKey": API_KEY}, timeout=30)
    r.raise_for_status()
    return r.json()

def get_odds(sport_key: str, regions: str = "eu", markets: str = "h2h", bookmakers: str = "pinnacle,bet365") -> pd.DataFrame:
    """
    Current odds snapshot for upcoming events. Use for alerts and as a proxy if closing not available.
    """
    r = requests.get(f"{BASE}/sports/{sport_key}/odds", params={
        "apiKey": API_KEY, "regions": regions, "markets": markets, "bookmakers": bookmakers, "oddsFormat":"decimal"
    }, timeout=30)
    r.raise_for_status()
    data = r.json()
    rows = []
    for ev in data:
        commence = ev.get("commence_time")
        home = ev.get("home_team"); away = ev.get("away_team")
        idv = ev.get("id")
        for bk in ev.get("bookmakers", []):
            bkname = bk.get("title","")
            for mk in bk.get("markets", []):
                if mk.get("key") == "h2h":
                    ou = mk.get("outcomes", [])
                    # Normalize order: home, draw, away if present
                    price_map = {o.get("name",""): float(o.get("price")) for o in ou}
                    rows.append(dict(event_id=idv, commence_time=commence, bookmaker=bkname,
                                     home=home, away=away,
                                     H=price_map.get(home), D=price_map.get("Draw"), A=price_map.get(away)))
    return pd.DataFrame(rows)

def get_historical_snapshot(sport_key: str, date_from: str, date_to: str, regions: str = "eu", markets: str = "h2h", bookmakers: str = "pinnacle,bet365") -> pd.DataFrame:
    """
    Historical snapshots require a paid plan; this function assumes access is enabled on the account.
    """
    url = f"{BASE}/historical/sports/{sport_key}/odds"
    params = {"apiKey": API_KEY, "dateFormat":"iso", "regions": regions, "markets": markets, "bookmakers": bookmakers,
              "from": date_from, "to": date_to}
    r = requests.get(url, params=params, timeout=60)
    r.raise_for_status()
    data = r.json()
    # Flatten similar to get_odds
    rows = []
    for snap in data:
        ts = snap.get("timestamp")
        for ev in snap.get("data", []):
            idv = ev.get("id"); home = ev.get("home_team"); away = ev.get("away_team")
            for bk in ev.get("bookmakers", []):
                bkname = bk.get("title","")
                for mk in bk.get("markets", []):
                    if mk.get("key") == "h2h":
                        for o in mk.get("outcomes", []):
                            rows.append(dict(timestamp=ts, event_id=idv, commence_time=ev.get("commence_time"),
                                             bookmaker=bkname, home=home, away=away,
                                             outcome=o.get("name"), price=float(o.get("price"))))
    return pd.DataFrame(rows)
