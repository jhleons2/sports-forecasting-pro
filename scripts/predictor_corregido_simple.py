"""
PREDICTOR CORREGIDO - Dixon-Coles + Reglas Dinámicas
====================================================

Usa Dixon-Coles (confiable) sin el XGBoost corrupto.
Calcula todas las predicciones basándose en modelo Poisson + tus 5 reglas.
"""

import sys
from pathlib import Path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict
from src.models.poisson_dc import DixonColes
from src.features.reglas_dinamicas import calcular_reglas_dinamicas
from src.features.ratings import add_elo

PROC = Path("data/processed")

class PredictorCorregidoSimple:
    """
    Predictor que usa Dixon-Coles + Reglas Dinámicas
    SIN el XGBoost corrupto que predice 68% empate
    """
    
    def __init__(self):
        self.dc_model = None
        self.df_historico = None
        self.df_con_elo = None
        self.mapeo_nombres = None
        self.load_and_train()
        
    def load_and_train(self):
        """Cargar datos y entrenar Dixon-Coles"""
        print("\n" + "=" * 70)
        print("  PREDICTOR CORREGIDO (Dixon-Coles + Reglas)")
        print("=" * 70)
        print("\nUsando Dixon-Coles (sin XGBoost corrupto)\n")
        
        # 1. Cargar datos
        print("1. Cargando datos...")
        self.df_historico = pd.read_parquet(PROC / "matches.parquet")
        print(f"   {len(self.df_historico)} partidos")
        
        # 2. ELO
        print("\n2. Calculando ELO...")
        self.df_con_elo = add_elo(self.df_historico)
        print("   OK")
        
        # 3. Dixon-Coles
        print("\n3. Entrenando Dixon-Coles...")
        self.dc_model = DixonColes().fit(self.df_con_elo)
        print("   OK")
        
        # 4. Sistema de mapeo dinámico
        print("\n4. Inicializando mapeo dinámico...")
        try:
            from src.utils.mapeador_dinamico import mapeador_dinamico
            self.mapeador_dinamico = mapeador_dinamico
            print(f"   OK: Sistema dinámico cargado ({len(self.mapeador_dinamico.nombres_historicos)} equipos históricos)")
        except Exception as e:
            print(f"   ADVERTENCIA: Error cargando mapeador dinámico: {e}")
            # Fallback a mapeo básico
            self.mapeo_nombres = {
                'Brentford FC': 'Brentford',
                'Liverpool FC': 'Liverpool',
                'Chelsea FC': 'Chelsea',
                'Sunderland AFC': 'Sunderland',
                'Man United FC': 'Man United',
                'Manchester United FC': 'Man United',
                'Man City FC': 'Man City',
                'Manchester City FC': 'Man City',
                'Arsenal FC': 'Arsenal',
                'Tottenham Hotspur FC': 'Tottenham',
                'West Ham United FC': 'West Ham',
                'Newcastle United FC': 'Newcastle',
                'Brighton & Hove Albion FC': 'Brighton',
                'Crystal Palace FC': 'Crystal Palace',
                'Fulham FC': 'Fulham',
                'Leeds United FC': 'Leeds',
                'Aston Villa FC': 'Aston Villa',
                'Everton FC': 'Everton',
                'Leicester City FC': 'Leicester',
                'Wolverhampton Wanderers FC': 'Wolves',
                'AFC Bournemouth': 'Bournemouth',
                'Nottingham Forest FC': "Nott'm Forest"
            }
            self.mapeador_dinamico = None
            print(f"   Mapeo basico: {len(self.mapeo_nombres)} equipos")
        
        print("\n" + "=" * 70)
        print("  PREDICTOR LISTO")
        print("=" * 70)
    
    def mapear_nombres(self, equipo_home: str, equipo_away: str):
        """Mapear nombres usando sistema dinámico o fallback básico"""
        if self.mapeador_dinamico:
            # Usar sistema dinámico
            home_mapeado, away_mapeado = self.mapeador_dinamico.mapear_equipos_partido(equipo_home, equipo_away)
            return home_mapeado, away_mapeado
        else:
            # Fallback a mapeo básico
            home_mapeado = self.mapeo_nombres.get(equipo_home, equipo_home)
            away_mapeado = self.mapeo_nombres.get(equipo_away, equipo_away)
            return home_mapeado, away_mapeado
    
    def predict_con_reglas_dinamicas(self, equipo_home: str, equipo_away: str, liga: str) -> Dict:
        """Predecir usando Dixon-Coles + reglas dinámicas"""
        print("\n" + "=" * 70)
        print("  PREDICCION CORREGIDA")
        print("=" * 70)
        
        # Mapear nombres
        home_mapeado, away_mapeado = self.mapear_nombres(equipo_home, equipo_away)
        print(f"\n{equipo_home} ({home_mapeado}) vs {equipo_away} ({away_mapeado})")
        
        # Calcular reglas dinámicas
        reglas = calcular_reglas_dinamicas(
            self.df_historico,
            home_mapeado,
            away_mapeado,
            liga
        )
        
        # Obtener ELO actual
        elo_home = self._get_current_elo(home_mapeado)
        elo_away = self._get_current_elo(away_mapeado)
        
        # Crear row para Dixon-Coles
        row = pd.Series({'EloHome': elo_home, 'EloAway': elo_away})
        
        # Calcular intensidades (xG)
        lam, mu = self._intensity(row)
        home_goals = lam
        away_goals = mu
        
        print(f"\nxG predichos:")
        print(f"   {equipo_home}: {home_goals:.2f}")
        print(f"   {equipo_away}: {away_goals:.2f}")
        
        # Calcular 1X2 desde Dixon-Coles
        matrix = self.dc_model.score_matrix(row, max_goals=10)
        pH = np.tril(matrix, -1).sum()
        pD = np.trace(matrix)
        pA = np.triu(matrix, 1).sum()
        
        probs_1x2 = {'home': pH, 'draw': pD, 'away': pA}
        
        # Ajustar con reglas
        probs_ajustadas = self._ajustar_con_reglas(probs_1x2, reglas, home_goals, away_goals)
        
        print(f"\nProbabilidades 1X2:")
        print(f"   Local: {probs_ajustadas['home']*100:.1f}%")
        print(f"   Empate: {probs_ajustadas['draw']*100:.1f}%")
        print(f"   Visitante: {probs_ajustadas['away']*100:.1f}%")
        
        # Calcular Over/Under
        ou_result = self.dc_model.prob_over_under(row, line=2.5)
        ou_probs = {
            'over_2_5': ou_result['pOver'],
            'under_2_5': ou_result['pUnder']
        }
        
        # Predecir eventos
        events = self._predict_events(home_goals, away_goals, elo_home, elo_away)
        
        return {
            '1x2': probs_ajustadas,
            'xg': {
                'home': float(home_goals),
                'away': float(away_goals),
                'total': float(home_goals + away_goals)
            },
            'ou': {
                'over_2_5': float(ou_probs['over_2_5']),
                'under_2_5': float(ou_probs['under_2_5'])
            },
            'events': events,
            'reglas': reglas,
            'elo_home': float(elo_home),
            'elo_away': float(elo_away)
        }
    
    def _intensity(self, row):
        """Calcular lambdas (intensidades de goles)"""
        p = self.dc_model.params_
        elo_diff = (row['EloHome'] - row['EloAway']) / 400.0
        lam = np.exp(p[0] + p[1]*elo_diff + p[4])
        mu = np.exp(p[2] - p[3]*elo_diff)
        return lam, mu
    
    def _ajustar_con_reglas(self, probs_base: Dict, reglas: Dict, xg_home: float, xg_away: float) -> Dict:
        """Ajustar probabilidades con reglas dinámicas"""
        home_prob = probs_base['home']
        draw_prob = probs_base['draw']
        away_prob = probs_base['away']
        
        # Factor de forma (con manejo de datos faltantes)
        home_form = reglas['ultimos_8_total']['home'].get('efectividad', 50.0) / 100.0
        away_form = reglas['ultimos_8_total']['away'].get('efectividad', 50.0) / 100.0
        
        # Factor H2H
        h2h_home_wins = reglas['ultimos_5_h2h']['home_wins']
        h2h_away_wins = reglas['ultimos_5_h2h']['away_wins']
        h2h_total = reglas['ultimos_5_h2h']['partidos']
        
        # Ajuste por forma
        form_diff = home_form - away_form
        
        if form_diff > 0.2:
            home_prob += 0.05
            away_prob -= 0.03
            draw_prob -= 0.02
        elif form_diff < -0.2:
            away_prob += 0.05
            home_prob -= 0.03
            draw_prob -= 0.02
        
        # Ajuste por H2H
        if h2h_total >= 2:
            if h2h_home_wins > h2h_away_wins:
                home_prob += 0.03
                away_prob -= 0.02
                draw_prob -= 0.01
            elif h2h_away_wins > h2h_home_wins:
                away_prob += 0.03
                home_prob -= 0.02
                draw_prob -= 0.01
        
        # Normalizar
        total = home_prob + draw_prob + away_prob
        
        return {
            'home': home_prob / total,
            'draw': draw_prob / total,
            'away': away_prob / total
        }
    
    def _get_current_elo(self, team: str) -> float:
        """Obtener ELO actual del equipo"""
        team_matches = self.df_con_elo[
            (self.df_con_elo['HomeTeam'] == team) | (self.df_con_elo['AwayTeam'] == team)
        ].sort_values('Date', ascending=False)
        
        if len(team_matches) == 0:
            return 1500.0
        
        last_match = team_matches.iloc[0]
        if last_match['HomeTeam'] == team:
            return last_match['EloHome']
        else:
            return last_match['EloAway']
    
    def _predict_events(self, xg_home: float, xg_away: float, elo_home: float, elo_away: float) -> Dict:
        """Predecir eventos (corners, cards, shots)"""
        total_xg = xg_home + xg_away
        
        # Corners (proporcional a xG)
        corners_home = max(3, min(8, int(xg_home * 4.5)))
        corners_away = max(3, min(8, int(xg_away * 4.5)))
        corners_total = corners_home + corners_away
        
        # Cards
        cards_yellow = max(2, min(6, int(total_xg * 1.5) + 2))
        cards_red = 0
        cards_total = cards_yellow + cards_red
        
        # Shots
        shots_home = max(5, min(15, int(xg_home * 6)))
        shots_away = max(5, min(15, int(xg_away * 6)))
        shots_total = shots_home + shots_away
        shots_on_target_home = max(2, int(shots_home * 0.35))
        shots_on_target_away = max(2, int(shots_away * 0.35))
        
        return {
            'corners': {
                'home': corners_home,
                'away': corners_away,
                'total': corners_total,
                'over_9_5': 1.0 if corners_total > 9.5 else 0.0,
                'over_10_5': 1.0 if corners_total > 10.5 else 0.0,
                'over_11_5': 1.0 if corners_total > 11.5 else 0.0
            },
            'cards': {
                'yellow': cards_yellow,
                'red': cards_red,
                'total': cards_total,
                'over_3_5': 1.0 if cards_total > 3.5 else 0.0,
                'over_4_5': 1.0 if cards_total > 4.5 else 0.0
            },
            'shots': {
                'home': shots_home,
                'away': shots_away,
                'total': shots_total,
                'on_target_home': shots_on_target_home,
                'on_target_away': shots_on_target_away
            }
        }

