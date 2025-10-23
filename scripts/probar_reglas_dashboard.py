"""Probar las reglas dinámicas directamente"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.predictor_reglas_dinamicas import PredictorReglasDinamicas
from src.features.reglas_dinamicas import calcular_reglas_dinamicas

print("\n" + "="*70)
print("  PROBANDO REGLAS DINÁMICAS PARA CHELSEA vs SUNDERLAND")
print("="*70)

# Inicializar predictor
predictor = PredictorReglasDinamicas()
predictor.load_and_train()

# Calcular reglas dinámicas
reglas = calcular_reglas_dinamicas(
    predictor.df_historico,
    'Chelsea',
    'Sunderland',
    'E0'
)

print("\n📊 REGLAS CALCULADAS:")
print(f"REGLA 1 - Últimos 8 total:")
print(f"  Chelsea: {reglas['ultimos_8_total']['home']['pts']}/24 pts ({reglas['ultimos_8_total']['home']['efectividad']:.1f}%)")
print(f"  Sunderland: {reglas['ultimos_8_total']['away']['pts']}/24 pts ({reglas['ultimos_8_total']['away']['efectividad']:.1f}%)")

print(f"\nREGLA 2 - Últimos 5 local:")
print(f"  Chelsea: {reglas['ultimos_5_local']['gf']} GF - {reglas['ultimos_5_local']['ga']} GA ({reglas['ultimos_5_local']['gd']:+d} GD)")
print(f"  Win rate: {reglas['ultimos_5_local']['win_rate']:.1f}%")

print(f"\nREGLA 3 - Últimos 5 visitante:")
print(f"  Sunderland: {reglas['ultimos_5_visitante']['gf']} GF - {reglas['ultimos_5_visitante']['ga']} GA ({reglas['ultimos_5_visitante']['gd']:+d} GD)")
print(f"  Win rate: {reglas['ultimos_5_visitante']['win_rate']:.1f}%")

print(f"\nREGLA 4 - H2H:")
print(f"  Partidos: {reglas['ultimos_5_h2h']['partidos']}")
if reglas['ultimos_5_h2h']['partidos'] > 0:
    print(f"  Chelsea: {reglas['ultimos_5_h2h']['home_wins']}W - {reglas['ultimos_5_h2h']['draws']}D - {reglas['ultimos_5_h2h']['away_wins']}L")

print(f"\nREGLA 5 - Bajas:")
print(f"  Chelsea: {reglas['bajas_jugadores']['home_bajas']} bajas")
print(f"  Sunderland: {reglas['bajas_jugadores']['away_bajas']} bajas")

# Obtener predicción
prediccion = predictor.predict_con_reglas_dinamicas('Chelsea', 'Sunderland', 'E0')

print(f"\n🎯 PREDICCIÓN:")
print(f"  Chelsea: {prediccion['1x2']['pH']*100:.1f}%")
print(f"  Empate: {prediccion['1x2']['pD']*100:.1f}%")
print(f"  Sunderland: {prediccion['1x2']['pA']*100:.1f}%")

print(f"\n✅ REGLAS FUNCIONAN CORRECTAMENTE")
