"""
Dashboard Profesional con Argon Template
Sistema de predicciones para proximos partidos de futbol

Uso:
    python app_argon.py
    
Abre en: http://localhost:5000
"""

from flask import Flask, render_template, jsonify, request
import pandas as pd
import numpy as np
from pathlib import Path
import urllib.parse
from datetime import datetime, timezone, timedelta
import pytz
import yaml

from scripts.predict_matches import MatchPredictor
from src.analysis.match_analyzer import analyze_single_match
from src.analysis.prediction_helper import generate_complete_predictions, get_betting_recommendations
from src.analysis.alerts import AlertManager

app = Flask(__name__)

# Cargar logos de equipos desde YAML
def load_team_logos():
    """Carga los logos de equipos desde el archivo YAML"""
    try:
        with open('config/team_logos.yaml', 'r', encoding='utf-8') as file:
            data = yaml.safe_load(file)
            # Combinar todas las ligas en un solo diccionario
            all_logos = {}
            for league, teams in data.items():
                all_logos.update(teams)
            return all_logos
    except Exception as e:
        print(f"Error cargando logos: {e}")
        return {}

# Cargar logos al iniciar la aplicación
TEAM_LOGOS = load_team_logos()

# Función para convertir hora a Colombia
def convert_to_colombia_time(date_str, time_str):
    """
    Convierte la fecha y hora a hora de Colombia (COT - UTC-5)
    Maneja diferentes zonas horarias según la liga
    """
    try:
        # Parsear fecha y hora
        datetime_str = f"{date_str} {time_str}"
        
        # Intentar diferentes formatos de fecha
        date_formats = [
            "%d/%m/%Y %H:%M",
            "%Y-%m-%d %H:%M",
            "%d-%m-%Y %H:%M",
            "%m/%d/%Y %H:%M",
            "%d/%m/%Y",
            "%Y-%m-%d",
            "%d-%m-%Y",
            "%m/%d/%Y"
        ]
        
        dt = None
        for fmt in date_formats:
            try:
                if len(fmt.split()) == 1:  # Solo fecha
                    dt = datetime.strptime(date_str, fmt)
                    # Agregar hora si no está presente
                    if time_str:
                        time_parts = time_str.split(':')
                        if len(time_parts) >= 2:
                            dt = dt.replace(hour=int(time_parts[0]), minute=int(time_parts[1]))
                        else:
                            dt = dt.replace(hour=15, minute=0)  # Hora por defecto 3 PM
                    else:
                        dt = dt.replace(hour=15, minute=0)  # Hora por defecto 3 PM
                else:  # Fecha y hora
                    dt = datetime.strptime(datetime_str, fmt)
                break
            except ValueError:
                continue
        
        if dt is None:
            # Si no se puede parsear, devolver valores originales
            return date_str, time_str
        
        # Asumir que la hora viene en UTC o hora local de la liga
        # Convertir a UTC primero si no tiene zona horaria
        if dt.tzinfo is None:
            # Asumir UTC para ligas europeas (Premier League, La Liga, etc.)
            dt = dt.replace(tzinfo=timezone.utc)
        
        # Convertir a hora de Colombia
        colombia_tz = pytz.timezone('America/Bogota')
        dt_colombia = dt.astimezone(colombia_tz)
        
        # Formatear de vuelta
        new_date = dt_colombia.strftime("%d/%m/%Y")
        new_time = dt_colombia.strftime("%H:%M")
        
        return new_date, new_time
        
    except Exception as e:
        print(f"Error convirtiendo hora: {e}")
        return date_str, time_str

# Función para obtener el logo del equipo
def get_team_logo(team_name):
    """
    Retorna la URL del logo del equipo.
    Si no existe, retorna un placeholder con la inicial del equipo.
    """
    # Limpiar el nombre del equipo
    clean_name = team_name.strip()
    
    # Buscar coincidencia exacta
    if clean_name in TEAM_LOGOS:
        return TEAM_LOGOS[clean_name]
    
    # Buscar coincidencia parcial (ignorar case)
    for team, logo in TEAM_LOGOS.items():
        if team.lower() in clean_name.lower() or clean_name.lower() in team.lower():
            return logo
    
    # Si no se encuentra, retornar None para que se use el fallback CSS
    return None

# Función para traducir términos técnicos
def translate_team_position(position):
    """Traduce posiciones de equipo al español"""
    translations = {
        'home': 'Local',
        'away': 'Visitante',
        'draw': 'Empate'
    }
    return translations.get(position.lower(), position)

# Registrar las funciones en el contexto de Jinja2
@app.context_processor
def utility_processor():
    return dict(
        get_team_logo=get_team_logo, 
        convert_to_colombia_time=convert_to_colombia_time,
        translate_team_position=translate_team_position
    )
