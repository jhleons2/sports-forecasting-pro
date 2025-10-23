"""
football-data.org API Integration
API RESTful para datos de fútbol en tiempo real

Documentación: https://www.football-data.org/documentation/quickstart
Plan gratuito: Top competiciones, 10 requests/minuto

Uso:
    python -m src.etl.football_data_org --competitions PL PD BL1 SA FL1
"""

import os
import time
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import pandas as pd
import requests
from tqdm import tqdm

# Configuración
API_KEY = os.getenv("FOOTBALL_DATA_ORG_KEY", "")
BASE_URL = "https://api.football-data.org/v4"

# Rate limiting: 10 requests/minuto en plan gratuito
REQUEST_DELAY = 6.5  # 6.5 segundos = ~9 requests/minuto (seguro)

# Mapeo de códigos de competición
# Documentación: https://www.football-data.org/documentation/api
COMPETITIONS = {
    # Top-5 Ligas Europeas (GRATIS)
    "PL": {"id": 2021, "name": "Premier League", "country": "England"},
    "ELC": {"id": 2016, "name": "Championship", "country": "England"},
    "PD": {"id": 2014, "name": "La Liga", "country": "Spain"},
    "BL1": {"id": 2002, "name": "Bundesliga", "country": "Germany"},
    "SA": {"id": 2019, "name": "Serie A", "country": "Italy"},
    "FL1": {"id": 2015, "name": "Ligue 1", "country": "France"},
    
    # Otras Europeas (GRATIS)
    "DED": {"id": 2003, "name": "Eredivisie", "country": "Netherlands"},
    "PPL": {"id": 2017, "name": "Primeira Liga", "country": "Portugal"},
    
    # Internacionales (GRATIS)
    "CL": {"id": 2001, "name": "Champions League", "country": "Europe"},
    "EL": {"id": 2146, "name": "Europa League", "country": "Europe"},
    "WC": {"id": 2000, "name": "FIFA World Cup", "country": "World"},
    "EC": {"id": 2018, "name": "European Championship", "country": "Europe"},
    "CLI": {"id": 2152, "name": "Copa Libertadores", "country": "South America"},
}


def get_headers() -> Dict[str, str]:
    """Headers para autenticación"""
    if not API_KEY:
        raise ValueError(
            "FOOTBALL_DATA_ORG_KEY no configurado en .env\n"
            "Obtén tu clave gratis en: https://www.football-data.org/client/register"
        )
    
    return {
        "X-Auth-Token": API_KEY,
        "User-Agent": "SportsForecasting/1.0 (Educational)"
    }


