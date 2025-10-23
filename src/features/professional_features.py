"""
MÓDULO DE FEATURES PROFESIONALES
=================================

Implementa las mejores prácticas de analistas y casas de apuestas:

1. Head-to-Head (H2H) - Últimos 3-5 enfrentamientos directos
2. Rendimiento Casa/Fuera SEPARADO - Últimos 5 partidos por contexto
3. Múltiples Ventanas Temporales - Forma actual (5) vs medio plazo (10-15)
4. Contexto y Motivación - Posición en tabla, streaks
5. Estadísticas Avanzadas - xG rolling, shot accuracy, etc.

Referencia: Análisis multicapa usado por casas de apuestas profesionales.
"""

import pandas as pd
import numpy as np
from typing import Optional, Tuple, Dict


def add_head_to_head_features(df: pd.DataFrame, n_matches: int = 5) -> pd.DataFrame:
    """
    Añade features de enfrentamientos directos (H2H).
    
    Los enfrentamientos históricos revelan:
    - Ventajas psicológicas ("maldiciones")
    - Patrones tácticos recurrentes
    - Favoritos históricos
    
    Parameters:
    -----------
    df : pd.DataFrame
        Dataset ordenado por fecha
    n_matches : int
        Número de enfrentamientos previos a considerar (default: 5)
    
    Returns:
    --------
    df : pd.DataFrame
        Dataset con nuevas columnas H2H
    
    Columnas añadidas:
    ------------------
    - H2H_home_wins: Victorias locales en últimos N enfrentamientos
    - H2H_draws: Empates en últimos N enfrentamientos
    - H2H_away_wins: Victorias visitantes en últimos N enfrentamientos
    - H2H_home_goals_avg: Goles promedio del local en H2H
    - H2H_away_goals_avg: Goles promedio del visitante en H2H
    - H2H_total_goals_avg: Total de goles promedio en H2H
    - H2H_home_win_rate: % de victorias del local en H2H
    - H2H_home_dominance: Ratio de dominancia (-1 a +1)
    
    Ejemplo:
    --------
    Si Tottenham vs Chelsea:
    - H2H_home_wins = 1 (de últimos 5)
    - H2H_away_wins = 4 (de últimos 5)
    - H2H_home_dominance = -0.6 (Chelsea domina)
    """
    df = df.sort_values('Date').copy()
    
    # Inicializar columnas
    h2h_cols = {
        'H2H_home_wins': 0,
        'H2H_draws': 0,
        'H2H_away_wins': 0,
        'H2H_home_goals_avg': 0.0,
        'H2H_away_goals_avg': 0.0,
        'H2H_total_goals_avg': 0.0,
        'H2H_home_win_rate': 0.0,
        'H2H_home_dominance': 0.0,
        'H2H_matches_found': 0
    }
    
    for col, default in h2h_cols.items():
        df[col] = default
    
    # Para cada partido, buscar enfrentamientos previos
    for idx, row in df.iterrows():
        home = row['HomeTeam']
        away = row['AwayTeam']
        date = row['Date']
        
        # Buscar enfrentamientos previos (cualquier orden de local/visitante)
        h2h_matches = df[
            (df['Date'] < date) &
            (
                ((df['HomeTeam'] == home) & (df['AwayTeam'] == away)) |
                ((df['HomeTeam'] == away) & (df['AwayTeam'] == home))
            )
        ].tail(n_matches)
        
        if len(h2h_matches) == 0:
            continue
        
        # Contar resultados desde perspectiva del equipo HOME actual
        home_wins = 0
        draws = 0
        away_wins = 0
        home_goals = []
        away_goals = []
        
        for _, h2h in h2h_matches.iterrows():
            if h2h['HomeTeam'] == home:
                # Mismo orden: Home actual era local en H2H
                if h2h['FTHG'] > h2h['FTAG']:
                    home_wins += 1
                elif h2h['FTHG'] == h2h['FTAG']:
                    draws += 1
                else:
                    away_wins += 1
                home_goals.append(h2h['FTHG'])
                away_goals.append(h2h['FTAG'])
            else:
                # Orden invertido: Home actual era visitante en H2H
                if h2h['FTAG'] > h2h['FTHG']:
                    home_wins += 1
                elif h2h['FTHG'] == h2h['FTAG']:
                    draws += 1
                else:
                    away_wins += 1
                home_goals.append(h2h['FTAG'])
                away_goals.append(h2h['FTHG'])
        
        # Calcular métricas
        total_h2h = len(h2h_matches)
        home_goals_avg = np.mean(home_goals) if home_goals else 0.0
        away_goals_avg = np.mean(away_goals) if away_goals else 0.0
        total_goals_avg = home_goals_avg + away_goals_avg
        home_win_rate = home_wins / total_h2h if total_h2h > 0 else 0.0
        
        # Dominancia: +1 = home domina, -1 = away domina, 0 = parejo
        home_dominance = (home_wins - away_wins) / total_h2h if total_h2h > 0 else 0.0
        
        # Actualizar DataFrame
        df.at[idx, 'H2H_home_wins'] = home_wins
        df.at[idx, 'H2H_draws'] = draws
        df.at[idx, 'H2H_away_wins'] = away_wins
        df.at[idx, 'H2H_home_goals_avg'] = home_goals_avg
        df.at[idx, 'H2H_away_goals_avg'] = away_goals_avg
        df.at[idx, 'H2H_total_goals_avg'] = total_goals_avg
        df.at[idx, 'H2H_home_win_rate'] = home_win_rate
        df.at[idx, 'H2H_home_dominance'] = home_dominance
        df.at[idx, 'H2H_matches_found'] = total_h2h
    
    print(f"✅ H2H Features añadidos: {len([c for c in h2h_cols.keys()])} columnas")
    print(f"   Partidos con H2H data: {(df['H2H_matches_found'] > 0).sum()} / {len(df)}")
    
    return df


