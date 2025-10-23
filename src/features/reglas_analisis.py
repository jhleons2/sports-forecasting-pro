"""
REGLAS DE ANÁLISIS PROFESIONAL
================================

Implementa las reglas específicas para análisis de partidos:

1. Últimos 8 partidos TOTAL (misma liga)
2. Últimos 5 de VISITANTE (misma liga)
3. Últimos 5 de LOCAL (misma liga)
4. Últimos 5 ENTRE SÍ (H2H - cualquier liga)
5. Bajas de jugadores (requiere API)

Todas las ventanas se calculan POR LIGA para mayor precisión.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional


def add_reglas_analisis(df: pd.DataFrame) -> pd.DataFrame:
    """
    Añade features siguiendo las reglas específicas de análisis.
    
    Reglas implementadas:
    1. Últimos 8 partidos total (misma liga)
    2. Últimos 5 como visitante (misma liga)
    3. Últimos 5 como local (misma liga)
    4. Últimos 5 H2H (entre equipos específicos)
    5. Bajas de jugadores (placeholder para API)
    
    Parameters:
    -----------
    df : pd.DataFrame
        Dataset con partidos históricos
        
    Returns:
    --------
    df : pd.DataFrame
        Dataset con features de reglas añadidos
    """
    print("\n" + "=" * 70)
    print("  APLICANDO REGLAS DE ANÁLISIS PROFESIONAL")
    print("=" * 70)
    
    df = df.sort_values(['League', 'Date']).copy()
    
    # ============================================================
    # REGLA 1: ÚLTIMOS 8 PARTIDOS TOTAL (MISMA LIGA)
    # ============================================================
    print("\n[REGLA 1] Últimos 8 partidos total (misma liga)...")
    
    # Por cada equipo en cada liga
    for league in df['League'].unique():
        league_df = df[df['League'] == league].copy()
        
        for team_col, gf_col, ga_col, prefix in [
            ('HomeTeam', 'FTHG', 'FTAG', 'Home'),
            ('AwayTeam', 'FTAG', 'FTHG', 'Away')
        ]:
            # Agrupar por equipo
            for team in league_df[team_col].unique():
                # Obtener todos los partidos del equipo (como local O visitante)
                team_home = league_df[league_df['HomeTeam'] == team].copy()
                team_away = league_df[league_df['AwayTeam'] == team].copy()
                
                # Combinar y ordenar por fecha
                all_matches = pd.concat([team_home, team_away]).sort_values('Date')
                
                # Calcular rolling últimos 8
                gf_values = []
                ga_values = []
                pts_values = []
                
                for idx in all_matches.index:
                    # Obtener últimos 8 partidos ANTES de este
                    prev_matches = all_matches[all_matches['Date'] < all_matches.loc[idx, 'Date']].tail(8)
                    
                    if len(prev_matches) > 0:
                        # Goles a favor
                        gf = 0
                        ga = 0
                        pts = 0
                        
                        for _, match in prev_matches.iterrows():
                            if match['HomeTeam'] == team:
                                gf += match['FTHG']
                                ga += match['FTAG']
                                if match['FTHG'] > match['FTAG']:
                                    pts += 3
                                elif match['FTHG'] == match['FTAG']:
                                    pts += 1
                            else:  # Away
                                gf += match['FTAG']
                                ga += match['FTHG']
                                if match['FTAG'] > match['FTHG']:
                                    pts += 3
                                elif match['FTAG'] == match['FTHG']:
                                    pts += 1
                        
                        gf_values.append(gf)
                        ga_values.append(ga)
                        pts_values.append(pts)
                    else:
                        gf_values.append(0)
                        ga_values.append(0)
                        pts_values.append(0)
                
                # Asignar valores al DataFrame original
                for i, idx in enumerate(all_matches.index):
                    if all_matches.loc[idx, team_col] == team:
                        df.at[idx, f'{prefix}_GF_ultimos8_liga'] = gf_values[i]
                        df.at[idx, f'{prefix}_GA_ultimos8_liga'] = ga_values[i]
                        df.at[idx, f'{prefix}_GD_ultimos8_liga'] = gf_values[i] - ga_values[i]
                        df.at[idx, f'{prefix}_Pts_ultimos8_liga'] = pts_values[i]
    
    # Llenar NaN con 0
    for col in [c for c in df.columns if 'ultimos8_liga' in c]:
        df[col] = df[col].fillna(0)
    
    print("   ✅ 8 columnas añadidas (4 home + 4 away)")
    
    # ============================================================
    # REGLA 2 & 3: ÚLTIMOS 5 LOCAL / ÚLTIMOS 5 VISITANTE (MISMA LIGA)
    # ============================================================
    print("\n[REGLA 2 & 3] Últimos 5 como local / Últimos 5 como visitante (misma liga)...")
    
    # Ya implementado en professional_features.py
    # Vamos a añadir una versión específica por liga
    
    for league in df['League'].unique():
        league_mask = df['League'] == league
        league_df = df[league_mask].copy()
        
        # Home (como local en esta liga)
        home_groups = league_df.groupby('HomeTeam')
        
        df.loc[league_mask, 'Home_GF_local5_liga'] = home_groups['FTHG'].rolling(5, min_periods=1).sum().reset_index(level=0, drop=True)
        df.loc[league_mask, 'Home_GA_local5_liga'] = home_groups['FTAG'].rolling(5, min_periods=1).sum().reset_index(level=0, drop=True)
        df.loc[league_mask, 'Home_GD_local5_liga'] = df.loc[league_mask, 'Home_GF_local5_liga'] - df.loc[league_mask, 'Home_GA_local5_liga']
        
        # Away (como visitante en esta liga)
        away_groups = league_df.groupby('AwayTeam')
        
        df.loc[league_mask, 'Away_GF_visitante5_liga'] = away_groups['FTAG'].rolling(5, min_periods=1).sum().reset_index(level=0, drop=True)
        df.loc[league_mask, 'Away_GA_visitante5_liga'] = away_groups['FTHG'].rolling(5, min_periods=1).sum().reset_index(level=0, drop=True)
        df.loc[league_mask, 'Away_GD_visitante5_liga'] = df.loc[league_mask, 'Away_GF_visitante5_liga'] - df.loc[league_mask, 'Away_GA_visitante5_liga']
    
    # Llenar NaN con 0
    for col in [c for c in df.columns if '_liga' in c and ('local5' in c or 'visitante5' in c)]:
        df[col] = df[col].fillna(0)
    
    print("   ✅ 6 columnas añadidas (3 local + 3 visitante)")
    
    # ============================================================
    # REGLA 4: ÚLTIMOS 5 ENTRE SÍ (H2H)
    # ============================================================
    print("\n[REGLA 4] Últimos 5 enfrentamientos directos (H2H)...")
    
    # Inicializar columnas
    h2h_cols = {
        'H2H5_home_wins': 0,
        'H2H5_draws': 0,
        'H2H5_away_wins': 0,
        'H2H5_home_goals_avg': 0.0,
        'H2H5_away_goals_avg': 0.0,
        'H2H5_total_goals_avg': 0.0,
        'H2H5_matches': 0
    }
    
    for col, default in h2h_cols.items():
        df[col] = default
    
    # Calcular H2H
    for idx, row in df.iterrows():
        home = row['HomeTeam']
        away = row['AwayTeam']
        date = row['Date']
        
        # Buscar últimos 5 enfrentamientos (cualquier orden)
        h2h = df[
            (df['Date'] < date) &
            (
                ((df['HomeTeam'] == home) & (df['AwayTeam'] == away)) |
                ((df['HomeTeam'] == away) & (df['AwayTeam'] == home))
            )
        ].tail(5)
        
        if len(h2h) > 0:
            home_wins = 0
            draws = 0
            away_wins = 0
            home_goals = []
            away_goals = []
            
            for _, h2h_match in h2h.iterrows():
                if h2h_match['HomeTeam'] == home:
                    # Mismo orden
                    if h2h_match['FTHG'] > h2h_match['FTAG']:
                        home_wins += 1
                    elif h2h_match['FTHG'] == h2h_match['FTAG']:
                        draws += 1
                    else:
                        away_wins += 1
                    home_goals.append(h2h_match['FTHG'])
                    away_goals.append(h2h_match['FTAG'])
                else:
                    # Orden invertido
                    if h2h_match['FTAG'] > h2h_match['FTHG']:
                        home_wins += 1
                    elif h2h_match['FTHG'] == h2h_match['FTAG']:
                        draws += 1
                    else:
                        away_wins += 1
                    home_goals.append(h2h_match['FTAG'])
                    away_goals.append(h2h_match['FTHG'])
            
            df.at[idx, 'H2H5_home_wins'] = home_wins
            df.at[idx, 'H2H5_draws'] = draws
            df.at[idx, 'H2H5_away_wins'] = away_wins
            df.at[idx, 'H2H5_home_goals_avg'] = np.mean(home_goals)
            df.at[idx, 'H2H5_away_goals_avg'] = np.mean(away_goals)
            df.at[idx, 'H2H5_total_goals_avg'] = np.mean(home_goals) + np.mean(away_goals)
            df.at[idx, 'H2H5_matches'] = len(h2h)
    
    h2h_count = (df['H2H5_matches'] > 0).sum()
    print(f"   ✅ 7 columnas H2H añadidas")
    print(f"   📊 {h2h_count} partidos con H2H data ({h2h_count/len(df)*100:.1f}%)")
    
    # ============================================================
    # REGLA 5: BAJAS DE JUGADORES (PLACEHOLDER)
    # ============================================================
    print("\n[REGLA 5] Bajas de jugadores (requiere API externa)...")
    
    # Placeholder para integración futura con API
    df['Home_jugadores_clave_bajas'] = 0
    df['Away_jugadores_clave_bajas'] = 0
    df['Home_jugadores_suspendidos'] = 0
    df['Away_jugadores_suspendidos'] = 0
    
    print("   ⚠️  Placeholder creado (4 columnas)")
    print("   📝 Integrar con API-FOOTBALL /injuries para datos reales")
    
    # ============================================================
    # RESUMEN
    # ============================================================
    print("\n" + "=" * 70)
    print("  RESUMEN DE REGLAS APLICADAS")
    print("=" * 70)
    print("""
    ✅ REGLA 1: Últimos 8 partidos total (misma liga) - 8 columnas
    ✅ REGLA 2: Últimos 5 como local (misma liga) - 3 columnas
    ✅ REGLA 3: Últimos 5 como visitante (misma liga) - 3 columnas
    ✅ REGLA 4: Últimos 5 H2H - 7 columnas
    ⚠️  REGLA 5: Bajas de jugadores - 4 columnas (placeholder)
    
    Total: 25 columnas añadidas
    """)
    
    return df


def get_analisis_partido(df: pd.DataFrame, home_team: str, away_team: str, league: str) -> Dict:
    """
    Obtiene análisis completo de un partido siguiendo las 5 reglas.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Dataset con features de reglas
    home_team : str
        Equipo local
    away_team : str
        Equipo visitante
    league : str
        Liga del partido
        
    Returns:
    --------
    dict : Análisis completo del partido
    """
    # Buscar último partido entre estos equipos
    match = df[
        (df['HomeTeam'] == home_team) &
        (df['AwayTeam'] == away_team) &
        (df['League'] == league)
    ].tail(1)
    
    if len(match) == 0:
        return {'error': 'Partido no encontrado'}
    
    match = match.iloc[0]
    
    analisis = {
        'partido': f"{home_team} vs {away_team}",
        'liga': league,
        
        # REGLA 1: Últimos 8 total
        'ultimos_8_total': {
            'home': {
                'gf': match.get('Home_GF_ultimos8_liga', 0),
                'ga': match.get('Home_GA_ultimos8_liga', 0),
                'gd': match.get('Home_GD_ultimos8_liga', 0),
                'pts': match.get('Home_Pts_ultimos8_liga', 0)
            },
            'away': {
                'gf': match.get('Away_GF_ultimos8_liga', 0),
                'ga': match.get('Away_GA_ultimos8_liga', 0),
                'gd': match.get('Away_GD_ultimos8_liga', 0),
                'pts': match.get('Away_Pts_ultimos8_liga', 0)
            }
        },
        
        # REGLA 2: Últimos 5 local
        'ultimos_5_local': {
            'gf': match.get('Home_GF_local5_liga', 0),
            'ga': match.get('Home_GA_local5_liga', 0),
            'gd': match.get('Home_GD_local5_liga', 0)
        },
        
        # REGLA 3: Últimos 5 visitante
        'ultimos_5_visitante': {
            'gf': match.get('Away_GF_visitante5_liga', 0),
            'ga': match.get('Away_GA_visitante5_liga', 0),
            'gd': match.get('Away_GD_visitante5_liga', 0)
        },
        
        # REGLA 4: Últimos 5 H2H
        'ultimos_5_h2h': {
            'home_wins': match.get('H2H5_home_wins', 0),
            'draws': match.get('H2H5_draws', 0),
            'away_wins': match.get('H2H5_away_wins', 0),
            'home_goals_avg': match.get('H2H5_home_goals_avg', 0),
            'away_goals_avg': match.get('H2H5_away_goals_avg', 0),
            'total_goals_avg': match.get('H2H5_total_goals_avg', 0),
            'partidos': match.get('H2H5_matches', 0)
        },
        
        # REGLA 5: Bajas
        'bajas_jugadores': {
            'home_bajas': match.get('Home_jugadores_clave_bajas', 0),
            'away_bajas': match.get('Away_jugadores_clave_bajas', 0),
            'home_suspendidos': match.get('Home_jugadores_suspendidos', 0),
            'away_suspendidos': match.get('Away_jugadores_suspendidos', 0)
        }
    }
    
    return analisis


def formato_analisis_texto(analisis: Dict) -> str:
    """
    Formatea el análisis en texto legible.
    
    Parameters:
    -----------
    analisis : dict
        Diccionario con análisis del partido
        
    Returns:
    --------
    str : Texto formateado
    """
    if 'error' in analisis:
        return f"❌ Error: {analisis['error']}"
    
    texto = f"""
