"""
FBref Scraper - Estadísticas Avanzadas de Fútbol
Fuente: https://fbref.com/

LEGAL: FBref permite scraping educativo con rate limiting (<20 req/min)
Ver: https://www.sports-reference.com/bot-traffic.html

Features disponibles:
- Estadísticas de tiros (xG, SoT, Dist)
- Métricas de pases (Cmp%, PrgP, PrgC)
- Acciones defensivas (Tkl, Int, Blocks)
- Presión (Press%, Def3rd, Mid3rd, Att3rd)
"""

import argparse
import time
from pathlib import Path
from typing import Dict, List
import pandas as pd
from tqdm import tqdm

# Rate limiting: FBref permite ~20 req/min
# Usamos 15 req/min para estar seguros
REQUEST_DELAY = 4.0  # segundos entre requests

LEAGUE_URLS = {
    "EPL": "https://fbref.com/en/comps/9/Premier-League-Stats",
    "La_Liga": "https://fbref.com/en/comps/12/La-Liga-Stats",
    "Bundesliga": "https://fbref.com/en/comps/20/Bundesliga-Stats",
    "Serie_A": "https://fbref.com/en/comps/11/Serie-A-Stats",
    "Ligue_1": "https://fbref.com/en/comps/13/Ligue-1-Stats"
}

# Para temporadas específicas, formato: /YYYY-YYYY/
# Ej: https://fbref.com/en/comps/9/2023-2024/2023-2024-Premier-League-Stats

def scrape_league_table(league_url: str) -> pd.DataFrame:
    """
    Scrape tabla de posiciones de liga
    
    Returns:
        DataFrame con: Squad, MP, W, D, L, GF, GA, GD, Pts, xG, xGA
    """
    print(f"Scraping: {league_url}")
    time.sleep(REQUEST_DELAY)
    
    try:
        tables = pd.read_html(league_url)
        # La tabla de posiciones generalmente es la primera
        df = tables[0]
        
        # Limpiar columnas multi-nivel si existen
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = ['_'.join(col).strip() if col[1] else col[0] 
                         for col in df.columns.values]
        
        # Renombrar para consistencia
        df = df.rename(columns={
            'Squad': 'Team',
            'Rk': 'Position'
        })
        
        return df
    except Exception as e:
        print(f"Error scraping {league_url}: {e}")
        return pd.DataFrame()


def scrape_team_shooting_stats(league_url: str) -> pd.DataFrame:
    """
    Scrape estadísticas de tiros por equipo
    
    Incluye: xG, SoT%, Dist, FK, PK
    """
    # Construir URL de shooting stats
    shooting_url = league_url.replace("-Stats", "-Shooting-Stats")
    
    print(f"Scraping shooting: {shooting_url}")
    time.sleep(REQUEST_DELAY)
    
    try:
        tables = pd.read_html(shooting_url)
        # Buscar tabla con estadísticas de tiros
        for df in tables:
            if 'Squad' in df.columns or ('Squad' in str(df.columns)):
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = ['_'.join(col).strip() if col[1] else col[0] 
                                 for col in df.columns.values]
                df = df.rename(columns={'Squad': 'Team'})
                return df
        return pd.DataFrame()
    except Exception as e:
        print(f"Error scraping shooting stats: {e}")
        return pd.DataFrame()


def scrape_team_passing_stats(league_url: str) -> pd.DataFrame:
    """
    Scrape estadísticas de pases por equipo
    
    Incluye: Cmp%, TotDist, PrgDist, PrgP (pases progresivos)
    """
    passing_url = league_url.replace("-Stats", "-Passing-Stats")
    
    print(f"Scraping passing: {passing_url}")
    time.sleep(REQUEST_DELAY)
    
    try:
        tables = pd.read_html(passing_url)
        for df in tables:
            if 'Squad' in df.columns or ('Squad' in str(df.columns)):
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = ['_'.join(col).strip() if col[1] else col[0] 
                                 for col in df.columns.values]
                df = df.rename(columns={'Squad': 'Team'})
                return df
        return pd.DataFrame()
    except Exception as e:
        print(f"Error scraping passing stats: {e}")
        return pd.DataFrame()


def scrape_team_defense_stats(league_url: str) -> pd.DataFrame:
    """
    Scrape estadísticas defensivas por equipo
    
    Incluye: Tkl, TklW, Int, Blocks, Clr, Err
    """
    defense_url = league_url.replace("-Stats", "-Defense-Stats")
    
    print(f"Scraping defense: {defense_url}")
    time.sleep(REQUEST_DELAY)
    
    try:
        tables = pd.read_html(defense_url)
        for df in tables:
            if 'Squad' in df.columns or ('Squad' in str(df.columns)):
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = ['_'.join(col).strip() if col[1] else col[0] 
                                 for col in df.columns.values]
                df = df.rename(columns={'Squad': 'Team'})
                return df
        return pd.DataFrame()
    except Exception as e:
        print(f"Error scraping defense stats: {e}")
        return pd.DataFrame()