def add_home_away_separated_form(df: pd.DataFrame, window: int = 5) -> pd.DataFrame:
    """
    Añade forma reciente SEPARADA por contexto (casa vs fuera).
    
    Esta es la diferencia clave:
    - "Últimos 5 partidos" mezcla casa y fuera (actual)
    - "Últimos 5 como LOCAL" solo cuenta partidos en casa
    - "Últimos 5 como VISITANTE" solo cuenta partidos fuera
    
    Muchos equipos tienen rendimientos MUY diferentes:
    - Man City: casi imbatible en Etihad, baja ligeramente fuera
    - Equipos modestos: fuertes en casa, débiles fuera
    
    Parameters:
    -----------
    df : pd.DataFrame
        Dataset ordenado por fecha
    window : int
        Ventana de partidos (default: 5)
    
    Returns:
    --------
    df : pd.DataFrame
        Dataset con columnas separadas por contexto
    
    Columnas añadidas:
    ------------------
    Home (como local):
    - Home_as_home_GF_roll{window}: Goles a favor como local
    - Home_as_home_GA_roll{window}: Goles en contra como local
    - Home_as_home_GD_roll{window}: Goal diff como local
    - Home_as_home_points_roll{window}: Puntos ganados como local
    - Home_as_home_win_rate_roll{window}: % victorias como local
    
    Away (como visitante):
    - Away_as_away_GF_roll{window}: Goles a favor como visitante
    - Away_as_away_GA_roll{window}: Goles en contra como visitante
    - Away_as_away_GD_roll{window}: Goal diff como visitante
    - Away_as_away_points_roll{window}: Puntos ganados como visitante
    - Away_as_away_win_rate_roll{window}: % victorias como visitante
    """
    df = df.sort_values('Date').copy()
    
    # ============================================================
    # HOME TEAM - Rendimiento como LOCAL (solo partidos en casa)
    # ============================================================
    home_groups = df.groupby('HomeTeam')
    
    # Goles como local
    df['Home_as_home_GF_roll' + str(window)] = home_groups['FTHG'].rolling(window, min_periods=1).sum().reset_index(level=0, drop=True)
    df['Home_as_home_GA_roll' + str(window)] = home_groups['FTAG'].rolling(window, min_periods=1).sum().reset_index(level=0, drop=True)
    df['Home_as_home_GD_roll' + str(window)] = df[f'Home_as_home_GF_roll{window}'] - df[f'Home_as_home_GA_roll{window}']
    
    # Puntos como local
    def home_points(row):
        if row['FTHG'] > row['FTAG']:
            return 3
        elif row['FTHG'] == row['FTAG']:
            return 1
        return 0
    
    df['_home_points'] = df.apply(home_points, axis=1)
    df['Home_as_home_points_roll' + str(window)] = home_groups['_home_points'].rolling(window, min_periods=1).sum().reset_index(level=0, drop=True)
    
    # Win rate como local
    df['_home_win'] = (df['FTHG'] > df['FTAG']).astype(int)
    df['Home_as_home_win_rate_roll' + str(window)] = home_groups['_home_win'].rolling(window, min_periods=1).mean().reset_index(level=0, drop=True)
    
    # ============================================================
    # AWAY TEAM - Rendimiento como VISITANTE (solo partidos fuera)
    # ============================================================
    away_groups = df.groupby('AwayTeam')
    
    # Goles como visitante
    df['Away_as_away_GF_roll' + str(window)] = away_groups['FTAG'].rolling(window, min_periods=1).sum().reset_index(level=0, drop=True)
    df['Away_as_away_GA_roll' + str(window)] = away_groups['FTHG'].rolling(window, min_periods=1).sum().reset_index(level=0, drop=True)
    df['Away_as_away_GD_roll' + str(window)] = df[f'Away_as_away_GF_roll{window}'] - df[f'Away_as_away_GA_roll{window}']
    
    # Puntos como visitante
    def away_points(row):
        if row['FTAG'] > row['FTHG']:
            return 3
        elif row['FTAG'] == row['FTHG']:
            return 1
        return 0
    
    df['_away_points'] = df.apply(away_points, axis=1)
    df['Away_as_away_points_roll' + str(window)] = away_groups['_away_points'].rolling(window, min_periods=1).sum().reset_index(level=0, drop=True)
    
    # Win rate como visitante
    df['_away_win'] = (df['FTAG'] > df['FTHG']).astype(int)
    df['Away_as_away_win_rate_roll' + str(window)] = away_groups['_away_win'].rolling(window, min_periods=1).mean().reset_index(level=0, drop=True)
    
    # Limpiar columnas temporales
    df = df.drop(columns=['_home_points', '_home_win', '_away_points', '_away_win'])
    
    print(f"✅ Home/Away Separated Form añadido: ventana {window} partidos")
    print(f"   10 columnas nuevas (5 home context + 5 away context)")
    
    return df


