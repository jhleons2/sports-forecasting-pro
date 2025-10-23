#!/usr/bin/env python3
"""
Script para probar el sistema completo de análisis automático
"""

import sys
import os
sys.path.append('.')

import pandas as pd
from src.analysis.match_analyzer import analyze_single_match
from src.analysis.prediction_helper import generate_complete_predictions
from src.analysis.alerts import AlertManager


def test_analysis_system():
    """Prueba el sistema completo de análisis"""
    
    print("=" * 70)
    print("PRUEBA DEL SISTEMA DE ANÁLISIS AUTOMÁTICO")
    print("=" * 70)
    
    # Datos de ejemplo (simulando el partido Chelsea vs Sunderland)
    match_data = {
        'HomeTeam': 'Chelsea FC',
        'AwayTeam': 'Sunderland AFC',
        'EloHome': 1500,
        'EloAway': 1500,
        'AHh': 0.0,
        'B365H': 3.50,
        'B365D': 3.20,
        'B365A': 2.10,
        'B365AHH': 1.95,
        'B365AHA': 1.95,
        'B365>2.5': 2.00,
        'B365<2.5': 1.90
    }
    
    # Predicciones del modelo (simuladas)
    model_predictions = {
        'home_win_prob': 0.261,
        'draw_prob': 0.268,
        'away_win_prob': 0.471,
        'ah_home_prob': 0.50,
        'ah_away_prob': 0.50,
        'over_25_prob': 0.52,
        'under_25_prob': 0.48
    }
    
    print("\n1. GENERANDO ANÁLISIS COMPLETO...")
    print("-" * 50)
    
    # Generar análisis completo
    complete_predictions = generate_complete_predictions(match_data, model_predictions)
    analysis = complete_predictions['analysis']
    
    print(f"OK - Partido: {analysis.home_team} vs {analysis.away_team}")
    print(f"OK - Favorito: {analysis.favorite_team} ({analysis.favorite_prob:.1%})")
    print(f"OK - Nivel de riesgo: {analysis.risk_level}")
    print(f"OK - Score de equilibrio: {analysis.balanced_score:.2f}")
    
    print("\n2. INSIGHTS AUTOMÁTICOS:")
    print("-" * 50)
    for insight in analysis.key_insights:
        print(f"• {insight}")
    
    print("\n3. ANÁLISIS DE EDGES:")
    print("-" * 50)
    for edge in analysis.edge_analysis:
        edge_pct = edge.edge * 100
        print(f"[{edge.market}] {edge.selection}")
        print(f"   Edge: {edge_pct:+.1f}% | Odds: {edge.odds:.2f} | Kelly: {edge.kelly_fraction:.1%}")
        print(f"   Recomendacion: {edge.recommendation.value} | Confianza: {edge.confidence}")
        print()
    
    print("\n4. RECOMENDACIONES DE APUESTAS:")
    print("-" * 50)
    if analysis.recommended_bets:
        for bet in analysis.recommended_bets:
            print(f"OK - {bet['market']} - {bet['selection']}")
            print(f"   Edge: {bet['edge']} | Odds: {bet['odds']} | Stake: {bet['kelly']}")
    else:
        print("NO - No hay apuestas recomendadas")
    
    print("\n5. APUESTAS A EVITAR:")
    print("-" * 50)
    if analysis.avoid_bets:
        for bet in analysis.avoid_bets:
            print(f"NO - {bet['market']} - {bet['selection']} (Edge: {bet['edge']})")
    else:
        print("OK - No hay apuestas a evitar")
    
    print("\n6. PROBANDO SISTEMA DE ALERTAS...")
    print("-" * 50)
    
    # Probar sistema de alertas
    alert_manager = AlertManager()
    
    # Crear datos simulados para alertas
    matches_with_analysis = [{
        'HomeTeam': match_data['HomeTeam'],
        'AwayTeam': match_data['AwayTeam'],
        'Date': '2025-10-25',
        'analysis': analysis
    }]
    
    alerts = alert_manager.generate_alerts(matches_with_analysis)
    
    print(f"OK - Alertas generadas: {len(alerts)}")
    
    if alerts:
        for alert in alerts:
            print(f"[{alert.urgency}] {alert.home_team} vs {alert.away_team}")
            print(f"   {alert.market} - {alert.selection} | Edge: {alert.edge:.1%}")
            print(f"   Stake sugerido: {alert.stake_suggestion:.1%} | Expira: {alert.expires_at.strftime('%H:%M')}")
            print()
    
    # Generar resumen
    summary = alert_manager.generate_alert_summary()
    print("7. RESUMEN DE ALERTAS:")
    print("-" * 50)
    print(f"Total alertas: {summary['total_alerts']}")
    print(f"Críticas: {summary['critical_alerts']}")
    print(f"Altas: {summary['high_alerts']}")
    print(f"Medias: {summary['medium_alerts']}")
    print(f"Bajas: {summary['low_alerts']}")
    print(f"Mejor edge: {summary['best_edge']:.1%}")
    print(f"Exposición total: {summary['total_exposure']:.1f}%")
    
    print("\n" + "=" * 70)
    print("OK - PRUEBA COMPLETADA EXITOSAMENTE")
    print("=" * 70)
    
    return True


if __name__ == "__main__":
    try:
        test_analysis_system()
    except Exception as e:
        print(f"\nERROR - Error en la prueba: {e}")
        import traceback
        traceback.print_exc()