def api_request(endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Request genérico a la API con rate limiting
    
    Args:
        endpoint: Path del endpoint (ej: "/competitions/PL/matches")
        params: Query parameters opcionales
    
    Returns:
        JSON response
    """
    time.sleep(REQUEST_DELAY)  # Rate limiting
    
    url = f"{BASE_URL}{endpoint}"
    
    try:
        response = requests.get(url, headers=get_headers(), params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429:
            print("[!] Rate limit excedido. Esperando 60s...")
            time.sleep(60)
            return api_request(endpoint, params)  # Retry
        elif e.response.status_code == 403:
            print("[X] Token invalido o competicion no incluida en tu plan")
            print(f"   Endpoint: {endpoint}")
            return {}
        else:
            print(f"[X] Error HTTP {e.response.status_code}: {e.response.text}")
            return {}
    
    except Exception as e:
        print(f"[X] Error en request: {e}")
        return {}


def get_competitions() -> pd.DataFrame:
    """
    Lista todas las competiciones disponibles
    
    Returns:
        DataFrame con competiciones
    """
    print("Obteniendo lista de competiciones...")
    data = api_request("/competitions")
    
    if not data or "competitions" not in data:
        return pd.DataFrame()
    
    rows = []
    for comp in data["competitions"]:
        rows.append({
            "id": comp.get("id"),
            "name": comp.get("name"),
            "code": comp.get("code"),
            "type": comp.get("type"),
            "country": comp.get("area", {}).get("name"),
            "current_season": comp.get("currentSeason", {}).get("startDate")
        })
    
    return pd.DataFrame(rows)


def get_matches(competition_code: str, season: Optional[str] = None, 
                status: str = "FINISHED") -> pd.DataFrame:
    """
    Obtiene partidos de una competición
    
    Args:
        competition_code: Código de competición (PL, PD, BL1, etc.)
        season: Año de temporada (ej: "2024") - None = temporada actual
        status: SCHEDULED | LIVE | IN_PLAY | PAUSED | FINISHED | POSTPONED | SUSPENDED | CANCELLED
    
    Returns:
        DataFrame con partidos
    """
    if competition_code not in COMPETITIONS:
        print(f"⚠️  Competición '{competition_code}' no reconocida")
        return pd.DataFrame()
    
    comp = COMPETITIONS[competition_code]
    print(f"Descargando partidos: {comp['name']} ({competition_code})")
    
    endpoint = f"/competitions/{competition_code}/matches"
    params = {"status": status}
    
    if season:
        params["season"] = season
    
    data = api_request(endpoint, params)
    
    if not data or "matches" not in data:
        return pd.DataFrame()
    
    rows = []
    for match in data["matches"]:
        rows.append({
            "date": match.get("utcDate"),
            "matchday": match.get("matchday"),
            "stage": match.get("stage"),
            "status": match.get("status"),
            "home_team": match.get("homeTeam", {}).get("name"),
            "away_team": match.get("awayTeam", {}).get("name"),
            "score_home": match.get("score", {}).get("fullTime", {}).get("home"),
            "score_away": match.get("score", {}).get("fullTime", {}).get("away"),
            "score_ht_home": match.get("score", {}).get("halfTime", {}).get("home"),
            "score_ht_away": match.get("score", {}).get("halfTime", {}).get("away"),
            "winner": match.get("score", {}).get("winner"),
            "competition": comp["name"],
            "competition_code": competition_code,
            "match_id": match.get("id"),
            "season": match.get("season", {}).get("startDate", "")[:4]
        })
    
    df = pd.DataFrame(rows)
    
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    
    return df


def get_standings(competition_code: str, season: Optional[str] = None) -> pd.DataFrame:
    """
    Obtiene tabla de posiciones
    
    Args:
        competition_code: Código de competición
        season: Año de temporada (None = actual)
    
    Returns:
        DataFrame con standings
    """
    if competition_code not in COMPETITIONS:
        return pd.DataFrame()
    
    comp = COMPETITIONS[competition_code]
    print(f"Descargando tabla: {comp['name']}")
    
    endpoint = f"/competitions/{competition_code}/standings"
    params = {"season": season} if season else {}
    
    data = api_request(endpoint, params)
    
    if not data or "standings" not in data:
        return pd.DataFrame()
    
    # Tomar tabla "TOTAL" (home + away)
    standings = next((s for s in data["standings"] if s.get("type") == "TOTAL"), None)
    
    if not standings:
        return pd.DataFrame()
    
    rows = []
    for entry in standings.get("table", []):
        rows.append({
            "position": entry.get("position"),
            "team": entry.get("team", {}).get("name"),
            "played": entry.get("playedGames"),
            "won": entry.get("won"),
            "draw": entry.get("draw"),
            "lost": entry.get("lost"),
            "points": entry.get("points"),
            "goals_for": entry.get("goalsFor"),
            "goals_against": entry.get("goalsAgainst"),
            "goal_difference": entry.get("goalDifference"),
            "form": entry.get("form"),  # Últimos 5 partidos (W/D/L)
            "competition": comp["name"],
            "competition_code": competition_code
        })
    
    return pd.DataFrame(rows)


def get_upcoming_matches(competition_code: str, days_ahead: int = 7) -> pd.DataFrame:
    """
    Obtiene próximos partidos (para picks/alertas)
    
    Args:
        competition_code: Código de competición
        days_ahead: Días hacia adelante a buscar
    
    Returns:
        DataFrame con fixtures próximos
    """
    if competition_code not in COMPETITIONS:
        return pd.DataFrame()
    
    comp = COMPETITIONS[competition_code]
    print(f"Próximos partidos ({days_ahead} días): {comp['name']}")
    
    today = datetime.utcnow().date()
    date_to = (today + timedelta(days=days_ahead)).isoformat()
    date_from = today.isoformat()
    
    endpoint = f"/competitions/{competition_code}/matches"
    params = {
        "status": "SCHEDULED",
        "dateFrom": date_from,
        "dateTo": date_to
    }
    
    data = api_request(endpoint, params)
    
    if not data or "matches" not in data:
        return pd.DataFrame()
    
    rows = []
    for match in data["matches"]:
        rows.append({
            "date": match.get("utcDate"),
            "matchday": match.get("matchday"),
            "home_team": match.get("homeTeam", {}).get("name"),
            "away_team": match.get("awayTeam", {}).get("name"),
            "competition": comp["name"],
            "competition_code": competition_code,
            "match_id": match.get("id")
        })
    
    df = pd.DataFrame(rows)
    
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    
    return df


def main():
    ap = argparse.ArgumentParser(
        description="football-data.org API - Datos en tiempo real"
    )
    ap.add_argument(
        "--competitions", 
        nargs="+", 
        default=["PL", "PD", "BL1", "SA", "FL1"],
        help="Códigos de competiciones (PL PD BL1 SA FL1 etc.)"
    )
    ap.add_argument(
        "--list-competitions",
        action="store_true",
        help="Lista todas las competiciones disponibles"
    )
    ap.add_argument(
        "--out-dir",
        default="data/raw/football_data_org",
        help="Directorio de salida"
    )
    ap.add_argument(
        "--mode",
        choices=["matches", "standings", "upcoming", "all"],
        default="all",
        help="Tipo de datos a descargar"
    )
    args = ap.parse_args()
    
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    
    print("\n" + "="*60)
    print("football-data.org API Integration")
    print("="*60 + "\n")
    
    # Listar competiciones
    if args.list_competitions:
        comps_df = get_competitions()
        if not comps_df.empty:
            print("\n[OK] Competiciones disponibles:\n")
            print(comps_df.to_string(index=False))
            
            fp = out / "competitions_available.csv"
            comps_df.to_csv(fp, index=False)
            print(f"\n[>] Guardado en: {fp}")
        return
    
    # Descargar datos por competición
    for comp_code in tqdm(args.competitions, desc="Competiciones"):
        if comp_code not in COMPETITIONS:
            print(f"\n[!] '{comp_code}' no reconocido. Usa --list-competitions")
            continue
        
        try:
            # Matches históricos (temporada actual)
            if args.mode in ["matches", "all"]:
                matches = get_matches(comp_code, status="FINISHED")
                if not matches.empty:
                    fp = out / f"{comp_code}_matches.csv"
                    matches.to_csv(fp, index=False)
                    print(f"  [OK] {len(matches)} partidos -> {fp.name}")
            
            # Tabla actual
            if args.mode in ["standings", "all"]:
                standings = get_standings(comp_code)
                if not standings.empty:
                    fp = out / f"{comp_code}_standings.csv"
                    standings.to_csv(fp, index=False)
                    print(f"  [OK] Tabla de {len(standings)} equipos -> {fp.name}")
            
            # Próximos partidos
            if args.mode in ["upcoming", "all"]:
                upcoming = get_upcoming_matches(comp_code, days_ahead=14)
                if not upcoming.empty:
                    fp = out / f"{comp_code}_upcoming.csv"
                    upcoming.to_csv(fp, index=False)
                    print(f"  [OK] {len(upcoming)} fixtures proximos -> {fp.name}")
        
        except Exception as e:
            print(f"  [ERROR] Error procesando {comp_code}: {e}")
            continue
    
    print("\n" + "="*60)
    print("[OK] Descarga completada!")
    print(f"[>] Archivos en: {out.absolute()}")
    print("="*60)
    print("\n[INFO] Uso:")
    print("  - Integra con tu pipeline de backtesting")
    print("  - Usa 'upcoming' para generar picks en producción")
    print("  - Complementa con Football-Data.co.uk (históricos + odds)")


if __name__ == "__main__":
    main()

