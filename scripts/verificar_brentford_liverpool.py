#!/usr/bin/env python3
"""
Script para verificar el pronóstico de Brentford vs Liverpool
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.predictor_corregido_simple import PredictorCorregidoSimple
from src.features.reglas_dinamicas import calcular_reglas_dinamicas
import pandas as pd

def verificar_brentford_liverpool():
    """Verificar pronóstico específico de Brentford vs Liverpool"""
    print("VERIFICANDO PRONÓSTICO: Brentford FC vs Liverpool FC")
    print("=" * 60)
    
    try:
        # Cargar predictor
        predictor = PredictorCorregidoSimple()
        predictor.load_and_train()
        
        # Datos del partido
        equipo_home = "Brentford FC"
        equipo_away = "Liverpool FC"
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
        print(f"  1. Últimos 8 total:")
        print(f"     - {home_mapeado}: {reglas.get('ultimos_8_total', {}).get('home', {}).get('partidos', 0)} partidos")
        print(f"     - {away_mapeado}: {reglas.get('ultimos_8_total', {}).get('away', {}).get('partidos', 0)} partidos")
        print(f"  2. Últimos 5 local: {reglas.get('ultimos_5_local', {}).get('partidos', 0)} partidos")
        print(f"  3. Últimos 5 visitante: {reglas.get('ultimos_5_visitante', {}).get('partidos', 0)} partidos")
        print(f"  4. H2H: {reglas.get('h2h', {}).get('partidos', 0)} partidos")
        
        # Verificar datos históricos específicos
        df_historico = predictor.df_historico
        
        # Buscar Brentford en datos históricos
        brentford_partidos = df_historico[
            (df_historico['HomeTeam'] == home_mapeado) | 
            (df_historico['AwayTeam'] == home_mapeado)
        ]
        print(f"\nPartidos históricos de {home_mapeado}: {len(brentford_partidos)}")
        
        # Buscar Liverpool en datos históricos
        liverpool_partidos = df_historico[
            (df_historico['HomeTeam'] == away_mapeado) | 
            (df_historico['AwayTeam'] == away_mapeado)
        ]
        print(f"Partidos históricos de {away_mapeado}: {len(liverpool_partidos)}")
        
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
        
        print(f"\nPRONÓSTICO ACTUAL:")
        print(f"  Brentford FC: {predictions['1x2']['home']*100:.1f}%")
        print(f"  Empate: {predictions['1x2']['draw']*100:.1f}%")
        print(f"  Liverpool FC: {predictions['1x2']['away']*100:.1f}%")
        print(f"  xG - Brentford: {predictions['xg']['home']:.2f}")
        print(f"  xG - Liverpool: {predictions['xg']['away']:.2f}")
        print(f"  ELO - Brentford: {predictions['elo_home']:.0f}")
        print(f"  ELO - Liverpool: {predictions['elo_away']:.0f}")
        
        # Análisis de la predicción
        print(f"\nANÁLISIS DEL PRONÓSTICO:")
        elo_diff = predictions['elo_home'] - predictions['elo_away']
        print(f"  Diferencia ELO: {elo_diff:.0f} puntos")
        
        if predictions['1x2']['away'] > 0.6:
            print(f"  OK: Liverpool es CLARO FAVORITO ({predictions['1x2']['away']*100:.1f}%)")
        elif predictions['1x2']['away'] > 0.5:
            print(f"  ADVERTENCIA: Liverpool es FAVORITO ({predictions['1x2']['away']*100:.1f}%)")
        else:
            print(f"  ERROR: Liverpool NO es favorito ({predictions['1x2']['away']*100:.1f}%)")
        
        # Verificar si es realista
        print(f"\n¿ES REALISTA ESTE PRONÓSTICO?")
        if predictions['1x2']['away'] > 0.65:
            print(f"  SÍ - Liverpool es uno de los mejores equipos del mundo")
            print(f"  SÍ - Brentford es equipo de mitad de tabla")
            print(f"  SÍ - Diferencia ELO significativa ({elo_diff:.0f} puntos)")
        else:
            print(f"  NO - Liverpool debería ser más favorito")
        
        print("\nVERIFICACION COMPLETADA")
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    verificar_brentford_liverpool()
