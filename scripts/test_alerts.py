#!/usr/bin/env python3
"""
Script para probar el sistema de alertas
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.analysis.alerts import AlertManager
import pandas as pd

def test_alerts():
    """Probar el sistema de alertas"""
    print("PROBANDO SISTEMA DE ALERTAS...")
    
    try:
        # Crear directorio de alertas si no existe
        alerts_dir = Path("data/alerts")
        alerts_dir.mkdir(parents=True, exist_ok=True)
        
        # Inicializar AlertManager
        alert_manager = AlertManager()
        print("OK: AlertManager inicializado correctamente")
        
        # Probar métodos básicos
        active_alerts = alert_manager.get_active_alerts()
        print(f"OK: Alertas activas: {len(active_alerts)}")
        
        summary = alert_manager.generate_alert_summary()
        print(f"OK: Resumen generado: {summary}")
        
        # Probar limpieza de alertas expiradas
        expired_count = alert_manager.clean_expired_alerts()
        print(f"OK: Alertas expiradas limpiadas: {expired_count}")
        
        print("\nSISTEMA DE ALERTAS FUNCIONANDO CORRECTAMENTE")
        return True
        
    except Exception as e:
        print(f"ERROR en sistema de alertas: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_alerts()
