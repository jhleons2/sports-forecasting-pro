"""Mostrar reglas dinámicas para Chelsea vs Sunderland"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.predictor_reglas_dinamicas import PredictorReglasDinamicas
from src.features.reglas_dinamicas import calcular_reglas_dinamicas

print("\n" + "="*80)
print("  CHELSEA vs SUNDERLAND - TUS 5 REGLAS DINÁMICAS")
print("="*80)

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

# Obtener predicción
prediccion = predictor.predict_con_reglas_dinamicas('Chelsea', 'Sunderland', 'E0')

print(f"\n📅 Fecha de cálculo: {reglas['fecha_calculo']}")
print(f"🏆 Partido: {reglas['partido']} ({reglas['liga']})")

print(f"\n🎯 PREDICCIÓN FINAL:")
print(f"   Chelsea (Local): {prediccion['1x2']['pH']*100:.1f}%")
print(f"   Empate: {prediccion['1x2']['pD']*100:.1f}%")
print(f"   Sunderland (Visitante): {prediccion['1x2']['pA']*100:.1f}%")

print(f"\n" + "="*80)
print("  JUSTIFICACIÓN POR TUS 5 REGLAS:")
print("="*80)

print(f"\n📊 REGLA 1: Últimos 8 partidos total (misma liga)")
print(f"   Chelsea: {reglas['ultimos_8_total']['home']['pts']}/24 pts ({reglas['ultimos_8_total']['home']['efectividad']:.1f}%)")
print(f"   Sunderland: {reglas['ultimos_8_total']['away']['pts']}/24 pts ({reglas['ultimos_8_total']['away']['efectividad']:.1f}%)")
print(f"   → Chelsea tiene mejor forma (+{reglas['ultimos_8_total']['home']['pts'] - reglas['ultimos_8_total']['away']['pts']} pts)")

print(f"\n🏠 REGLA 2: Últimos 5 como local (misma liga)")
print(f"   Chelsea en casa: {reglas['ultimos_5_local']['gf']} GF - {reglas['ultimos_5_local']['ga']} GA ({reglas['ultimos_5_local']['gd']:+d} GD)")
print(f"   Win rate: {reglas['ultimos_5_local']['win_rate']:.1f}%")
print(f"   → Chelsea es {'MUY FUERTE' if reglas['ultimos_5_local']['win_rate'] >= 60 else 'REGULAR' if reglas['ultimos_5_local']['win_rate'] >= 40 else 'DÉBIL'} en casa")

print(f"\n✈️  REGLA 3: Últimos 5 como visitante (misma liga)")
print(f"   Sunderland fuera: {reglas['ultimos_5_visitante']['gf']} GF - {reglas['ultimos_5_visitante']['ga']} GA ({reglas['ultimos_5_visitante']['gd']:+d} GD)")
print(f"   Win rate: {reglas['ultimos_5_visitante']['win_rate']:.1f}%")
print(f"   → Sunderland es {'MUY FUERTE' if reglas['ultimos_5_visitante']['win_rate'] >= 60 else 'REGULAR' if reglas['ultimos_5_visitante']['win_rate'] >= 40 else 'DÉBIL'} fuera")

print(f"\n🔄 REGLA 4: Últimos 5 entre sí (H2H)")
print(f"   Partidos encontrados: {reglas['ultimos_5_h2h']['partidos']}")
if reglas['ultimos_5_h2h']['partidos'] > 0:
    print(f"   Chelsea: {reglas['ultimos_5_h2h']['home_wins']}W - {reglas['ultimos_5_h2h']['draws']}D - {reglas['ultimos_5_h2h']['away_wins']}L")
    print(f"   → {'Chelsea domina' if reglas['ultimos_5_h2h']['dominancia'] > 0.2 else 'Sunderland domina' if reglas['ultimos_5_h2h']['dominancia'] < -0.2 else 'Equilibrado'}")
else:
    print(f"   → Sin historial reciente")

print(f"\n🚑 REGLA 5: Bajas de jugadores")
print(f"   Chelsea: {reglas['bajas_jugadores']['home_bajas']} bajas")
print(f"   Sunderland: {reglas['bajas_jugadores']['away_bajas']} bajas")
print(f"   → {'Sin bajas importantes' if reglas['bajas_jugadores']['home_bajas'] == 0 and reglas['bajas_jugadores']['away_bajas'] == 0 else 'Hay bajas importantes'}")

print(f"\n" + "="*80)
print("  CONCLUSIÓN:")
print("="*80)

if prediccion['1x2']['pH'] > prediccion['1x2']['pA']:
    favorito = "Chelsea"
    porcentaje = prediccion['1x2']['pH']*100
    razon = "Mejor forma últimos 8 + Fuerte en casa"
elif prediccion['1x2']['pA'] > prediccion['1x2']['pH']:
    favorito = "Sunderland"
    porcentaje = prediccion['1x2']['pA']*100
    razon = "Mejor forma últimos 8 + Fuerte fuera"
else:
    favorito = "Empate"
    porcentaje = prediccion['1x2']['pD']*100
    razon = "Equilibrio entre equipos"

print(f"\n🏆 FAVORITO: {favorito} ({porcentaje:.1f}%)")
print(f"📝 RAZÓN: {razon}")

print(f"\n✅ PREDICCIÓN BASADA EN TUS 5 REGLAS DINÁMICAS")
print(f"   Calculado desde HOY ({reglas['fecha_calculo']})")
print(f"   Sistema: 100% dinámico y actualizado")
