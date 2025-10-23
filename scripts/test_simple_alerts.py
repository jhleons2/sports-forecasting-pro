#!/usr/bin/env python3
"""
Script para probar el sistema de alertas simplificado
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.analysis.simple_alerts import SimpleAlertManager
import pandas as pd

def test_simple_alerts():
    """Probar el sistema de alertas simplificado"""
    print("PROBANDO SISTEMA DE ALERTAS SIMPLIFICADO...")
    
    try:
        # Crear directorio de alertas si no existe
        alerts_dir = Path("data/alerts")
        alerts_dir.mkdir(parents=True, exist_ok=True)
        
        # Inicializar SimpleAlertManager
        alert_manager = SimpleAlertManager()
        print("OK: SimpleAlertManager inicializado correctamente")
        
        # Crear datos de prueba
        test_matches = [
            {
                'match_data': {
                    'HomeTeam': 'Manchester City',
                    'AwayTeam': 'Brighton',
                    'Date': '2025-10-25'
                },
                'analysis': {
                    'probabilities': {
                        'home_win': 0.75,  # Alta probabilidad de victoria local
                        'draw': 0.15,
                        'away_win': 0.10
                    },
                    'over_under': {
                        'over_2_5': 0.80,  # Alta probabilidad Over 2.5
                        'under_2_5': 0.20
                    }
                }
            },
            {
                'match_data': {
                    'HomeTeam': 'Arsenal',
                    'AwayTeam': 'Chelsea',
                    'Date': '2025-10-26'
                },
                'analysis': {
                    'probabilities': {
                        'home_win': 0.45,
                        'draw': 0.30,
                        'away_win': 0.25
                    },
                    'over_under': {
                        'over_2_5': 0.35,
                        'under_2_5': 0.65  # Alta probabilidad Under 2.5
                    }
                }
            }
        ]
        
        # Generar alertas de prueba
        alerts = alert_manager.generate_alerts_from_predictions(test_matches)
        print(f"OK: Alertas generadas: {len(alerts)}")
        
        for alert in alerts:
            print(f"  - {alert.market} {alert.selection}: {alert.recommendation}")
        
        # Guardar alertas
        if alerts:
            alert_manager.save_alerts(alerts)
            print("OK: Alertas guardadas correctamente")
        
        # Probar métodos básicos
        active_alerts = alert_manager.get_active_alerts()
        print(f"OK: Alertas activas: {len(active_alerts)}")
        
        summary = alert_manager.generate_alert_summary()
        print(f"OK: Resumen generado: {summary}")
        
        # Probar limpieza de alertas expiradas
        expired_count = alert_manager.clean_expired_alerts()
        print(f"OK: Alertas expiradas limpiadas: {expired_count}")
        
        print("\nSISTEMA DE ALERTAS SIMPLIFICADO FUNCIONANDO CORRECTAMENTE")
        return True
        
    except Exception as e:
        print(f"ERROR en sistema de alertas simplificado: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_simple_alerts()
