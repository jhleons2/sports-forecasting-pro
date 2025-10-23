#!/usr/bin/env python3
"""
Script para verificar los datos de Leeds vs West Ham
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.predictor_corregido_simple import PredictorCorregidoSimple
from src.features.reglas_dinamicas import calcular_reglas_dinamicas
import pandas as pd

def verificar_datos_leeds_westham():
    """Verificar datos específicos de Leeds vs West Ham"""
    print("VERIFICANDO DATOS: Leeds United FC vs West Ham United FC")
    print("=" * 60)
    
    try:
        # Cargar predictor
        predictor = PredictorCorregidoSimple()
        predictor.load_and_train()
        
        # Datos del partido
        equipo_home = "Leeds United FC"
        equipo_away = "West Ham United FC"
        liga = "E0"
        
        print(f"\nPartido: {equipo_home} vs {equipo_away}")
        print(f"Liga: {liga}")
        
        # Mapear nombres
        home_mapeado, away_mapeado = predictor.mapear_nombres(equipo_home, equipo_away)
        print(f"\nNombres mapeados:")
        print(f"  {equipo_home} -> {home_mapeado}")
        print(f"  {equipo_away} -> {away_mapeado}")
        
        # Obtener ELO actual
        elo_home = predictor._get_current_elo(home_mapeado)
        elo_away = predictor._get_current_elo(away_mapeado)
        print(f"\nRatings ELO:")
        print(f"  {home_mapeado}: {elo_home:.0f}")
        print(f"  {away_mapeado}: {elo_away:.0f}")
        
        # Calcular reglas dinámicas
        reglas = calcular_reglas_dinamicas(
            predictor.df_historico,
            home_mapeado,
            away_mapeado,
            liga
        )
        
        print(f"\nREGLAS CALCULADAS:")
        print(f"  1. Últimos 8 total: {reglas.get('ultimos_8_total', {}).get('partidos', 0)} partidos")
        print(f"  2. Últimos 5 local: {reglas.get('ultimos_5_local', {}).get('partidos', 0)} partidos")
        print(f"  3. Últimos 5 visitante: {reglas.get('ultimos_5_visitante', {}).get('partidos', 0)} partidos")
        print(f"  4. H2H: {reglas.get('h2h', {}).get('partidos', 0)} partidos")
        
        # Verificar datos históricos específicos
        df_historico = predictor.df_historico
        
        # Buscar Leeds en datos históricos
        leeds_partidos = df_historico[
            (df_historico['HomeTeam'] == home_mapeado) | 
            (df_historico['AwayTeam'] == home_mapeado)
        ]
        print(f"\nPartidos históricos de {home_mapeado}: {len(leeds_partidos)}")
        
        # Buscar West Ham en datos históricos
        westham_partidos = df_historico[
            (df_historico['HomeTeam'] == away_mapeado) | 
            (df_historico['AwayTeam'] == away_mapeado)
        ]
        print(f"Partidos históricos de {away_mapeado}: {len(westham_partidos)}")
        
        # Buscar enfrentamientos directos
        h2h_partidos = df_historico[
            ((df_historico['HomeTeam'] == home_mapeado) & (df_historico['AwayTeam'] == away_mapeado)) |
            ((df_historico['HomeTeam'] == away_mapeado) & (df_historico['AwayTeam'] == home_mapeado))
        ]
        print(f"Enfrentamientos directos: {len(h2h_partidos)}")
        
        if len(h2h_partidos) > 0:
            print("\nÚltimos enfrentamientos:")
            for _, partido in h2h_partidos.tail(3).iterrows():
                resultado = f"{partido['FTHG']}-{partido['FTAG']}"
                print(f"  {partido['Date']}: {partido['HomeTeam']} {resultado} {partido['AwayTeam']}")
        
        # Hacer predicción completa
        predictions = predictor.predict_con_reglas_dinamicas(equipo_home, equipo_away, liga)
        
        print(f"\nPREDICCIONES:")
        print(f"  1X2 - Local: {predictions['1x2']['home']*100:.1f}%")
        print(f"  1X2 - Empate: {predictions['1x2']['draw']*100:.1f}%")
        print(f"  1X2 - Visitante: {predictions['1x2']['away']*100:.1f}%")
        print(f"  xG - Local: {predictions['xg']['home']:.2f}")
        print(f"  xG - Visitante: {predictions['xg']['away']:.2f}")
        print(f"  ELO - Local: {predictions['elo_home']:.0f}")
        print(f"  ELO - Visitante: {predictions['elo_away']:.0f}")
        
        print("\nVERIFICACION COMPLETADA")
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    verificar_datos_leeds_westham()
