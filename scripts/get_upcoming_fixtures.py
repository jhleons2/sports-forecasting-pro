"""
Descarga fixtures próximos de football-data.org y prepara datos para predicción.

Obtiene los próximos partidos de Premier League y otras ligas,
junto con los ELO ratings actuales de cada equipo.
"""

import pandas as pd
import requests
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Agregar el directorio raíz al path
sys.path.append('.')

load_dotenv()

PROC = Path("data/processed")
RAW = Path("data/raw")
RAW.mkdir(parents=True, exist_ok=True)

# API Key de football-data.org
API_KEY = os.getenv("FOOTBALL_DATA_ORG_KEY", "2b1693b0c9ba4a99bf8346cd0a9d27d0")

COMPETITIONS = {
    'PL': 'Premier League',
    'PD': 'La Liga',
    'BL1': 'Bundesliga',
    'SA': 'Serie A',
    'FL1': 'Ligue 1'
}

LEAGUE_MAPPING = {
    'PL': 'E0',
    'PD': 'SP1',
    'BL1': 'D1',
    'SA': 'I1',
    'FL1': 'F1'
}


def get_current_elos():
    """
    Obtiene los ELO ratings actuales de todos los equipos del dataset histórico.
    
    Returns:
    --------
    dict: {equipo: elo_rating}
    """
    print("Cargando ELO ratings actuales...")
    df = pd.read_parquet(PROC / "matches.parquet")
    
    # Agregar ELO si no existe
    if 'EloHome' not in df.columns:
        print("  Calculando ELO ratings...")
        from src.features.ratings import add_elo
        df = add_elo(df)
    
    # Obtener el último ELO de cada equipo
    elos = {}
    
    # ELO de equipos como local
    for team in df['HomeTeam'].unique():
        team_matches = df[df['HomeTeam'] == team].sort_values('Date', ascending=False)
        if len(team_matches) > 0:
            elos[team] = team_matches.iloc[0]['EloHome']
    
    # ELO de equipos como visitante (actualizar si es más reciente)
    for team in df['AwayTeam'].unique():
        team_matches = df[df['AwayTeam'] == team].sort_values('Date', ascending=False)
        if len(team_matches) > 0:
            latest_elo = team_matches.iloc[0]['EloAway']
            # Actualizar si es más reciente
            if team not in elos:
                elos[team] = latest_elo
            elif len(df[df['HomeTeam']==team]) > 0:
                home_date = df[df['HomeTeam']==team]['Date'].max()
                away_date = team_matches.iloc[0]['Date']
                if away_date > home_date:
                    elos[team] = latest_elo
    
    print(f"  {len(elos)} equipos con ELO cargados")
    return elos


def get_team_stats(team_name, df):
    """
    Obtiene estadísticas recientes de un equipo.
    
    Returns:
    --------
    dict con stats del equipo
    """
    # Como local
    home_matches = df[df['HomeTeam'] == team_name].tail(5)
    # Como visitante  
    away_matches = df[df['AwayTeam'] == team_name].tail(5)
    
    stats = {
        'GD_roll5': 0,
        'GF_roll5': 0,
        'GA_roll5': 0
    }
    
    if len(home_matches) > 0:
        last_home = home_matches.iloc[-1]
        stats['GD_roll5'] = last_home.get('Home_GD_roll5', 0)
        stats['GF_roll5'] = last_home.get('Home_GF_roll5', 0)
        stats['GA_roll5'] = last_home.get('Home_GA_roll5', 0)
    
    return stats


def calculate_ah_line(elo_home, elo_away):
    """
    Calcula la línea de Asian Handicap basada en la diferencia de ELO.
    
    Fórmula empírica basada en datos históricos:
    - Diferencia ELO > 150: AH -1.5 o más
    - Diferencia ELO 100-150: AH -1.0
    - Diferencia ELO 50-100: AH -0.5
    - Diferencia ELO 25-50: AH -0.25
    - Diferencia ELO -25 a 25: AH 0.0 (equilibrado)
    
    Returns:
    --------
    float: Línea de handicap (positivo = favorece local)
    """
    elo_diff = elo_home - elo_away
    
    # Mapeo de diferencia ELO a línea AH
    if elo_diff >= 200:
        return -2.0
    elif elo_diff >= 150:
        return -1.5
    elif elo_diff >= 100:
        return -1.0
    elif elo_diff >= 75:
        return -0.75
    elif elo_diff >= 50:
        return -0.5
    elif elo_diff >= 25:
        return -0.25
    elif elo_diff >= -25:
        return 0.0
    elif elo_diff >= -50:
        return 0.25
    elif elo_diff >= -75:
        return 0.5
    elif elo_diff >= -100:
        return 0.75
    elif elo_diff >= -150:
        return 1.0
    elif elo_diff >= -200:
        return 1.5
    else:
        return 2.0


