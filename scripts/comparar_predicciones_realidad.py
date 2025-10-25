"""
Comparador de Predicciones vs Realidad
=======================================

Este script compara las predicciones generadas por el sistema
con los resultados reales de partidos ya jugados.

Funcionalidades:
1. Carga datos históricos (partidos ya jugados con resultados)
2. Genera predicciones para esos partidos
3. Compara predicciones vs resultados reales
4. Calcula métricas de precisión
5. Genera reporte de aciertos/errores
"""

import sys
from pathlib import Path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List
from scripts.predictor_corregido_simple import PredictorCorregidoSimple

PROC = Path("data/processed")
REPORTS = Path("reports")


def comparar_prediccion_realidad(
    df_historico: pd.DataFrame,
    predictor: PredictorCorregidoSimple,
    fecha_inicio: str = None,
    fecha_fin: str = None
) -> pd.DataFrame:
    """
    Compara predicciones con resultados reales
    
    Args:
        df_historico: DataFrame con partidos históricos (ya jugados)
        predictor: Instancia del predictor
        fecha_inicio: Fecha desde donde empezar a comparar
        fecha_fin: Fecha hasta donde comparar
    
    Returns:
        DataFrame con comparación de predicciones vs realidad
    """
    print("\n" + "=" * 70)
    print("  COMPARACIÓN: PREDICCIONES VS REALIDAD")
    print("=" * 70)
    
    # Filtrar por fechas si se especifican
    if fecha_inicio:
        df_historico = df_historico[df_historico['Date'] >= fecha_inicio]
    if fecha_fin:
        df_historico = df_historico[df_historico['Date'] <= fecha_fin]
    
    print(f"\nAnalizando {len(df_historico)} partidos...")
    print(f"Rango: {df_historico['Date'].min()} a {df_historico['Date'].max()}")
    
    resultados = []
    
    for idx, row in df_historico.iterrows():
        try:
            # Obtener datos del partido
            home_team = row['HomeTeam']
            away_team = row['AwayTeam']
            league = row.get('League', 'E0')
            
            # Resultado real
            home_goals_real = int(row['FTHG'])
            away_goals_real = int(row['FTAG'])
            
            # Determinar resultado real (1X2)
            if home_goals_real > away_goals_real:
                resultado_real = 'H'
            elif away_goals_real > home_goals_real:
                resultado_real = 'A'
            else:
                resultado_real = 'D'
            
            # Mapear nombres
            home_mapeado, away_mapeado = predictor.mapear_nombres(home_team, away_team)
            
            # Obtener predicción
            prediccion = predictor.predict_con_reglas_dinamicas(
                home_team, away_team, league
            )
            
            prob_home = prediccion['1x2']['home']
            prob_draw = prediccion['1x2']['draw']
            prob_away = prediccion['1x2']['away']
            
            # Predicción del modelo (la de mayor probabilidad)
            if prob_home > prob_draw and prob_home > prob_away:
                prediccion_modelo = 'H'
            elif prob_draw > prob_away:
                prediccion_modelo = 'D'
            else:
                prediccion_modelo = 'A'
            
            # ¿Acierto?
            acierto = prediccion_modelo == resultado_real
            
            # Guardar resultado
            resultados.append({
                'fecha': row['Date'],
                'liga': league,
                'home_team': home_team,
                'away_team': away_team,
                'home_goals': home_goals_real,
                'away_goals': away_goals_real,
                'resultado_real': resultado_real,
                'prob_home': prob_home,
                'prob_draw': prob_draw,
                'prob_away': prob_away,
                'prediccion': prediccion_modelo,
                'acierto': acierto,
                'xG_home_pred': prediccion['xg']['home'],
                'xG_away_pred': prediccion['xg']['away']
            })
            
            if idx % 50 == 0:
                print(f"  Procesados {idx}/{len(df_historico)} partidos...")
                
        except Exception as e:
            print(f"  Error procesando partido {idx}: {e}")
            continue
    
    df_resultados = pd.DataFrame(resultados)
    
    print(f"\n✅ Completado: {len(df_resultados)} partidos analizados")
    
    return df_resultados


def calcular_metricas(df_resultados: pd.DataFrame) -> Dict:
    """
    Calcula métricas de precisión del modelo
    
    Returns:
        Diccionario con métricas
    """
    if len(df_resultados) == 0:
        return {}
    
    total = len(df_resultados)
    aciertos = df_resultados['acierto'].sum()
    hit_rate = (aciertos / total) * 100
    
    # Aciertos por resultado
    aciertos_home = len(df_resultados[
        (df_resultados['prediccion'] == 'H') & 
        (df_resultados['resultado_real'] == 'H')
    ])
    aciertos_draw = len(df_resultados[
        (df_resultados['prediccion'] == 'D') & 
        (df_resultados['resultado_real'] == 'D')
    ])
    aciertos_away = len(df_resultados[
        (df_resultados['prediccion'] == 'A') & 
        (df_resultados['resultado_real'] == 'A')
    ])
    
    # Distribución de predicciones vs realidad
    distribucion_predicciones = df_resultados['prediccion'].value_counts()
    distribucion_realidad = df_resultados['resultado_real'].value_counts()
    
    metrics = {
        'total_partidos': total,
        'aciertos': aciertos,
        'errores': total - aciertos,
        'hit_rate': hit_rate,
        'aciertos_home': aciertos_home,
        'aciertos_draw': aciertos_draw,
        'aciertos_away': aciertos_away,
        'distribucion_predicciones': distribucion_predicciones.to_dict(),
        'distribucion_realidad': distribucion_realidad.to_dict()
    }
    
    return metrics