def add_multi_window_form(df: pd.DataFrame, windows: list = [5, 10, 15]) -> pd.DataFrame:
    """
    Añade forma en múltiples ventanas temporales.
    
    Los profesionales cruzan:
    - Forma inmediata (5 partidos): momentum actual
    - Forma media (10 partidos): tendencia consolidada
    - Forma larga (15-20 partidos): rendimiento de temporada
    
    Ejemplo:
    - Arsenal: 7W en últimos 8 = forma inmediata excelente
    - Arsenal: 12W en últimos 15 = forma media buena
    - Arsenal: 18W en últimos 25 = forma de temporada sólida
    
    Parameters:
    -----------
    df : pd.DataFrame
        Dataset ordenado por fecha
    windows : list
        Lista de ventanas a calcular (default: [5, 10, 15])
    
    Returns:
    --------
    df : pd.DataFrame
        Dataset con columnas para cada ventana
    
    Columnas añadidas (por ventana):
    ---------------------------------
    - Home_GF_roll{w}, Home_GA_roll{w}, Home_GD_roll{w}
    - Away_GF_roll{w}, Away_GA_roll{w}, Away_GD_roll{w}
    - Home_points_roll{w}, Away_points_roll{w}
    - Home_win_rate_roll{w}, Away_win_rate_roll{w}
    """
    from src.features.rolling import add_form
    
    df = df.sort_values('Date').copy()
    
    for window in windows:
        print(f"   Procesando ventana {window}...")
        
        # Usar función existente para goles
        df = add_form(df, window=window)
        
        # Añadir puntos y win rate
        def home_points(row):
            if row['FTHG'] > row['FTAG']: return 3
            elif row['FTHG'] == row['FTAG']: return 1
            return 0
        
        def away_points(row):
            if row['FTAG'] > row['FTHG']: return 3
            elif row['FTAG'] == row['FTHG']: return 1
            return 0
        
        df['_hp'] = df.apply(home_points, axis=1)
        df['_ap'] = df.apply(away_points, axis=1)
        df['_hw'] = (df['FTHG'] > df['FTAG']).astype(int)
        df['_aw'] = (df['FTAG'] > df['FTHG']).astype(int)
        
        home_groups = df.groupby('HomeTeam')
        away_groups = df.groupby('AwayTeam')
        
        df[f'Home_points_roll{window}'] = home_groups['_hp'].rolling(window, min_periods=1).sum().reset_index(level=0, drop=True)
        df[f'Away_points_roll{window}'] = away_groups['_ap'].rolling(window, min_periods=1).sum().reset_index(level=0, drop=True)
        df[f'Home_win_rate_roll{window}'] = home_groups['_hw'].rolling(window, min_periods=1).mean().reset_index(level=0, drop=True)
        df[f'Away_win_rate_roll{window}'] = away_groups['_aw'].rolling(window, min_periods=1).mean().reset_index(level=0, drop=True)
        
        df = df.drop(columns=['_hp', '_ap', '_hw', '_aw'])
    
    print(f"✅ Multi-Window Form añadido: {len(windows)} ventanas {windows}")
    
    return df