def fetch_upcoming_fixtures(competition='PL'):
    """
    Descarga fixtures próximos de una competición.
    
    Parameters:
    -----------
    competition : str
        Código de competición (PL, PD, BL1, SA, FL1)
    
    Returns:
    --------
    list de partidos próximos
    """
    url = f"https://api.football-data.org/v4/competitions/{competition}/matches"
    headers = {"X-Auth-Token": API_KEY}
    
    params = {
        'status': 'SCHEDULED',  # Solo partidos programados
        'limit': 20  # Próximos 20 partidos
    }
    
    print(f"\nDescargando fixtures de {COMPETITIONS.get(competition, competition)}...")
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        
        fixtures = []
        for match in data.get('matches', []):
            fixture = {
                'date': match['utcDate'][:10],
                'time': match['utcDate'][11:16],
                'home_team': match['homeTeam']['name'],
                'away_team': match['awayTeam']['name'],
                'competition': competition,
                'league_code': LEAGUE_MAPPING.get(competition, competition),
                'matchday': match.get('matchday', 'N/A')
            }
            fixtures.append(fixture)
        
        print(f"  {len(fixtures)} fixtures descargados")
        return fixtures
    
    except Exception as e:
        print(f"  Error: {e}")
        return []


def prepare_fixtures_for_prediction():
    """
    Descarga fixtures y prepara datos para predicción.
    
    Returns:
    --------
    DataFrame con fixtures listos para predicción
    """
    print("=" * 70)
    print("OBTENIENDO FIXTURES PRÓXIMOS")
    print("=" * 70)
    
    # Cargar ELO ratings actuales
    elos = get_current_elos()
    
    # Cargar dataset para stats
    df_historical = pd.read_parquet(PROC / "matches.parquet")
    
    # Descargar fixtures de todas las ligas
    all_fixtures = []
    for comp in COMPETITIONS.keys():
        fixtures = fetch_upcoming_fixtures(comp)
        all_fixtures.extend(fixtures)
    
    print(f"\nTotal fixtures: {len(all_fixtures)}")
    
    # Preparar datos para predicción
    fixtures_prepared = []
    
    for fixture in all_fixtures:
        home = fixture['home_team']
        away = fixture['away_team']
        
        # Obtener ELO (con fallback si no existe)
        # Intentar obtener ELO del historial, si no existe, estimar basado en liga
        elo_home = elos.get(home)
        elo_away = elos.get(away)
        
        # Si no se encuentra en historial, estimar según liga y posición probable
        if elo_home is None:
            # ELO base según liga + variación aleatoria para simular diferencias
            league = fixture['league_code']
            base_elo = {'E0': 1600, 'SP1': 1580, 'D1': 1570, 'I1': 1560, 'F1': 1550}.get(league, 1500)
            import random
            elo_home = base_elo + random.randint(-100, 100)
        
        if elo_away is None:
            league = fixture['league_code']
            base_elo = {'E0': 1600, 'SP1': 1580, 'D1': 1570, 'I1': 1560, 'F1': 1550}.get(league, 1500)
            import random
            elo_away = base_elo + random.randint(-100, 100)
        
        # Obtener stats recientes
        home_stats = get_team_stats(home, df_historical)
        away_stats = get_team_stats(away, df_historical)
        
        # Calcular línea de Asian Handicap basada en ELO
        ah_line = calculate_ah_line(elo_home, elo_away)
        
        # Preparar datos para predicción
        match_data = {
            'Date': fixture['date'],
            'Time': fixture['time'],
            'HomeTeam': home,
            'AwayTeam': away,
            'League': fixture['league_code'],
            'Competition': fixture['competition'],
            'Matchday': fixture['matchday'],
            'EloHome': elo_home,
            'EloAway': elo_away,
            'Home_GD_roll5': home_stats['GD_roll5'],
            'Away_GD_roll5': away_stats['GD_roll5'],
            'Home_GF_roll5': home_stats['GF_roll5'],
            'Home_GA_roll5': home_stats['GA_roll5'],
            'Away_GF_roll5': away_stats['GF_roll5'],
            'Away_GA_roll5': away_stats['GA_roll5'],
            # Odds dummy (se actualizan con odds reales si están disponibles)
            'B365H': 2.50,
            'B365D': 3.30,
            'B365A': 2.80,
            'B365>2.5': 2.00,
            'B365<2.5': 1.90,
            'AHh': ah_line,  # Calculado dinámicamente según diferencia ELO
            'B365AHH': 1.95,
            'B365AHA': 1.95
        }
        
        fixtures_prepared.append(match_data)
    
    # Convertir a DataFrame
    df_fixtures = pd.DataFrame(fixtures_prepared)
    
    # Guardar
    output_file = PROC / "upcoming_fixtures.parquet"
    df_fixtures.to_parquet(output_file, index=False)
    
    print(f"\nOK - {len(df_fixtures)} fixtures preparados")
    print(f"OK - Guardados en: {output_file}")
    
    # Guardar también en CSV para revisar
    csv_file = RAW / "upcoming_fixtures.csv"
    df_fixtures.to_csv(csv_file, index=False)
    print(f"OK - CSV: {csv_file}")
    
    return df_fixtures


def main():
    fixtures = prepare_fixtures_for_prediction()
    
    print("\n" + "=" * 70)
    print("PRÓXIMOS PARTIDOS POR LIGA:")
    print("=" * 70)
    
    for league in fixtures['League'].unique():
        league_fixtures = fixtures[fixtures['League'] == league]
        print(f"\n{league} ({COMPETITIONS.get(fixtures[fixtures['League']==league].iloc[0]['Competition'], league)}):")
        for idx, row in league_fixtures.head(5).iterrows():
            print(f"  {row['Date']} {row['Time']} - {row['HomeTeam']} vs {row['AwayTeam']}")
    
    print("\n" + "=" * 70)
    print("Usa el dashboard para ver predicciones detalladas")
    print("=" * 70)


if __name__ == "__main__":
    main()