def generar_reporte(df_resultados: pd.DataFrame, metrics: Dict):
    """Genera reporte en consola y archivo"""
    
    print("\n" + "=" * 70)
    print("  REPORTE DE PRECISIÓN")
    print("=" * 70)
    
    print(f"\n📊 MÉTRICAS GENERALES:")
    print(f"   Total partidos: {metrics['total_partidos']}")
    print(f"   Aciertos: {metrics['aciertos']}")
    print(f"   Errores: {metrics['errores']}")
    print(f"   Hit-rate: {metrics['hit_rate']:.2f}%")
    
    print(f"\n🎯 ACIERTOS POR RESULTADO:")
    print(f"   Home: {metrics['aciertos_home']}")
    print(f"   Draw: {metrics['aciertos_draw']}")
    print(f"   Away: {metrics['aciertos_away']}")
    
    print(f"\n📈 DISTRIBUCIÓN DE PREDICCIONES:")
    for resultado, count in metrics['distribucion_predicciones'].items():
        pct = (count / metrics['total_partidos']) * 100
        print(f"   {resultado}: {count} ({pct:.1f}%)")
    
    print(f"\n📉 DISTRIBUCIÓN DE REALIDAD:")
    for resultado, count in metrics['distribucion_realidad'].items():
        pct = (count / metrics['total_partidos']) * 100
        print(f"   {resultado}: {count} ({pct:.1f}%)")
    
    # Guardar a CSV
    output_file = REPORTS / "comparacion_predicciones_realidad.csv"
    df_resultados.to_csv(output_file, index=False)
    print(f"\n✅ Reporte guardado en: {output_file}")
    
    # Guardar métricas
    metrics_file = REPORTS / "metricas_precision.txt"
    with open(metrics_file, 'w', encoding='utf-8') as f:
        f.write("REPORTE DE PRECISIÓN DEL MODELO\n")
        f.write("=" * 70 + "\n\n")
        f.write(f"Total partidos analizados: {metrics['total_partidos']}\n")
        f.write(f"Hit-rate: {metrics['hit_rate']:.2f}%\n")
        f.write(f"Aciertos: {metrics['aciertos']}\n")
        f.write(f"Errores: {metrics['errores']}\n\n")
        f.write("Distribución de predicciones:\n")
        for k, v in metrics['distribucion_predicciones'].items():
            f.write(f"  {k}: {v}\n")
        f.write("\nDistribución de realidad:\n")
        for k, v in metrics['distribucion_realidad'].items():
            f.write(f"  {k}: {v}\n")
    
    print(f"✅ Métricas guardadas en: {metrics_file}")


def main():
    """Función principal"""
    print("\n" + "=" * 70)
    print("  COMPARADOR DE PREDICCIONES vs REALIDAD")
    print("=" * 70)
    
    # 1. Cargar predictor
    print("\n1. Cargando predictor...")
    predictor = PredictorCorregidoSimple()
    print("   OK")
    
    # 2. Cargar datos históricos
    print("\n2. Cargando datos históricos...")
    df_historico = pd.read_parquet(PROC / "matches.parquet")
    print(f"   {len(df_historico)} partidos cargados")
    
    # 3. Filtrar solo partidos con resultados
    df_historico = df_historico[
        df_historico['FTHG'].notna() & 
        df_historico['FTAG'].notna()
    ]
    print(f"   {len(df_historico)} partidos con resultados")
    
    # 4. Comparar predicciones con realidad
    print("\n3. Comparando predicciones con realidad...")
    
    # Usar TODOS los partidos para análisis completo
    print(f"   Usando {len(df_historico)} partidos para análisis completo")
    
    df_resultados = comparar_prediccion_realidad(
        df_historico,
        predictor
    )
    
    # 5. Calcular métricas
    print("\n4. Calculando métricas...")
    metrics = calcular_metricas(df_resultados)
    
    # 6. Generar reporte
    print("\n5. Generando reporte...")
    generar_reporte(df_resultados, metrics)
    
    print("\n" + "=" * 70)
    print("  ANÁLISIS COMPLETADO")
    print("=" * 70)


if __name__ == "__main__":
    main()