def add_motivation_context(df: pd.DataFrame) -> pd.DataFrame:
    """
    Añade contexto de motivación y situación en tabla.
    
    La motivación es CRÍTICA:
    - Equipo peleando título: máxima motivación
    - Equipo peleando Europa: alta motivación
    - Equipo evitando descenso: motivación extrema
    - Equipo mid-table sin objetivos: baja motivación
    
    NOTA: Requiere datos de standings (clasificación).
    Si no están disponibles, estima posición por puntos acumulados.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Dataset con partidos históricos
    
    Returns:
    --------
    df : pd.DataFrame
        Dataset con features de motivación
    
    Columnas añadidas:
    ------------------
    - Home_position_estimated: Posición estimada en tabla
    - Away_position_estimated: Posición estimada en tabla
    - Home_motivation_score: Score 0-10 de motivación
    - Away_motivation_score: Score 0-10 de motivación
    - Home_on_winning_streak: Racha de victorias (bool)
    - Away_on_winning_streak: Racha de victorias (bool)
    - Home_streak_length: Longitud de racha actual
    - Away_streak_length: Longitud de racha actual
    """
    df = df.sort_values('Date').copy()
    
    # Calcular posición estimada por puntos rolling de temporada
    # (Aproximación: asumimos 38 jornadas, usamos rolling 20 como "media temporada")
    
    df['Home_position_estimated'] = 10  # Default mid-table
    df['Away_position_estimated'] = 10
    df['Home_motivation_score'] = 5.0
    df['Away_motivation_score'] = 5.0
    df['Home_on_winning_streak'] = False
    df['Away_on_winning_streak'] = False
    df['Home_streak_length'] = 0
    df['Away_streak_length'] = 0
    
    # Por ahora, solo calculamos streaks (rachas)
    # Para posiciones reales, necesitaríamos standings de API
    
    for team_col in ['HomeTeam', 'AwayTeam']:
        is_home = (team_col == 'HomeTeam')
        prefix = 'Home' if is_home else 'Away'
        gf_col = 'FTHG' if is_home else 'FTAG'
        ga_col = 'FTAG' if is_home else 'FTHG'
        
        for team in df[team_col].unique():
            team_matches = df[df[team_col] == team].copy()
            
            streak = 0
            streak_type = None  # 'W', 'D', 'L'
            
            for idx in team_matches.index:
                match = df.loc[idx]
                
                # Resultado del partido
                if match[gf_col] > match[ga_col]:
                    result = 'W'
                elif match[gf_col] == match[ga_col]:
                    result = 'D'
                else:
                    result = 'L'
                
                # Actualizar racha
                if result == 'W':
                    if streak_type == 'W':
                        streak += 1
                    else:
                        streak = 1
                        streak_type = 'W'
                else:
                    streak = 0
                    streak_type = result
                
                # Guardar racha
                df.at[idx, f'{prefix}_streak_length'] = streak if streak_type == 'W' else 0
                df.at[idx, f'{prefix}_on_winning_streak'] = (streak >= 3)  # 3+ victorias seguidas
    
    print(f"✅ Motivation Context añadido: streaks y rachas calculadas")
    print(f"   NOTA: Para motivación real, integrar standings de API")
    
    return df