app.config['SECRET_KEY'] = 'sports-forecasting-pro-2025'

PROC = Path("data/processed")
REPORTS = Path("reports")

# Cargar predictor globalmente (solo una vez)
print("Inicializando predictor...")
predictor = MatchPredictor()
predictor.load_and_train()
print("OK - Predictor listo")

# Cargar fixtures proximos - SINCRONIZACION AUTOMATICA AL INICIO
try:
    upcoming_fixtures = pd.read_parquet(PROC / "upcoming_fixtures.parquet")
    print(f"OK - {len(upcoming_fixtures)} fixtures cargados")
except:
    print("ADVERTENCIA: No se encontraron fixtures, sincronizando automaticamente...")
    try:
        from scripts.get_upcoming_fixtures import prepare_fixtures_for_prediction
        prepare_fixtures_for_prediction()
        upcoming_fixtures = pd.read_parquet(PROC / "upcoming_fixtures.parquet")
        print(f"OK - Fixtures sincronizados automaticamente: {len(upcoming_fixtures)} partidos")
    except Exception as e:
        upcoming_fixtures = pd.DataFrame()
        print(f"ERROR - No se pudieron cargar fixtures: {e}")


@app.route('/')
def index():
    """
    Pagina principal con lista de proximos partidos.
    Sincronizacion automatica de fixtures.
    """
    # Sincronizacion automatica de fixtures - SOLO SI NO HAY DATOS
    global upcoming_fixtures
    if len(upcoming_fixtures) == 0:
        try:
            print("OK - No hay fixtures, sincronizando automaticamente...")
            from scripts.get_upcoming_fixtures import prepare_fixtures_for_prediction
            prepare_fixtures_for_prediction()
            upcoming_fixtures = pd.read_parquet(PROC / "upcoming_fixtures.parquet")
            print(f"OK - Fixtures sincronizados: {len(upcoming_fixtures)} partidos")
        except Exception as e:
            print(f"ERROR - Error en sincronizacion: {e}")
    else:
        print(f"OK - Usando {len(upcoming_fixtures)} fixtures existentes")
    
    # Obtener proximos partidos por liga
    fixtures_by_league = {}
    
    if len(upcoming_fixtures) > 0:
        for league in upcoming_fixtures['League'].unique():
            league_fixtures = upcoming_fixtures[upcoming_fixtures['League'] == league].head(15)
            fixtures_by_league[league] = league_fixtures.to_dict('records')
    else:
        # Si aun no hay fixtures, intentar sincronizacion final
        print("ADVERTENCIA: Aun no hay fixtures, intentando sincronizacion final...")
        try:
            from scripts.get_upcoming_fixtures import prepare_fixtures_for_prediction
            prepare_fixtures_for_prediction()
            upcoming_fixtures = pd.read_parquet(PROC / "upcoming_fixtures.parquet")
            print(f"OK - Fixtures obtenidos en sincronizacion final: {len(upcoming_fixtures)} partidos")
            
            # Reintentar organizar por liga
            for league in upcoming_fixtures['League'].unique():
                league_fixtures = upcoming_fixtures[upcoming_fixtures['League'] == league].head(10)
                fixtures_by_league[league] = league_fixtures.to_dict('records')
        except Exception as e:
            print(f"ERROR - Sincronizacion final fallo: {e}")
    
    # Estadisticas de backtesting
    backtest_stats = {}
    try:
        log = pd.read_csv(REPORTS / "backtest_log.csv")
        backtest_stats = {
            'roi': f"{(log['pnl'].sum() / log['stake'].sum() * 100):.2f}%",
            'total_bets': len(log),
            'hit_rate': f"{(log['result']=='WIN').mean()*100:.1f}%",
            'pnl': f"{log['pnl'].sum():.2f}"
        }
    except:
        backtest_stats = {'roi': 'N/A', 'total_bets': 0, 'hit_rate': 'N/A', 'pnl': 'N/A'}
    
    return render_template('index.html', 
                         fixtures_by_league=fixtures_by_league,
                         backtest_stats=backtest_stats,
                         total_fixtures=len(upcoming_fixtures))