def scrape_league_full(league_key: str, league_url: str, season: str = "current") -> Dict[str, pd.DataFrame]:
    """
    Scrape todas las estadísticas disponibles de una liga
    
    Args:
        league_key: Código de liga (EPL, La_Liga, etc.)
        league_url: URL base de FBref
        season: 'current' o 'YYYY-YYYY'
    
    Returns:
        Dict con DataFrames: 'table', 'shooting', 'passing', 'defense'
    """
    # Ajustar URL para temporada específica
    if season != "current":
        # Insertar temporada en URL
        # Ejemplo: .../comps/9/Premier-League-Stats
        #       -> .../comps/9/2023-2024/2023-2024-Premier-League-Stats
        parts = league_url.split('/')
        comp_id = parts[5]  # '9', '12', etc.
        league_name = parts[-1].replace('-Stats', '')
        league_url = f"https://fbref.com/en/comps/{comp_id}/{season}/{season}-{league_name}-Stats"
    
    print(f"\n{'='*60}")
    print(f"Scraping {league_key} - Season: {season}")
    print(f"{'='*60}\n")
    
    data = {}
    
    # 1. Tabla de posiciones
    data['table'] = scrape_league_table(league_url)
    
    # 2. Estadísticas de tiros
    data['shooting'] = scrape_team_shooting_stats(league_url)
    
    # 3. Estadísticas de pases
    data['passing'] = scrape_team_passing_stats(league_url)
    
    # 4. Estadísticas defensivas
    data['defense'] = scrape_team_defense_stats(league_url)
    
    return data


def merge_all_stats(stats_dict: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """
    Merge todas las estadísticas en un único DataFrame
    
    Join por columna 'Team'
    """
    if not stats_dict or 'table' not in stats_dict:
        return pd.DataFrame()
    
    df = stats_dict['table'].copy()
    
    # Merge progresivo
    for key in ['shooting', 'passing', 'defense']:
        if key in stats_dict and not stats_dict[key].empty:
            # Evitar duplicar columnas comunes (MP, W, D, L, etc.)
            aux = stats_dict[key].copy()
            common_cols = set(df.columns) & set(aux.columns)
            cols_to_drop = [c for c in common_cols if c != 'Team']
            if cols_to_drop:
                aux = aux.drop(columns=cols_to_drop)
            
            df = df.merge(aux, on='Team', how='left')
    
    return df


def main():
    ap = argparse.ArgumentParser(description="FBref Scraper - Estadísticas Avanzadas")
    ap.add_argument("--leagues", nargs="+", default=list(LEAGUE_URLS.keys()),
                    help="Ligas a descargar: EPL La_Liga Bundesliga Serie_A Ligue_1")
    ap.add_argument("--season", default="current",
                    help="Temporada: 'current' o 'YYYY-YYYY' (ej: 2023-2024)")
    ap.add_argument("--out_dir", default="data/raw/fbref")
    args = ap.parse_args()
    
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    
    print(f"\n{'#'*60}")
    print(f"# FBref Scraper - Rate Limited (4s delay)")
    print(f"# Leagues: {', '.join(args.leagues)}")
    print(f"# Season: {args.season}")
    print(f"{'#'*60}\n")
    
    for league in tqdm(args.leagues, desc="Ligas"):
        if league not in LEAGUE_URLS:
            print(f"⚠️  Liga '{league}' no soportada. Disponibles: {list(LEAGUE_URLS.keys())}")
            continue
        
        try:
            # Scrape all stats
            stats = scrape_league_full(league, LEAGUE_URLS[league], args.season)
            
            # Guardar por separado
            season_str = args.season if args.season != "current" else "latest"
            for stat_type, df in stats.items():
                if not df.empty:
                    fp = out / f"{league}_{season_str}_{stat_type}.csv"
                    df.to_csv(fp, index=False)
                    print(f"✅ Guardado: {fp} ({len(df)} equipos)")
            
            # Guardar merged
            merged = merge_all_stats(stats)
            if not merged.empty:
                fp_merged = out / f"{league}_{season_str}_full.csv"
                merged.to_csv(fp_merged, index=False)
                print(f"✅ Guardado merged: {fp_merged}\n")
        
        except Exception as e:
            print(f"❌ Error procesando {league}: {e}\n")
            continue
    
    print("\n" + "="*60)
    print("✅ Scraping completado!")
    print(f"📁 Archivos guardados en: {out.absolute()}")
    print("="*60)
    print("\n⚠️  IMPORTANTE:")
    print("- FBref permite scraping educativo con rate limiting")
    print("- Respeta el delay de 4s entre requests")
    print("- NO uses esto en producción sin permiso explícito")
    print("- Atribuye la fuente en tus análisis: https://fbref.com/")


if __name__ == "__main__":
    main()