def add_xg_rolling_features(df: pd.DataFrame, window: int = 5) -> pd.DataFrame:
    """
    Añade features rolling de Expected Goals (xG).
    
    El xG es el estadístico MÁS importante después del resultado:
    - xG alto + pocos goles = mala suerte, revertirá
    - xG bajo + muchos goles = buena suerte, no es sostenible
    
    Parameters:
    -----------
    df : pd.DataFrame
        Dataset con columnas xG_home, xG_away
    window : int
        Ventana para rolling (default: 5)
    
    Returns:
    --------
    df : pd.DataFrame
        Dataset con xG rolling features
    
    Columnas añadidas:
    ------------------
    - Home_xG_roll{window}: xG promedio del local
    - Away_xG_roll{window}: xG promedio del visitante
    - Home_xG_overperformance_roll{window}: Goles - xG (suerte)
    - Away_xG_overperformance_roll{window}: Goles - xG (suerte)
    - Home_xG_consistency_roll{window}: Desviación estándar (consistencia)
    - Away_xG_consistency_roll{window}: Desviación estándar (consistencia)
    """
    if 'xG_home' not in df.columns or 'xG_away' not in df.columns:
        print(f"⚠️  xG columns not found, skipping xG rolling features")
        return df
    
    df = df.sort_values('Date').copy()
    
    # xG rolling promedio
    home_groups = df.groupby('HomeTeam')
    away_groups = df.groupby('AwayTeam')
    
    df[f'Home_xG_roll{window}'] = home_groups['xG_home'].rolling(window, min_periods=1).mean().reset_index(level=0, drop=True)
    df[f'Away_xG_roll{window}'] = away_groups['xG_away'].rolling(window, min_periods=1).mean().reset_index(level=0, drop=True)
    
    # xG overperformance (suerte/finishing)
    df['_home_xG_over'] = df['FTHG'] - df['xG_home'].fillna(df['FTHG'])
    df['_away_xG_over'] = df['FTAG'] - df['xG_away'].fillna(df['FTAG'])
    
    df[f'Home_xG_overperformance_roll{window}'] = home_groups['_home_xG_over'].rolling(window, min_periods=1).mean().reset_index(level=0, drop=True)
    df[f'Away_xG_overperformance_roll{window}'] = away_groups['_away_xG_over'].rolling(window, min_periods=1).mean().reset_index(level=0, drop=True)
    
    # xG consistency
    df[f'Home_xG_consistency_roll{window}'] = home_groups['xG_home'].rolling(window, min_periods=2).std().reset_index(level=0, drop=True).fillna(0)
    df[f'Away_xG_consistency_roll{window}'] = away_groups['xG_away'].rolling(window, min_periods=2).std().reset_index(level=0, drop=True).fillna(0)
    
    df = df.drop(columns=['_home_xG_over', '_away_xG_over'])
    
    print(f"✅ xG Rolling Features añadidos: ventana {window}")
    
    return df


