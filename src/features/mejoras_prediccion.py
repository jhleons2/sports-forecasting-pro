"""
Mejoras al Sistema de Predicción
Basado en análisis del partido Chelsea 1-2 Sunderland

Mejoras implementadas:
1. Ajuste temporal (probabilidades según minuto del partido)
2. Diferencial xG (modelado de eficiencia)
3. Ponderación según calidad del rival
"""

import numpy as np
from typing import Dict, Tuple


class MejoraTemporal:
    """Ajusta probabilidades según el contexto temporal del partido"""
    
    @staticmethod
    def ajustar_probabilidades_tiempo_real(
        match_minute: int,
        home_goals: int,
        away_goals: int,
        original_probs: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Ajusta probabilidades según minuto y marcador actual
        
        Args:
            match_minute: Minuto actual del partido
            home_goals: Goles del equipo local
            away_goals: Goles del equipo visitante
            original_probs: Probabilidades originales {'home': X, 'draw': Y, 'away': Z}
            
        Returns:
            Probabilidades ajustadas
        """
        # Si es antes del partido
        if match_minute == 0:
            return original_probs
        
        diff_goals = home_goals - away_goals
        
        # Últimos 10 minutos del partido
        if match_minute >= 80:
            if home_goals == away_goals:
                # Empate en tiempo final
                empate_prob = min(0.90, original_probs['draw'] * 2.5)
                home_prob = (1 - empate_prob) * 0.4
                away_prob = (1 - empate_prob) * 0.4
                
                return {
                    'home': round(home_prob, 3),
                    'draw': round(empate_prob, 3),
                    'away': round(away_prob, 3)
                }
            elif diff_goals == 1:
                # Diferencia de 1 gol
                lider_prob = min(0.75, original_probs['home' if diff_goals > 0 else 'away'] * 1.8)
                empate_prob = (1 - lider_prob) * 0.5
                
                if diff_goals > 0:
                    return {
                        'home': round(lider_prob, 3),
                        'draw': round(empate_prob, 3),
                        'away': round(1 - lider_prob - empate_prob, 3)
                    }
                else:
                    return {
                        'home': round(1 - lider_prob - empate_prob, 3),
                        'draw': round(empate_prob, 3),
                        'away': round(lider_prob, 3)
                    }
            elif abs(diff_goals) >= 2:
                # Diferencia de 2+ goles
                lider_prob = 0.92
                if diff_goals > 0:
                    return {
                        'home': round(lider_prob, 3),
                        'draw': round(0.04, 3),
                        'away': round(0.04, 3)
                    }
                else:
                    return {
                        'home': round(0.04, 3),
                        'draw': round(0.04, 3),
                        'away': round(lider_prob, 3)
                    }
        
        # Segundo tiempo (45-80 minutos)
        elif match_minute >= 45:
            if home_goals == away_goals:
                empate_multiplier = 1.4
                original_probs['draw'] *= empate_multiplier
                total = sum(original_probs.values())
                return {k: round(v/total, 3) for k, v in original_probs.items()}
        
        return original_probs


class MejoraEficiencia:
    """Modela la eficiencia de conversión de goles por equipo"""
    
    @staticmethod
    def ajustar_por_eficiencia(
        home_xg: float,
        away_xg: float,
        home_conversion_rate: float = 0.15,
        away_conversion_rate: float = 0.15
    ) -> Tuple[float, float]:
        """
        Ajusta xG por capacidad de conversión real del equipo
        
        Args:
            home_xg: xG del equipo local
            away_xg: xG del equipo visitante
            home_conversion_rate: Tasa de conversión histórica del equipo local
            away_conversion_rate: Tasa de conversión histórica del equipo visitante
            
        Returns:
            Tupla con (home_xg_ajustado, away_xg_ajustado)
        """
        # Ajuste basado en eficiencia
        # Equipos con mayor eficiencia convierten mejor su xG
        
        home_adjustment = 1 + (home_conversion_rate - 0.15) * 1.5  # Ajuste de hasta +/- 30%
        away_adjustment = 1 + (away_conversion_rate - 0.15) * 1.5
        
        adjusted_home_xg = home_xg * home_adjustment
        adjusted_away_xg = away_xg * away_adjustment
        
        return round(adjusted_home_xg, 2), round(adjusted_away_xg, 2)
    
    @staticmethod
    def calcular_eficiencia_equipo(goals: int, shots_on_target: int) -> float:
        """
        Calcula la tasa de conversión de un equipo
        
        Args:
            goals: Goles marcados
            shots_on_target: Tiros a puerta
            
        Returns:
            Tasa de conversión (0.0 - 1.0)
        """
        if shots_on_target == 0:
            return 0.15  # Tasa promedio
        
        conversion = goals / shots_on_target
        return max(0.05, min(0.80, conversion))  # Limitar entre 5% y 80%


class MejoraRivalidad:
    """Ponderación según calidad relativa de los equipos"""
    
    @staticmethod
    def peso_reglas_segun_rival(home_elo: float, away_elo: float) -> Dict[str, float]:
        """
        Ajusta pesos de reglas según diferencia ELO entre equipos
        
        Args:
            home_elo: ELO del equipo local
            away_elo: ELO del equipo visitante
            
        Returns:
            Diccionario con pesos ajustados para cada tipo de regla
        """
        diff_elo = home_elo - away_elo
        
        # Caso 1: Favorito claro (diferencia > 150)
        if diff_elo > 150:
            return {
                'recent_form': 0.70,      # Menos peso a forma reciente
                'h2h': 0.90,              # Más peso al historial
                'home_advantage': 0.65,   # Menos ventaja local
                'underdog_risk': 0.35,    # Agregar factor de sorpresa
                'efficiency_boost': 0.20  # Equipo débil más eficiente
            }
        
        # Caso 2: Favorito moderado (100-150)
        elif diff_elo > 100:
            return {
                'recent_form': 0.85,
                'h2h': 0.85,
                'home_advantage': 0.75,
                'underdog_risk': 0.25,
                'efficiency_boost': 0.15
            }
        
        # Caso 3: Partido equilibrado (±100)
        elif diff_elo > -100:
            return {
                'recent_form': 1.00,
                'h2h': 1.00,
                'home_advantage': 1.00,
                'underdog_risk': 0.15,
                'efficiency_boost': 0.10
            }
        
        # Caso 4: Desfavorito (away team favorito)
        elif diff_elo > -150:
            return {
                'recent_form': 1.15,      # Más peso a forma reciente
                'h2h': 0.90,
                'home_advantage': 1.25,   # Ventaja local importante
                'underdog_risk': 0.10,
                'efficiency_boost': 0.05
            }
        
        # Caso 5: Desfavorito claro
        else:
            return {
                'recent_form': 1.30,
                'h2h': 0.85,
                'home_advantage': 1.40,
                'underdog_risk': 0.05,
                'efficiency_boost': 0.05
            }
    
    @staticmethod
    def riesgo_gol_sorpresa_final(
        match_minute: int,
        score_difference: int,
        home_elo: float,
        away_elo: float
    ) -> Dict[str, float]:
        """
        Modela probabilidad de gol sorpresa en final del partido
        
        Args:
            match_minute: Minuto actual
            score_difference: Diferencia de goles (home - away)
            home_elo: ELO del equipo local
            away_elo: ELO del equipo visitante
            
        Returns:
            Diccionario con probabilidad de sorpresa y tipo
        """
        diff_elo = home_elo - away_elo
        
        # Solo en últimos 10 minutos
        if match_minute < 80:
            return {
                'surprise_goal_probability': 0.05,
                'match_type': 'normal'
            }
        
        # Empate en últimos minutos = alta probabilidad de sorpresa
        if score_difference == 0:
            surprise_prob = 0.20
            
            # Si hay gran diferencia ELO, mayor probabilidad
            if abs(diff_elo) > 150:
                surprise_prob = 0.25
            
            return {
                'surprise_goal_probability': surprise_prob,
                'match_type': 'balanced_late',
                'both_teams_risk': True
            }
        
        # Equipo perdiendo por 1 gol = presión final
        elif abs(score_difference) == 1:
            surprise_prob = 0.15
            
            # Si es el equipo débil el que pierde, menos sorpresa
            if (score_difference < 0 and diff_elo > 100) or \
               (score_difference > 0 and diff_elo < -100):
                surprise_prob = 0.08
            
            return {
                'surprise_goal_probability': surprise_prob,
                'match_type': 'one_goal_difference',
                'equalizing_risk': True
            }
        
        return {
            'surprise_goal_probability': 0.03,
            'match_type': 'settled'
        }


class AplicarMejorasCompletas:
    """Aplica todas las mejoras de forma integrada"""
    
    def __init__(self):
        self.mejora_temporal = MejoraTemporal()
        self.mejora_eficiencia = MejoraEficiencia()
        self.mejora_rivalidad = MejoraRivalidad()
    
    def predecir_mejorado(
        self,
        home_elo: float,
        away_elo: float,
        home_xg: float,
        away_xg: float,
        original_probs: Dict[str, float],
        match_minute: int = 0,
        home_goals: int = 0,
        away_goals: int = 0,
        home_shots_on_target: int = None,
        away_shots_on_target: int = None
    ) -> Dict:
        """
        Predicción mejorada integrando todas las mejoras
        
        Args:
            home_elo, away_elo: Ratings ELO
            home_xg, away_xg: xG esperados
            original_probs: Probabilidades originales {'home': X, 'draw': Y, 'away': Z}
            match_minute: Minuto del partido (0 = antes del partido)
            home_goals, away_goals: Goles actuales
            home_shots_on_target, away_shots_on_target: Tiros a puerta
            
        Returns:
            Diccionario con predicción mejorada y metadatos
        """
        # 1. Ajustar xG por eficiencia si hay datos
        if home_shots_on_target is not None and away_shots_on_target is not None:
            home_efficiency = self.mejora_eficiencia.calcular_eficiencia_equipo(
                home_goals, home_shots_on_target
            )
            away_efficiency = self.mejora_eficiencia.calcular_eficiencia_equipo(
                away_goals, away_shots_on_target
            )
            
            home_xg, away_xg = self.mejora_eficiencia.ajustar_por_eficiencia(
                home_xg, away_xg, home_efficiency, away_efficiency
            )
        
        # 2. Obtener pesos según calidad del rival
        pesos = self.mejora_rivalidad.peso_reglas_segun_rival(home_elo, away_elo)
        
        # 3. Ajustar probabilidades según contexto temporal
        adjusted_probs = self.mejora_temporal.ajustar_probabilidades_tiempo_real(
            match_minute, home_goals, away_goals, original_probs.copy()
        )
        
        # 4. Calcular riesgo de gol sorpresa
        score_diff = home_goals - away_goals
        surprise_risk = self.mejora_rivalidad.riesgo_gol_sorpresa_final(
            match_minute, score_diff, home_elo, away_elo
        )
        
        return {
            'probabilities': adjusted_probs,
            'adjusted_xg': {
                'home': home_xg,
                'away': away_xg
            },
            'rule_weights': pesos,
            'surprise_risk': surprise_risk,
            'confidence': self._calcular_confianza(adjusted_probs, pesos),
            'recommendations': self._generar_recomendaciones(adjusted_probs, surprise_risk, pesos)
        }
    
    def _calcular_confianza(self, probs: Dict[str, float], pesos: Dict[str, float]) -> float:
        """Calcula nivel de confianza en la predicción"""
        max_prob = max(probs.values())
        
        # Confianza alta si probabilidad dominante > 60%
        if max_prob > 0.60:
            confianza_base = 0.85
        elif max_prob > 0.45:
            confianza_base = 0.70
        else:
            confianza_base = 0.55
        
        # Ajustar por pesos
        if pesos.get('underdog_risk', 0.15) > 0.25:
            confianza_base *= 0.85  # Reducir confianza en partidos con mayor riesgo
        
        return round(confianza_base, 2)
    
    def _generar_recomendaciones(
        self,
        probs: Dict[str, float],
        surprise_risk: Dict,
        pesos: Dict[str, float]
    ) -> list:
        """Genera recomendaciones de apuestas"""
        recommendations = []
        
        max_prob_team = max(probs.items(), key=lambda x: x[1])
        
        # Recomendación principal
        if max_prob_team[1] > 0.55:
            recommendations.append({
                'type': 'STRONG',
                'bet': max_prob_team[0].upper(),
                'confidence': 'HIGH',
                'reason': f'Probabilidad dominante del {max_prob_team[1]*100:.1f}%'
            })
        
        # Alertas de riesgo
        if pesos.get('underdog_risk', 0.15) > 0.25:
            recommendations.append({
                'type': 'WARNING',
                'message': 'Riesgo alto de sorpresa del equipo débil',
                'risk_level': 'MEDIUM'
            })
        
        if surprise_risk.get('surprise_goal_probability', 0.05) > 0.15:
            recommendations.append({
                'type': 'INFO',
                'message': 'Alta probabilidad de gol sorpresa en últimos minutos',
                'suggestion': 'Considerar apuestas en vivo o over 2.5'
            })
        
        return recommendations
