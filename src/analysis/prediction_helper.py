#!/usr/bin/env python3
"""
Helper para generar predicciones completas con análisis automático
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from .match_analyzer import analyze_single_match, MatchAnalysis


def generate_complete_predictions(match_data: Dict, model_predictions: Dict) -> Dict:
    """
    Genera predicciones completas con análisis automático
    
    Args:
        match_data: Datos del partido
        model_predictions: Predicciones básicas del modelo
        
    Returns:
        Dict con predicciones completas y análisis
    """
    
    # Estructurar predicciones en formato estándar
    # Extraer predicciones 1X2 (puede venir como pH/pD/pA o home/draw/away)
    predictions_1x2 = model_predictions.get('1x2', {})
    
    # Manejar ambos formatos de 1X2
    if 'pH' in predictions_1x2:
        home_prob = predictions_1x2['pH']
        draw_prob = predictions_1x2['pD']
        away_prob = predictions_1x2['pA']
    else:
        home_prob = predictions_1x2.get('home', 0.33)
        draw_prob = predictions_1x2.get('draw', 0.33)
        away_prob = predictions_1x2.get('away', 0.34)
    
    # Extraer Asian Handicap (ya viene en formato correcto)
    ah_predictions = model_predictions.get('asian_handicap_0', {})
    
    # Extraer Over/Under
    ou_predictions = model_predictions.get('over_under_2.5', {})
    
    formatted_predictions = {
        '1x2': {
            'home': home_prob,
            'draw': draw_prob,
            'away': away_prob
        },
        'asian_handicap_0': ah_predictions,
        'over_under': ou_predictions
    }
    
    # Generar análisis automático
    analysis = analyze_single_match(match_data, formatted_predictions)
    
    # Combinar predicciones con análisis
    complete_predictions = {
        'match_data': match_data,
        'basic_predictions': model_predictions,
        'formatted_predictions': formatted_predictions,
        'analysis': analysis,
        'insights': analysis.key_insights,
        'recommendations': analysis.recommended_bets,
        'avoid_bets': analysis.avoid_bets,
        'summary': {
            'favorite_team': analysis.favorite_team,
            'favorite_prob': analysis.favorite_prob,
            'underdog_prob': analysis.underdog_prob,
            'risk_level': analysis.risk_level,
            'balanced_score': analysis.balanced_score,
            'match_outcome': analysis.match_outcome.value
        }
    }
    
    return complete_predictions


def get_betting_recommendations(analysis: MatchAnalysis, bankroll: float = 1000.0) -> Dict:
    """
    Genera recomendaciones específicas de apuestas con sizing
    
    Args:
        analysis: Análisis del partido
        bankroll: Bankroll disponible
        
    Returns:
        Dict con recomendaciones detalladas
    """
    
    recommendations = {
        'primary_bets': [],
        'secondary_bets': [],
        'avoid_bets': [],
        'total_exposure': 0.0,
        'max_stake': 0.0,
        'risk_assessment': {}
    }
    
    # Procesar cada edge analysis
    for edge in analysis.edge_analysis:
        stake_amount = edge.kelly_fraction * bankroll
        
        bet_info = {
            'market': edge.market,
            'selection': edge.selection,
            'odds': edge.odds,
            'edge': edge.edge,
            'model_prob': edge.model_prob,
            'implied_prob': edge.implied_prob,
            'kelly_fraction': edge.kelly_fraction,
            'stake_amount': stake_amount,
            'confidence': edge.confidence,
            'expected_value': edge.edge * stake_amount,
            'recommendation': edge.recommendation.value
        }
        
        # Categorizar por recomendación
        if edge.recommendation.value in ['STRONG_VALUE', 'VALUE']:
            recommendations['primary_bets'].append(bet_info)
        elif edge.recommendation.value == 'WEAK_VALUE':
            recommendations['secondary_bets'].append(bet_info)
        else:
            recommendations['avoid_bets'].append(bet_info)
        
        recommendations['total_exposure'] += stake_amount
        recommendations['max_stake'] = max(recommendations['max_stake'], stake_amount)
    
    # Evaluación de riesgo
    recommendations['risk_assessment'] = {
        'total_exposure_pct': (recommendations['total_exposure'] / bankroll) * 100,
        'max_stake_pct': (recommendations['max_stake'] / bankroll) * 100,
        'number_of_bets': len(recommendations['primary_bets']) + len(recommendations['secondary_bets']),
        'risk_level': 'LOW' if recommendations['total_exposure_pct'] < 5 else 
                     'MEDIUM' if recommendations['total_exposure_pct'] < 15 else 'HIGH'
    }
    
    return recommendations


def format_edge_for_display(edge: float) -> Dict:
    """
    Formatea un edge para mostrar en el dashboard
    
    Args:
        edge: Valor del edge (ej: 0.05 = 5%)
        
    Returns:
        Dict con información formateada
    """
    
    edge_pct = edge * 100
    
    if edge >= 0.10:
        return {
            'value': f"+{edge_pct:.1f}%",
            'class': 'success',
            'icon': 'fas fa-arrow-up',
            'description': 'Excelente valor',
            'strength': 'Fuerte'
        }
    elif edge >= 0.05:
        return {
            'value': f"+{edge_pct:.1f}%",
            'class': 'info',
            'icon': 'fas fa-arrow-up',
            'description': 'Buen valor',
            'strength': 'Moderado'
        }
    elif edge >= 0.02:
        return {
            'value': f"+{edge_pct:.1f}%",
            'class': 'warning',
            'icon': 'fas fa-minus',
            'description': 'Valor débil',
            'strength': 'Débil'
        }
    elif edge >= 0:
        return {
            'value': f"+{edge_pct:.1f}%",
            'class': 'secondary',
            'icon': 'fas fa-minus',
            'description': 'Sin ventaja clara',
            'strength': 'Mínimo'
        }
    else:
        return {
            'value': f"{edge_pct:.1f}%",
            'class': 'danger',
            'icon': 'fas fa-arrow-down',
            'description': 'Evitar',
            'strength': 'Negativo'
        }


def generate_match_summary(analysis: MatchAnalysis) -> Dict:
    """
    Genera un resumen ejecutivo del partido
    
    Args:
        analysis: Análisis del partido
        
    Returns:
        Dict con resumen ejecutivo
    """
    
    # Determinar estrategia recomendada
    if analysis.risk_level == 'LOW':
        strategy = 'CONSERVADORA'
        strategy_desc = 'Partido equilibrado - ideal para apuestas seguras'
    elif analysis.risk_level == 'MEDIUM':
        strategy = 'MODERADA'
        strategy_desc = 'Oportunidades moderadas - diversificar apuestas'
    else:
        strategy = 'AGRESIVA'
        strategy_desc = 'Alto riesgo/recompensa - stakes más pequeños'
    
    # Contar recomendaciones
    strong_value = len([e for e in analysis.edge_analysis if e.recommendation.value == 'STRONG_VALUE'])
    value = len([e for e in analysis.edge_analysis if e.recommendation.value == 'VALUE'])
    
    return {
        'strategy': strategy,
        'strategy_description': strategy_desc,
        'key_opportunities': strong_value + value,
        'avoid_count': len(analysis.avoid_bets),
        'confidence_level': 'ALTA' if analysis.balanced_score > 0.7 else 'MEDIA' if analysis.balanced_score > 0.4 else 'BAJA',
        'betting_focus': 'Asian Handicap' if any('Asian Handicap' in e.market for e in analysis.edge_analysis if e.recommendation.value in ['STRONG_VALUE', 'VALUE']) else '1X2',
        'quick_insight': analysis.key_insights[0] if analysis.key_insights else 'Sin insights específicos'
    }


if __name__ == "__main__":
    # Ejemplo de uso
    match_data = {
        'HomeTeam': 'Chelsea FC',
        'AwayTeam': 'Sunderland AFC',
        'EloHome': 1500,
        'EloAway': 1500,
        'AHh': 0.0,
        'B365H': 3.50,
        'B365D': 3.20,
        'B365A': 2.10
    }
    
    model_predictions = {
        'home_win_prob': 0.261,
        'draw_prob': 0.268,
        'away_win_prob': 0.471,
        'ah_home_prob': 0.50,
        'ah_away_prob': 0.50,
        'over_25_prob': 0.52,
        'under_25_prob': 0.48
    }
    
    complete = generate_complete_predictions(match_data, model_predictions)
    print("Predicciones completas generadas con éxito!")
    print(f"Favorito: {complete['summary']['favorite_team']}")
    print(f"Recomendaciones: {len(complete['recommendations'])}")