@app.route('/predict/<league>/<int:match_idx>')
def predict_match(league, match_idx):
    """
    Pagina de prediccion detallada para un partido especifico FUTURO.
    Sincronizacion automatica de fixtures.
    """
    # Sincronizacion automatica antes de hacer prediccion
    try:
        print(f"OK - Sincronizando fixtures para prediccion de {league}...")
        from scripts.get_upcoming_fixtures import prepare_fixtures_for_prediction
        prepare_fixtures_for_prediction()
        
        # Recargar fixtures actualizados
        global upcoming_fixtures
        upcoming_fixtures = pd.read_parquet(PROC / "upcoming_fixtures.parquet")
    except Exception as e:
        print(f"ERROR - Error en sincronizacion: {e}")
    
    # Obtener datos del partido FUTURO
    league_fixtures = upcoming_fixtures[upcoming_fixtures['League'] == league].reset_index(drop=True)
    
    if match_idx >= len(league_fixtures):
        return "Partido no encontrado", 404
    
    match_data = league_fixtures.iloc[match_idx].to_dict()
    
    # Generar prediccion
    predictions = predictor.predict_all(match_data)
    
    # Agregar fecha del partido
    match_data['fixture_date'] = match_data.get('Date', 'N/A')
    match_data['fixture_time'] = match_data.get('Time', 'N/A')
    
    return render_template('predict.html', 
                         match_data=match_data,
                         predictions=predictions)


@app.route('/api/predict', methods=['POST'])
def api_predict():
    """
    API REST para hacer predicciones.
    """
    data = request.json
    
    try:
        predictions = predictor.predict_all(data)
        return jsonify(predictions)
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/sync')
def sync_fixtures():
    """
    Endpoint para sincronizacion manual de fixtures.
    """
    try:
        print("OK - Sincronizacion manual iniciada...")
        from scripts.get_upcoming_fixtures import prepare_fixtures_for_prediction
        prepare_fixtures_for_prediction()
        
        # Recargar fixtures actualizados
        global upcoming_fixtures
        upcoming_fixtures = pd.read_parquet(PROC / "upcoming_fixtures.parquet")
        
        result = {
            'status': 'success',
            'message': f'OK - Fixtures sincronizados: {len(upcoming_fixtures)} partidos',
            'total_fixtures': len(upcoming_fixtures)
        }
        print(result['message'])
        return jsonify(result)
        
    except Exception as e:
        result = {
            'status': 'error',
            'message': f'ERROR - Error en sincronizacion: {str(e)}'
        }
        print(result['message'])
        return jsonify(result), 500


@app.route('/api/fixtures')
def api_fixtures():
    """
    API para obtener fixtures proximos.
    """
    league = request.args.get('league', None)
    
    if league:
        fixtures = upcoming_fixtures[upcoming_fixtures['League'] == league]
    else:
        fixtures = upcoming_fixtures
    
    return jsonify(fixtures.head(50).to_dict('records'))


@app.route('/backtesting')
def backtesting():
    """
    Pagina de backtesting con estadisticas historicas.
    """
    try:
        log = pd.read_csv(REPORTS / "backtest_log.csv", parse_dates=['date'])
        
        # Metricas generales
        stats = {
            'total_bets': len(log),
            'turnover': log['stake'].sum(),
            'pnl': log['pnl'].sum(),
            'roi': (log['pnl'].sum() / log['stake'].sum() * 100),
            'hit_rate': (log['result']=='WIN').mean() * 100
        }
        
        # Por mercado
        by_market = log.groupby('market').agg({
            'stake': 'sum',
            'pnl': 'sum',
            'result': 'count'
        }).reset_index()
        by_market['roi'] = (by_market['pnl'] / by_market['stake'] * 100).round(2)
        by_market.columns = ['Mercado', 'Turnover', 'PNL', 'Apuestas', 'ROI']
        
        return render_template('backtesting.html',
                             stats=stats,
                             by_market=by_market.to_dict('records'),
                             recent_bets=log.tail(20).to_dict('records'))
    except:
        return render_template('backtesting.html',
                             stats={},
                             by_market=[],
                             recent_bets=[])


@app.route('/analysis/<league>/<int:match_index>')
def analysis(league, match_index):
    """
    Pagina de analisis completo con insights automáticos y recomendaciones.
    """
    try:
        # Cargar fixtures
        fixtures_df = pd.read_parquet(PROC / "upcoming_fixtures.parquet")
        league_fixtures = fixtures_df[fixtures_df['League'] == league]
        
        if match_index >= len(league_fixtures):
            return "Partido no encontrado", 404
        
        match_data = league_fixtures.iloc[match_index].to_dict()
        
        # Usar el predictor global
        global predictor
        basic_predictions = predictor.predict_all(match_data)
        
        # Generar análisis completo
        complete_predictions = generate_complete_predictions(match_data, basic_predictions)
        
        # Convertir edge_analysis a formato serializable
        analysis = complete_predictions['analysis']
        serializable_edges = []
        for edge in analysis.edge_analysis:
            serializable_edges.append({
                'market': edge.market,
                'selection': edge.selection,
                'model_prob': edge.model_prob,
                'implied_prob': edge.implied_prob,
                'odds': edge.odds,
                'edge': edge.edge,
                'recommendation': edge.recommendation.value,
                'kelly_fraction': edge.kelly_fraction,
                'confidence': edge.confidence
            })
        
        return render_template('analysis.html',
                             match_data=match_data,
                             analysis=analysis,
                             serializable_edges=serializable_edges,
                             predictions=complete_predictions['basic_predictions'],
                             formatted_predictions=complete_predictions['formatted_predictions'])
    
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"ERROR en analisis: {e}")
        print(error_trace)
        return f"Error generando análisis: {e}<br><pre>{error_trace}</pre>", 500