def add_all_professional_features(df: pd.DataFrame, 
                                  h2h_matches: int = 5,
                                  form_window: int = 5,
                                  multi_windows: list = [5, 10, 15],
                                  enable_xg: bool = True) -> pd.DataFrame:
    """
    Añade TODAS las features profesionales de una vez.
    
    Esta es la función maestra que implementa el enfoque multicapa
    usado por analistas y casas de apuestas profesionales.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Dataset base
    h2h_matches : int
        Enfrentamientos directos a considerar (default: 5)
    form_window : int
        Ventana para forma separada casa/fuera (default: 5)
    multi_windows : list
        Ventanas para análisis temporal múltiple (default: [5,10,15])
    enable_xg : bool
        Activar features de xG (default: True)
    
    Returns:
    --------
    df : pd.DataFrame
        Dataset con TODAS las features profesionales
    
    Proceso:
    --------
    1. ✅ Head-to-Head (H2H)
    2. ✅ Rendimiento Casa/Fuera separado
    3. ✅ Múltiples ventanas temporales
    4. ✅ Contexto de motivación
    5. ✅ xG rolling (si disponible)
    """
    print("\n" + "=" * 70)
    print("  AÑADIENDO FEATURES PROFESIONALES")
    print("=" * 70)
    print(f"\nDataset inicial: {len(df)} partidos, {len(df.columns)} columnas\n")
    
    # 1. Head-to-Head
    print("[1/5] Head-to-Head (H2H)...")
    df = add_head_to_head_features(df, n_matches=h2h_matches)
    
    # 2. Rendimiento Casa/Fuera separado
    print(f"\n[2/5] Rendimiento Casa/Fuera separado...")
    df = add_home_away_separated_form(df, window=form_window)
    
    # 3. Múltiples ventanas temporales
    print(f"\n[3/5] Múltiples ventanas temporales...")
    df = add_multi_window_form(df, windows=multi_windows)
    
    # 4. Motivación y contexto
    print(f"\n[4/5] Motivación y contexto...")
    df = add_motivation_context(df)
    
    # 5. xG rolling (si está disponible)
    if enable_xg:
        print(f"\n[5/5] xG Rolling features...")
        df = add_xg_rolling_features(df, window=form_window)
    else:
        print(f"\n[5/5] xG features DESACTIVADO")
    
    print("\n" + "=" * 70)
    print(f"  COMPLETADO")
    print("=" * 70)
    print(f"\nDataset final: {len(df)} partidos, {len(df.columns)} columnas")
    print(f"Columnas añadidas: {len(df.columns) - 20} (aprox.)\n")
    
    return df


if __name__ == "__main__":
    print("""
    MÓDULO DE FEATURES PROFESIONALES
    =================================
    
    Uso:
    
    from src.features.professional_features import add_all_professional_features
    
    df = pd.read_parquet("data/processed/matches.parquet")
    df = add_all_professional_features(df)
    
    Features implementados:
    ✅ Head-to-Head (H2H) - Últimos 5 enfrentamientos
    ✅ Rendimiento Casa/Fuera SEPARADO
    ✅ Múltiples Ventanas (5, 10, 15 partidos)
    ✅ Motivación y Streaks
    ✅ xG Rolling (si disponible)
    
    Basado en mejores prácticas de casas de apuestas profesionales.
    """)