╔════════════════════════════════════════════════════════════════╗
║  ANÁLISIS COMPLETO: {analisis['partido']:^42s}  ║
║  Liga: {analisis['liga']:^56s}  ║
╚════════════════════════════════════════════════════════════════╝

📊 REGLA 1: ÚLTIMOS 8 PARTIDOS TOTAL (MISMA LIGA)
────────────────────────────────────────────────────────────────
  {analisis['partido'].split(' vs ')[0]}:
    Goles a favor:    {analisis['ultimos_8_total']['home']['gf']:.0f}
    Goles en contra:  {analisis['ultimos_8_total']['home']['ga']:.0f}
    Diferencia:       {analisis['ultimos_8_total']['home']['gd']:+.0f}
    Puntos:           {analisis['ultimos_8_total']['home']['pts']:.0f}/24

  {analisis['partido'].split(' vs ')[1]}:
    Goles a favor:    {analisis['ultimos_8_total']['away']['gf']:.0f}
    Goles en contra:  {analisis['ultimos_8_total']['away']['ga']:.0f}
    Diferencia:       {analisis['ultimos_8_total']['away']['gd']:+.0f}
    Puntos:           {analisis['ultimos_8_total']['away']['pts']:.0f}/24

🏠 REGLA 2: ÚLTIMOS 5 COMO LOCAL (MISMA LIGA)
────────────────────────────────────────────────────────────────
  {analisis['partido'].split(' vs ')[0]}:
    Goles a favor:    {analisis['ultimos_5_local']['gf']:.0f}
    Goles en contra:  {analisis['ultimos_5_local']['ga']:.0f}
    Diferencia:       {analisis['ultimos_5_local']['gd']:+.0f}

