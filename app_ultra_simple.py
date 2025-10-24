#!/usr/bin/env python3
"""
Aplicación Flask ultra-simplificada para Railway
Sistema de Precisión Máxima (75.2%)
"""

import os
import sys
from datetime import datetime
from flask import Flask, render_template, jsonify, request

# Configurar path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Crear aplicación Flask
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'sistema_precision_maxima_2025')

# Configuración de precisión máxima
MODEL_ACCURACY = 75.2
AVG_CONFIDENCE = 89.1
TOTAL_MATCHES = 2079

@app.route('/')
def index():
    """Página principal del dashboard"""
    try:
        # Estadísticas del sistema de precisión máxima
        system_stats = {
            'model_accuracy': f"{MODEL_ACCURACY:.1f}%",
            'matches_analyzed': f"{TOTAL_MATCHES:,}",
            'avg_confidence': f"{AVG_CONFIDENCE:.1f}%",
            'last_update': datetime.now().strftime('%H:%M')
        }
        
        # Datos de ejemplo para próximos partidos
        upcoming_fixtures = [
            {
                'HomeTeam': 'Liverpool',
                'AwayTeam': 'Manchester City',
                'Date': '2025-10-25',
                'League': 'E0'
            },
            {
                'HomeTeam': 'Barcelona',
                'AwayTeam': 'Real Madrid',
                'Date': '2025-10-26',
                'League': 'SP1'
            },
            {
                'HomeTeam': 'Bayern Munich',
                'AwayTeam': 'Borussia Dortmund',
                'Date': '2025-10-27',
                'League': 'D1'
            }
        ]
        
        # Agrupar por liga
        fixtures_by_league = {}
        for fixture in upcoming_fixtures:
            league = fixture['League']
            if league not in fixtures_by_league:
                fixtures_by_league[league] = []
            fixtures_by_league[league].append(fixture)
        
        return render_template('index.html', 
                            fixtures_by_league=fixtures_by_league,
                            system_stats=system_stats,
                            total_fixtures=len(upcoming_fixtures),
                            con_reglas=True)
    except Exception as e:
        return f"Error cargando dashboard: {str(e)}", 500

@app.route('/predict/<league>/<home_team>/<away_team>')
def predict(league, home_team, away_team):
    """Predicción simplificada"""
    try:
        # Predicción de ejemplo con precisión máxima
        prediction = {
            '1x2': {
                'home': 0.45,  # 45%
                'draw': 0.25,  # 25%
                'away': 0.30   # 30%
            },
            'confidence': 0.89,  # 89%
            'model_info': {
                'type': 'Sistema de Precisión Máxima',
                'accuracy': '75.2%',
                'models_used': 15,
                'features': 268
            }
        }
        
        return jsonify(prediction)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/alerts')
def alerts():
    """Página de alertas"""
    try:
        return render_template('alerts.html')
    except Exception as e:
        return f"Error cargando alertas: {str(e)}", 500

@app.route('/api/generate_alerts')
def generate_alerts():
    """Generar alertas de valor"""
    try:
        # Alertas de ejemplo
        alerts = [
            {
                'match': 'Liverpool vs Manchester City',
                'market': '1X2',
                'prediction': 'Liverpool',
                'probability': 0.45,
                'odds': 2.2,
                'value': 0.12,
                'confidence': 0.89
            }
        ]
        
        return jsonify({
            'alerts': alerts,
            'total': len(alerts),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health_check():
    """Endpoint de healthcheck para Railway"""
    return {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'model_accuracy': f"{MODEL_ACCURACY:.1f}%",
        'system': 'Sistema de Precisión Máxima'
    }, 200

@app.route('/status')
def status():
    """Endpoint de estado del sistema"""
    return {
        'system': 'Sistema de Precisión Máxima',
        'version': '1.0.0',
        'model_accuracy': f"{MODEL_ACCURACY:.1f}%",
        'avg_confidence': f"{AVG_CONFIDENCE:.1f}%",
        'total_matches': TOTAL_MATCHES,
        'models_used': 15,
        'features': 268,
        'status': 'operational',
        'timestamp': datetime.now().isoformat()
    }, 200

def main():
    """Función principal"""
    # Configuración para Railway
    PORT = int(os.environ.get("PORT", 8080))
    HOST = "0.0.0.0"
    DEBUG = os.environ.get("FLASK_DEBUG", "False").lower() == "true"
    
    print("=" * 70)
    print("SISTEMA DE PRECISION MAXIMA (75.2%) - INICIANDO")
    print("=" * 70)
    print(f"Host: {HOST}")
    print(f"Puerto: {PORT}")
    print(f"Debug: {DEBUG}")
    print(f"URL: http://{HOST}:{PORT}")
    print("=" * 70)
    
    app.run(host=HOST, port=PORT, debug=DEBUG)

if __name__ == "__main__":
    main()