@app.route('/alerts')
def alerts():
    """
    Pagina de alertas de valor activas.
    """
    try:
        alert_manager = AlertManager()
        
        # Limpiar alertas expiradas
        expired_count = alert_manager.clean_expired_alerts()
        
        # Obtener alertas activas
        active_alerts = alert_manager.get_active_alerts()
        
        # Generar resumen
        summary = alert_manager.generate_alert_summary()
        
        # Agrupar por urgencia
        alerts_by_urgency = {
            'CRITICAL': alert_manager.get_alerts_by_urgency('CRITICAL'),
            'HIGH': alert_manager.get_alerts_by_urgency('HIGH'),
            'MEDIUM': alert_manager.get_alerts_by_urgency('MEDIUM'),
            'LOW': alert_manager.get_alerts_by_urgency('LOW')
        }
        
        return render_template('alerts.html',
                             alerts=active_alerts,
                             alerts_by_urgency=alerts_by_urgency,
                             summary=summary,
                             expired_cleaned=expired_count)
    
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"ERROR en alertas: {e}")
        print(error_trace)
        # Retornar página con alertas vacías en caso de error
        return render_template('alerts.html',
                             alerts=[],
                             alerts_by_urgency={'CRITICAL': [], 'HIGH': [], 'MEDIUM': [], 'LOW': []},
                             summary={'total_alerts': 0, 'critical_alerts': 0, 'high_alerts': 0, 
                                    'medium_alerts': 0, 'low_alerts': 0, 'best_edge': 0, 'total_exposure': 0},
                             expired_cleaned=0)


@app.route('/api/generate_alerts', methods=['POST'])
def api_generate_alerts():
    """
    API endpoint para generar alertas automáticas.
    Solo procesa los próximos 50 partidos para evitar sobrecarga.
    """
    try:
        # Cargar fixtures con análisis
        fixtures_df = pd.read_parquet(PROC / "upcoming_fixtures.parquet")
        
        # Filtrar solo próximos partidos (próximas 48 horas) o primeros 50
        from datetime import datetime, timedelta
        now = datetime.now()
        cutoff = now + timedelta(hours=48)
        
        # Intentar filtrar por fecha, si falla usar los primeros 50
        try:
            fixtures_df['DateObj'] = pd.to_datetime(fixtures_df['Date'])
            fixtures_df = fixtures_df[fixtures_df['DateObj'] <= cutoff].head(50)
        except:
            fixtures_df = fixtures_df.head(50)
        
        print(f"Generando alertas para {len(fixtures_df)} partidos...")
        
        # Generar análisis para partidos seleccionados
        matches_with_analysis = []
        global predictor
        
        for idx, row in fixtures_df.iterrows():
            try:
                match_data = row.to_dict()
                basic_predictions = predictor.predict_all(match_data)
                complete_predictions = generate_complete_predictions(match_data, basic_predictions)
                
                matches_with_analysis.append({
                    'match_data': match_data,
                    'analysis': complete_predictions['analysis']
                })
            except Exception as e:
                print(f"Error procesando partido {idx}: {e}")
                continue
        
        print(f"Análisis completados: {len(matches_with_analysis)}")
        
        # Generar alertas
        alert_manager = AlertManager()
        alerts = alert_manager.generate_alerts(matches_with_analysis)
        
        print(f"Alertas generadas: {len(alerts)}")
        
        # Guardar alertas
        if alerts:
            alert_manager.save_alerts(alerts)
        
        # Generar resumen
        summary = alert_manager.generate_alert_summary()
        
        return jsonify({
            'status': 'success',
            'alerts_generated': len(alerts),
            'matches_analyzed': len(matches_with_analysis),
            'summary': summary,
            'message': f'Se generaron {len(alerts)} alertas de {len(matches_with_analysis)} partidos analizados'
        })
    
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"ERROR generando alertas: {e}")
        print(error_trace)
        return jsonify({
            'status': 'error',
            'message': f'Error generando alertas: {e}'
        }), 500


if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("DASHBOARD ARGON - SPORTS FORECASTING PRO")
    print("=" * 70)
    print("\nIniciando servidor...")
    print("Dashboard disponible en: http://localhost:5000")
    print("\nPresiona Ctrl+C para detener")
    print("=" * 70 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)