✈️  REGLA 3: ÚLTIMOS 5 COMO VISITANTE (MISMA LIGA)
────────────────────────────────────────────────────────────────
  {analisis['partido'].split(' vs ')[1]}:
    Goles a favor:    {analisis['ultimos_5_visitante']['gf']:.0f}
    Goles en contra:  {analisis['ultimos_5_visitante']['ga']:.0f}
    Diferencia:       {analisis['ultimos_5_visitante']['gd']:+.0f}

🔄 REGLA 4: ÚLTIMOS 5 ENFRENTAMIENTOS DIRECTOS
────────────────────────────────────────────────────────────────
  Partidos H2H:     {analisis['ultimos_5_h2h']['partidos']:.0f}
  Victorias local:  {analisis['ultimos_5_h2h']['home_wins']:.0f}
  Empates:          {analisis['ultimos_5_h2h']['draws']:.0f}
  Victorias visit:  {analisis['ultimos_5_h2h']['away_wins']:.0f}
  
  Goles promedio:
    Local:          {analisis['ultimos_5_h2h']['home_goals_avg']:.1f}
    Visitante:      {analisis['ultimos_5_h2h']['away_goals_avg']:.1f}
    Total:          {analisis['ultimos_5_h2h']['total_goals_avg']:.1f}

⚠️  REGLA 5: BAJAS DE JUGADORES
────────────────────────────────────────────────────────────────
  {analisis['partido'].split(' vs ')[0]}:
    Jugadores clave bajas:  {analisis['bajas_jugadores']['home_bajas']:.0f}
    Suspendidos:            {analisis['bajas_jugadores']['home_suspendidos']:.0f}
  
  {analisis['partido'].split(' vs ')[1]}:
    Jugadores clave bajas:  {analisis['bajas_jugadores']['away_bajas']:.0f}
    Suspendidos:            {analisis['bajas_jugadores']['away_suspendidos']:.0f}

╚════════════════════════════════════════════════════════════════╝
"""
    
    return texto


if __name__ == "__main__":
    print("""
    MÓDULO DE REGLAS DE ANÁLISIS
    =============================
    
    Uso:
    
    from src.features.reglas_analisis import add_reglas_analisis, get_analisis_partido
    
    # Añadir features
    df = pd.read_parquet("data/processed/matches.parquet")
    df = add_reglas_analisis(df)
    
    # Obtener análisis
    analisis = get_analisis_partido(df, "Arsenal", "Chelsea", "E0")
    print(formato_analisis_texto(analisis))
    """)

