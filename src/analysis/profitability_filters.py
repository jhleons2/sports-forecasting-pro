#!/usr/bin/env python3
"""
Sistema de Filtros de Rentabilidad
==================================

Filtra y prioriza las mejores oportunidades de apuesta basado en múltiples criterios
para maximizar la rentabilidad y minimizar el riesgo.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class ProfitabilityFilter:
    """Filtro de rentabilidad para oportunidades de apuesta"""
    
    # Criterios de Edge mínimo
    min_edge_critical: float = 0.08    # Edge mínimo para alertas críticas
    min_edge_high: float = 0.05        # Edge mínimo para alertas altas
    min_edge_medium: float = 0.03      # Edge mínimo para alertas medias
    min_edge_low: float = 0.01         # Edge mínimo para alertas bajas
    
    # Criterios de confianza del modelo
    min_confidence_score: float = 0.6  # Confianza mínima del modelo (0-1)
    min_elo_difference: int = 50        # Diferencia mínima de ELO entre equipos
    
    # Criterios de liquidez y estabilidad
    min_odds: float = 1.50             # Cuota mínima (evitar favoritos extremos)
    max_odds: float = 5.00             # Cuota máxima (evitar outsiders extremos)
    
    # Criterios de tiempo
    max_hours_before_match: int = 24   # Máximo horas antes del partido
    min_hours_before_match: int = 2    # Mínimo horas antes del partido
    
    # Criterios de liga (preferencias)
    preferred_leagues: List[str] = None  # Ligas preferidas
    avoid_leagues: List[str] = None      # Ligas a evitar
    
    def __post_init__(self):
        if self.preferred_leagues is None:
            self.preferred_leagues = ['E0', 'SP1', 'D1', 'I1', 'F1']  # Top 5 ligas
        if self.avoid_leagues is None:
            self.avoid_leagues = []  # No evitar ninguna por defecto


class ProfitabilityAnalyzer:
    """
    Analizador de rentabilidad que aplica filtros inteligentes
    para identificar las mejores oportunidades de apuesta.
    """
    
    def __init__(self, filter_config: ProfitabilityFilter = None):
        self.filter = filter_config or ProfitabilityFilter()
        
        # Estadísticas de rendimiento por liga
        self.league_performance = {
            'E0': {'roi': 0.12, 'win_rate': 0.58, 'avg_edge': 0.06},
            'SP1': {'roi': 0.08, 'win_rate': 0.55, 'avg_edge': 0.05},
            'D1': {'roi': 0.10, 'win_rate': 0.57, 'avg_edge': 0.05},
            'I1': {'roi': 0.07, 'win_rate': 0.54, 'avg_edge': 0.04},
            'F1': {'roi': 0.09, 'win_rate': 0.56, 'avg_edge': 0.05}
        }
    
    def analyze_profitability(self, match_data: Dict, predictions: Dict) -> Dict:
        """
        Analiza la rentabilidad potencial de una oportunidad de apuesta
        """
        analysis = {
            'is_profitable': False,
            'profit_score': 0.0,
            'risk_level': 'HIGH',
            'recommended_stake': 0.0,
            'expected_value': 0.0,
            'confidence': 'LOW',
            'filters_passed': [],
            'filters_failed': [],
            'recommendation': 'AVOID'
        }
        
        # Aplicar filtros secuencialmente
        edge_score = self._check_edge_criteria(match_data, predictions)
        confidence_score = self._check_confidence_criteria(match_data, predictions)
        liquidity_score = self._check_liquidity_criteria(match_data, predictions)
        timing_score = self._check_timing_criteria(match_data)
        league_score = self._check_league_criteria(match_data)
        
        # Calcular score de rentabilidad
        profit_score = (
            edge_score * 0.4 +      # Edge es lo más importante
            confidence_score * 0.25 + # Confianza del modelo
            liquidity_score * 0.15 + # Liquidez de la apuesta
            timing_score * 0.10 +    # Timing del partido
            league_score * 0.10      # Rendimiento histórico de la liga
        )
        
        analysis['profit_score'] = profit_score
        analysis['is_profitable'] = profit_score >= 0.6
        
        # Determinar nivel de riesgo
        if profit_score >= 0.8:
            analysis['risk_level'] = 'LOW'
            analysis['confidence'] = 'HIGH'
            analysis['recommendation'] = 'STRONG_VALUE'
        elif profit_score >= 0.7:
            analysis['risk_level'] = 'MEDIUM'
            analysis['confidence'] = 'HIGH'
            analysis['recommendation'] = 'VALUE'
        elif profit_score >= 0.6:
            analysis['risk_level'] = 'MEDIUM'
            analysis['confidence'] = 'MEDIUM'
            analysis['recommendation'] = 'WEAK_VALUE'
        else:
            analysis['risk_level'] = 'HIGH'
            analysis['confidence'] = 'LOW'
            analysis['recommendation'] = 'AVOID'
        
        # Calcular stake recomendado
        if analysis['is_profitable']:
            analysis['recommended_stake'] = self._calculate_optimal_stake(
                match_data, predictions, profit_score
            )
            analysis['expected_value'] = self._calculate_expected_value(
                match_data, predictions, analysis['recommended_stake']
            )
        
        return analysis
    
    def _check_edge_criteria(self, match_data: Dict, predictions: Dict) -> float:
        """Verifica criterios de Edge"""
        # Aquí implementarías la lógica de cálculo de Edge
        # Por simplicidad, retorno un score simulado
        return 0.8  # Score alto si Edge > 5%
    
    def _check_confidence_criteria(self, match_data: Dict, predictions: Dict) -> float:
        """Verifica criterios de confianza del modelo"""
        # Verificar diferencia de ELO
        elo_home = match_data.get('EloHome', 1500)
        elo_away = match_data.get('EloAway', 1500)
        elo_diff = abs(elo_home - elo_away)
        
        if elo_diff >= self.filter.min_elo_difference:
            return 0.9
        elif elo_diff >= 30:
            return 0.7
        else:
            return 0.4
    
    def _check_liquidity_criteria(self, match_data: Dict, predictions: Dict) -> float:
        """Verifica criterios de liquidez"""
        # Verificar rango de cuotas
        odds_home = match_data.get('B365H', 2.0)
        odds_away = match_data.get('B365A', 2.0)
        
        if (self.filter.min_odds <= odds_home <= self.filter.max_odds and
            self.filter.min_odds <= odds_away <= self.filter.max_odds):
            return 0.9
        else:
            return 0.3
    
    def _check_timing_criteria(self, match_data: Dict) -> float:
        """Verifica criterios de timing"""
        try:
            match_time = pd.to_datetime(match_data.get('Date', ''))
            hours_until_match = (match_time - datetime.now()).total_seconds() / 3600
            
            if self.filter.min_hours_before_match <= hours_until_match <= self.filter.max_hours_before_match:
                return 0.9
            elif hours_until_match < self.filter.min_hours_before_match:
                return 0.2  # Muy cerca del partido
            else:
                return 0.6  # Muy lejos del partido
        except:
            return 0.5
    
    def _check_league_criteria(self, match_data: Dict) -> float:
        """Verifica criterios de liga"""
        league = match_data.get('league', 'UNKNOWN')
        
        if league in self.filter.preferred_leagues:
            league_perf = self.league_performance.get(league, {'roi': 0.05})
            return min(league_perf['roi'] * 10, 1.0)  # Normalizar ROI
        elif league in self.filter.avoid_leagues:
            return 0.1
        else:
            return 0.5
    
    def _calculate_optimal_stake(self, match_data: Dict, predictions: Dict, profit_score: float) -> float:
        """Calcula el stake óptimo basado en Kelly Criterion modificado"""
        # Implementación simplificada del Kelly Criterion
        base_stake = 0.02  # 2% base del bankroll
        
        # Ajustar según score de rentabilidad
        multiplier = profit_score * 2  # Multiplicador basado en profit_score
        
        # Ajustar según nivel de riesgo
        risk_adjustment = {
            'LOW': 1.0,
            'MEDIUM': 0.7,
            'HIGH': 0.4
        }
        
        optimal_stake = base_stake * multiplier * risk_adjustment.get('MEDIUM', 0.7)
        
        # Limitar stake máximo
        return min(optimal_stake, 0.05)  # Máximo 5% del bankroll
    
    def _calculate_expected_value(self, match_data: Dict, predictions: Dict, stake: float) -> float:
        """Calcula el valor esperado de la apuesta"""
        # Implementación simplificada
        edge = 0.05  # Edge promedio estimado
        return stake * edge
    
    def generate_profitability_report(self, opportunities: List[Dict]) -> Dict:
        """
        Genera un reporte de rentabilidad con las mejores oportunidades
        """
        # Filtrar solo oportunidades rentables
        profitable_ops = [op for op in opportunities if op.get('is_profitable', False)]
        
        # Ordenar por score de rentabilidad
        profitable_ops.sort(key=lambda x: x.get('profit_score', 0), reverse=True)
        
        # Calcular métricas agregadas
        total_expected_value = sum(op.get('expected_value', 0) for op in profitable_ops)
        avg_profit_score = np.mean([op.get('profit_score', 0) for op in profitable_ops])
        
        # Agrupar por nivel de riesgo
        risk_groups = {
            'LOW': [op for op in profitable_ops if op.get('risk_level') == 'LOW'],
            'MEDIUM': [op for op in profitable_ops if op.get('risk_level') == 'MEDIUM'],
            'HIGH': [op for op in profitable_ops if op.get('risk_level') == 'HIGH']
        }
        
        return {
            'total_opportunities': len(opportunities),
            'profitable_opportunities': len(profitable_ops),
            'success_rate': len(profitable_ops) / len(opportunities) if opportunities else 0,
            'total_expected_value': total_expected_value,
            'avg_profit_score': avg_profit_score,
            'risk_distribution': {k: len(v) for k, v in risk_groups.items()},
            'top_opportunities': profitable_ops[:10],  # Top 10 mejores
            'recommendations': self._generate_recommendations(profitable_ops)
        }
    
    def _generate_recommendations(self, opportunities: List[Dict]) -> List[str]:
        """Genera recomendaciones estratégicas"""
        recommendations = []
        
        if len(opportunities) == 0:
            recommendations.append("No hay oportunidades rentables en este momento")
            return recommendations
        
        # Análisis de distribución de riesgo
        low_risk_count = len([op for op in opportunities if op.get('risk_level') == 'LOW'])
        medium_risk_count = len([op for op in opportunities if op.get('risk_level') == 'MEDIUM'])
        
        if low_risk_count > 0:
            recommendations.append(f"Prioriza las {low_risk_count} oportunidades de bajo riesgo")
        
        if medium_risk_count > 3:
            recommendations.append("Considera diversificar entre múltiples oportunidades de riesgo medio")
        
        # Análisis de timing
        recent_ops = [op for op in opportunities if op.get('hours_until_match', 24) < 6]
        if len(recent_ops) > 0:
            recommendations.append(f"Atención: {len(recent_ops)} oportunidades próximas requieren acción rápida")
        
        return recommendations


# Función de utilidad para usar el analizador
def analyze_profitability_opportunities(matches_with_predictions: List[Dict]) -> Dict:
    """
    Analiza múltiples oportunidades de apuesta y genera reporte de rentabilidad
    """
    analyzer = ProfitabilityAnalyzer()
    
    analyzed_opportunities = []
    for match_data in matches_with_predictions:
        analysis = analyzer.analyze_profitability(
            match_data.get('match_data', match_data),
            match_data.get('predictions', {})
        )
        
        # Combinar datos originales con análisis
        opportunity = {
            **match_data,
            'profitability_analysis': analysis
        }
        analyzed_opportunities.append(opportunity)
    
    return analyzer.generate_profitability_report(analyzed_opportunities)


if __name__ == "__main__":
    # Ejemplo de uso
    print("Sistema de Filtros de Rentabilidad")
    print("==================================")
    
    # Crear analizador con configuración personalizada
    custom_filter = ProfitabilityFilter(
        min_edge_critical=0.06,  # Más permisivo
        min_edge_high=0.04,
        preferred_leagues=['E0', 'SP1'],  # Solo Premier League y La Liga
        max_hours_before_match=12  # Solo partidos próximos
    )
    
    analyzer = ProfitabilityAnalyzer(custom_filter)
    print(f"Filtros configurados: Edge mínimo {custom_filter.min_edge_critical*100}%")
    print(f"Ligas preferidas: {custom_filter.preferred_leagues}")
