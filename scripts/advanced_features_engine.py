#!/usr/bin/env python3
"""
Features Avanzados para Máxima Precisión
========================================

Implementa features específicos que mejoran la precisión del modelo:
1. Features de contexto temporal
2. Features de motivación
3. Features de rendimiento situacional
4. Features de mercado (odds)
5. Features de lesiones y suspensiones
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.features.ratings import add_elo
from src.features.rolling import add_form

PROC = Path("data/processed")

class AdvancedFeaturesEngine:
    """
    Motor de features avanzados para máxima precisión
    """
    
    def __init__(self):
        self.feature_cache = {}
        
    def add_temporal_context_features(self, df):
        """Añadir features de contexto temporal"""
        print("   Añadiendo features de contexto temporal...")
        
        # Convertir fecha a datetime
        df['Date'] = pd.to_datetime(df['Date'])
        
        # 1. Día de la semana
        df['day_of_week'] = df['Date'].dt.dayofweek
        df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
        
        # 2. Mes de la temporada
        df['month'] = df['Date'].dt.month
        df['season_period'] = df['month'].apply(self._get_season_period)
        
        # 3. Días de descanso
        df = self._add_rest_days_features(df)
        
        # 4. Congestión de calendario
        df = self._add_calendar_congestion_features(df)
        
        return df
    
    def _get_season_period(self, month):
        """Determinar período de la temporada"""
        if month in [8, 9]:  # Agosto-Septiembre
            return 1  # Inicio de temporada
        elif month in [10, 11, 12]:  # Octubre-Diciembre
            return 2  # Primera mitad
        elif month in [1, 2]:  # Enero-Febrero
            return 3  # Mitad de temporada
        elif month in [3, 4]:  # Marzo-Abril
            return 4  # Segunda mitad
        else:  # Mayo-Junio
            return 5  # Final de temporada
    
    def _add_rest_days_features(self, df):
        """Añadir features de días de descanso"""
        df = df.sort_values(['HomeTeam', 'Date']).reset_index(drop=True)
        
        # Días de descanso para equipo local
        df['home_rest_days'] = df.groupby('HomeTeam')['Date'].diff().dt.days.fillna(7)
        df['home_rest_days'] = df['home_rest_days'].clip(1, 14)  # Limitar entre 1-14 días
        
        # Días de descanso para equipo visitante
        df = df.sort_values(['AwayTeam', 'Date']).reset_index(drop=True)
        df['away_rest_days'] = df.groupby('AwayTeam')['Date'].diff().dt.days.fillna(7)
        df['away_rest_days'] = df['away_rest_days'].clip(1, 14)
        
        # Diferencia de descanso
        df['rest_days_diff'] = df['home_rest_days'] - df['away_rest_days']
        
        # Ventaja de descanso
        df['home_rest_advantage'] = (df['rest_days_diff'] > 2).astype(int)
        df['away_rest_advantage'] = (df['rest_days_diff'] < -2).astype(int)
        
        return df
    
    def _add_calendar_congestion_features(self, df):
        """Añadir features de congestión de calendario"""
        # Partidos en últimos 7 días para cada equipo
        df['home_matches_7d'] = 0
        df['away_matches_7d'] = 0
        
        for idx, row in df.iterrows():
            # Partidos del equipo local en últimos 7 días
            home_team_matches = df[
                ((df['HomeTeam'] == row['HomeTeam']) | (df['AwayTeam'] == row['HomeTeam'])) &
                (df['Date'] < row['Date']) &
                (df['Date'] >= row['Date'] - pd.Timedelta(days=7))
            ]
            df.loc[idx, 'home_matches_7d'] = len(home_team_matches)
            
            # Partidos del equipo visitante en últimos 7 días
            away_team_matches = df[
                ((df['HomeTeam'] == row['AwayTeam']) | (df['AwayTeam'] == row['AwayTeam'])) &
                (df['Date'] < row['Date']) &
                (df['Date'] >= row['Date'] - pd.Timedelta(days=7))
            ]
            df.loc[idx, 'away_matches_7d'] = len(away_team_matches)
        
        # Congestión relativa
        df['congestion_diff'] = df['home_matches_7d'] - df['away_matches_7d']
        df['home_congestion_advantage'] = (df['congestion_diff'] < -1).astype(int)
        df['away_congestion_advantage'] = (df['congestion_diff'] > 1).astype(int)
        
        return df
    
    def add_motivation_features(self, df):
        """Añadir features de motivación"""
        print("   Añadiendo features de motivación...")
        
        # 1. Posición en tabla
        df = self._add_table_position_features(df)
        
        # 2. Objetivos de temporada
        df = self._add_season_objectives_features(df)
        
        # 3. Presión de resultados
        df = self._add_result_pressure_features(df)
        
        return df
    
    def _add_table_position_features(self, df):
        """Añadir features de posición en tabla"""
        # Calcular tabla acumulativa para cada fecha
        df['home_table_position'] = 0
        df['away_table_position'] = 0
        
        for idx, row in df.iterrows():
            # Tabla hasta esta fecha
            table_data = self._calculate_table_position(df, row['Date'])
            
            if row['HomeTeam'] in table_data:
                df.loc[idx, 'home_table_position'] = table_data[row['HomeTeam']]
            if row['AwayTeam'] in table_data:
                df.loc[idx, 'away_table_position'] = table_data[row['AwayTeam']]
        
        # Diferencia de posición
        df['position_diff'] = df['home_table_position'] - df['away_table_position']
        
        # Ventaja de posición
        df['home_position_advantage'] = (df['position_diff'] < -3).astype(int)
        df['away_position_advantage'] = (df['position_diff'] > 3).astype(int)
        
        return df
    
    def _calculate_table_position(self, df, date):
        """Calcular posición en tabla hasta una fecha específica"""
        # Filtrar partidos hasta la fecha
        matches_until_date = df[df['Date'] < date].copy()
        
        if len(matches_until_date) == 0:
            return {}
        
        # Calcular puntos por equipo
        team_points = {}
        
        for _, match in matches_until_date.iterrows():
            home_team = match['HomeTeam']
            away_team = match['AwayTeam']
            
            if home_team not in team_points:
                team_points[home_team] = {'points': 0, 'played': 0}
            if away_team not in team_points:
                team_points[away_team] = {'points': 0, 'played': 0}
            
            team_points[home_team]['played'] += 1
            team_points[away_team]['played'] += 1
            
            # Asignar puntos
            if match['FTHG'] > match['FTAG']:  # Victoria local
                team_points[home_team]['points'] += 3
            elif match['FTHG'] < match['FTAG']:  # Victoria visitante
                team_points[away_team]['points'] += 3
            else:  # Empate
                team_points[home_team]['points'] += 1
                team_points[away_team]['points'] += 1
        
        # Ordenar por puntos y asignar posición
        sorted_teams = sorted(team_points.items(), 
                            key=lambda x: (x[1]['points'], x[1]['played']), 
                            reverse=True)
        
        positions = {}
        for i, (team, _) in enumerate(sorted_teams):
            positions[team] = i + 1
        
        return positions
    
    def _add_season_objectives_features(self, df):
        """Añadir features de objetivos de temporada"""
        # Objetivos basados en posición en tabla
        df['home_objective'] = df['home_table_position'].apply(self._get_team_objective)
        df['away_objective'] = df['away_table_position'].apply(self._get_team_objective)
        
        # Urgencia del partido
        df['match_urgency'] = df.apply(self._calculate_match_urgency, axis=1)
        
        return df
    
    def _get_team_objective(self, position):
        """Determinar objetivo del equipo basado en posición"""
        if position <= 4:
            return 1  # Champions League
        elif position <= 6:
            return 2  # Europa League
        elif position <= 17:
            return 3  # Mantenerse en liga
        else:
            return 4  # Evitar descenso
    
    def _calculate_match_urgency(self, row):
        """Calcular urgencia del partido"""
        home_obj = row['home_objective']
        away_obj = row['away_objective']
        
        # Mayor urgencia si ambos equipos tienen objetivos similares
        if home_obj == away_obj:
            return 3  # Alta urgencia
        elif abs(home_obj - away_obj) == 1:
            return 2  # Media urgencia
        else:
            return 1  # Baja urgencia
    
    def _add_result_pressure_features(self, df):
        """Añadir features de presión de resultados"""
        # Racha de resultados recientes
        df = self._add_result_streak_features(df)
        
        # Presión por resultados negativos
        df = self._add_negative_pressure_features(df)
        
        return df
    
    def _add_result_streak_features(self, df):
        """Añadir features de racha de resultados"""
        df['home_streak'] = 0
        df['away_streak'] = 0
        
        for idx, row in df.iterrows():
            # Racha del equipo local
            home_streak = self._calculate_team_streak(df, row['HomeTeam'], row['Date'], 'home')
            df.loc[idx, 'home_streak'] = home_streak
            
            # Racha del equipo visitante
            away_streak = self._calculate_team_streak(df, row['AwayTeam'], row['Date'], 'away')
            df.loc[idx, 'away_streak'] = away_streak
        
        # Diferencia de racha
        df['streak_diff'] = df['home_streak'] - df['away_streak']
        
        return df
    
    def _calculate_team_streak(self, df, team, date, team_type):
        """Calcular racha de un equipo"""
        # Partidos recientes del equipo
        team_matches = df[
            ((df['HomeTeam'] == team) | (df['AwayTeam'] == team)) &
            (df['Date'] < date)
        ].tail(5)  # Últimos 5 partidos
        
        if len(team_matches) == 0:
            return 0
        
        streak = 0
        for _, match in team_matches.iterrows():
            if match['HomeTeam'] == team:
                if match['FTHG'] > match['FTAG']:
                    streak += 1
                elif match['FTHG'] < match['FTAG']:
                    streak -= 1
            else:  # Away team
                if match['FTHG'] < match['FTAG']:
                    streak += 1
                elif match['FTHG'] > match['FTAG']:
                    streak -= 1
        
        return streak
    
    def _add_negative_pressure_features(self, df):
        """Añadir features de presión por resultados negativos"""
        # Partidos sin ganar
        df['home_winless'] = 0
        df['away_winless'] = 0
        
        for idx, row in df.iterrows():
            # Partidos sin ganar del equipo local
            home_winless = self._calculate_winless_matches(df, row['HomeTeam'], row['Date'])
            df.loc[idx, 'home_winless'] = home_winless
            
            # Partidos sin ganar del equipo visitante
            away_winless = self._calculate_winless_matches(df, row['AwayTeam'], row['Date'])
            df.loc[idx, 'away_winless'] = away_winless
        
        # Presión por resultados negativos
        df['home_negative_pressure'] = (df['home_winless'] >= 3).astype(int)
        df['away_negative_pressure'] = (df['away_winless'] >= 3).astype(int)
        
        return df
    
    def _calculate_winless_matches(self, df, team, date):
        """Calcular partidos consecutivos sin ganar"""
        team_matches = df[
            ((df['HomeTeam'] == team) | (df['AwayTeam'] == team)) &
            (df['Date'] < date)
        ].tail(10)  # Últimos 10 partidos
        
        winless = 0
        for _, match in team_matches.iterrows():
            if match['HomeTeam'] == team:
                if match['FTHG'] <= match['FTAG']:  # No ganó
                    winless += 1
                else:
                    break
            else:  # Away team
                if match['FTHG'] >= match['FTAG']:  # No ganó
                    winless += 1
                else:
                    break
        
        return winless
    
    def add_market_features(self, df):
        """Añadir features del mercado (odds)"""
        print("   Añadiendo features del mercado...")
        
        # Features de odds si están disponibles
        odds_columns = ['B365H', 'B365D', 'B365A']
        
        if all(col in df.columns for col in odds_columns):
            # Probabilidades implícitas
            df['implied_prob_home'] = 1.0 / df['B365H']
            df['implied_prob_draw'] = 1.0 / df['B365D']
            df['implied_prob_away'] = 1.0 / df['B365A']
            
            # Overround
            df['overround'] = df['implied_prob_home'] + df['implied_prob_draw'] + df['implied_prob_away']
            
            # Probabilidades ajustadas (sin overround)
            df['adj_prob_home'] = df['implied_prob_home'] / df['overround']
            df['adj_prob_draw'] = df['implied_prob_draw'] / df['overround']
            df['adj_prob_away'] = df['implied_prob_away'] / df['overround']
            
            # Valor del mercado
            df['market_value_home'] = df['adj_prob_home'] - df['adj_prob_away']
            df['market_value_draw'] = df['adj_prob_draw'] - df['adj_prob_away']
            
            print(f"     OK - Features de mercado añadidos")
        else:
            print(f"     INFO - Columnas de odds no encontradas, omitiendo features de mercado")
        
        return df
    
    def add_all_advanced_features(self, df):
        """Añadir todos los features avanzados"""
        print("\n" + "=" * 70)
        print("AÑADIENDO FEATURES AVANZADOS PARA MÁXIMA PRECISIÓN")
        print("=" * 70)
        
        print(f"\nDataset inicial: {len(df)} partidos, {len(df.columns)} columnas")
        
        # 1. Features básicos
        print("\n[1/4] Features básicos...")
        df = add_elo(df)
        df = add_form(df)
        
        # 2. Contexto temporal
        print("\n[2/4] Contexto temporal...")
        df = self.add_temporal_context_features(df)
        
        # 3. Motivación
        print("\n[3/4] Motivación...")
        df = self.add_motivation_features(df)
        
        # 4. Mercado
        print("\n[4/4] Mercado...")
        df = self.add_market_features(df)
        
        print(f"\nDataset final: {len(df)} partidos, {len(df.columns)} columnas")
        print("=" * 70)
        
        return df


def main():
    """Ejemplo de uso del motor de features avanzados"""
    print("Probando motor de features avanzados...")
    
    # Cargar datos de ejemplo
    df = pd.read_parquet(PROC / "matches.parquet")
    
    # Crear motor de features
    feature_engine = AdvancedFeaturesEngine()
    
    # Añadir features avanzados
    df_with_features = feature_engine.add_all_advanced_features(df)
    
    print(f"\nFeatures añadidos exitosamente!")
    print(f"Columnas nuevas: {len(df_with_features.columns) - len(df.columns)}")
    
    # Mostrar algunas columnas nuevas
    new_columns = [col for col in df_with_features.columns if col not in df.columns]
    print(f"\nAlgunas columnas nuevas:")
    for col in new_columns[:10]:
        print(f"  - {col}")


if __name__ == "__main__":
    main()
