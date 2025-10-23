"""Verificar predicción Chelsea vs Sunderland"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.predictor_reglas_dinamicas import PredictorReglasDinamicas

print("\n" + "="*70)
print("  VERIFICACIÓN: Chelsea vs Sunderland")
print("="*70)

predictor = PredictorReglasDinamicas()
predictor.load_and_train()

resultado = predictor.predict_con_reglas_dinamicas('Chelsea', 'Sunderland', 'E0')

print("\n1X2:")
print(f"  GANA LOCAL")
print(f"  {resultado['1x2']['pH']*100:.1f}%")
print(f"  Chelsea FC (Local)")
print()
print(f"  EMPATE")
print(f"  {resultado['1x2']['pD']*100:.1f}%")
print(f"  Empate")
print()
print(f"  GANA VISITANTE")
print(f"  {resultado['1x2']['pA']*100:.1f}%")
print(f"  Sunderland AFC (Visitante)")

print("\n" + "="*70)
print("  JUSTIFICACIÓN (REGLAS DINÁMICAS desde HOY):")
print("="*70)

r = resultado['reglas']

print(f"\n📊 REGLA 1: Últimos 8 total")
print(f"   Chelsea: {r['ultimos_8_total']['home']['pts']}/24 pts ({r['ultimos_8_total']['home']['efectividad']:.1f}%)")
print(f"   Sunderland: {r['ultimos_8_total']['away']['pts']}/24 pts ({r['ultimos_8_total']['away']['efectividad']:.1f}%)")

print(f"\n🏠 REGLA 2: Últimos 5 local")
print(f"   Chelsea: {r['ultimos_5_local']['gf']} GF - {r['ultimos_5_local']['ga']} GA ({r['ultimos_5_local']['gd']:+d} GD)")
print(f"   Win rate: {r['ultimos_5_local']['win_rate']:.1f}%")

print(f"\n✈️  REGLA 3: Últimos 5 visitante")
print(f"   Sunderland: {r['ultimos_5_visitante']['gf']} GF - {r['ultimos_5_visitante']['ga']} GA ({r['ultimos_5_visitante']['gd']:+d} GD)")
print(f"   Win rate: {r['ultimos_5_visitante']['win_rate']:.1f}%")

print(f"\n🔄 REGLA 4: H2H")
print(f"   Partidos: {r['ultimos_5_h2h']['partidos']}")
if r['ultimos_5_h2h']['partidos'] > 0:
    print(f"   Chelsea: {r['ultimos_5_h2h']['home_wins']}W - {r['ultimos_5_h2h']['draws']}D - {r['ultimos_5_h2h']['away_wins']}L")
    print(f"   Dominancia: {r['ultimos_5_h2h']['dominancia']:+.2f}")

print("\n" + "="*70)
print("  ANÁLISIS:")
print("="*70)

suma = resultado['1x2']['pH'] + resultado['1x2']['pD'] + resultado['1x2']['pA']
print(f"\nSuma de probabilidades: {suma:.4f} {'✅ CORRECTO' if abs(suma - 1.0) < 0.01 else '❌ ERROR'}")

# Análisis de lógica
if resultado['1x2']['pA'] > resultado['1x2']['pH']:
    print(f"\n⚠️  VISITANTE MÁS PROBABLE QUE LOCAL")
    print(f"   Sunderland ({resultado['1x2']['pA']*100:.1f}%) > Chelsea ({resultado['1x2']['pH']*100:.1f}%)")
    print(f"\n   Razones posibles:")
    if r['ultimos_8_total']['away']['pts'] > r['ultimos_8_total']['home']['pts']:
        print(f"   ✅ Sunderland mejor forma últimos 8 ({r['ultimos_8_total']['away']['pts']} vs {r['ultimos_8_total']['home']['pts']} pts)")
    if r['ultimos_5_visitante']['win_rate'] > r['ultimos_5_local']['win_rate']:
        print(f"   ✅ Sunderland mejor fuera ({r['ultimos_5_visitante']['win_rate']:.0f}%) que Chelsea en casa ({r['ultimos_5_local']['win_rate']:.0f}%)")
    if r['ultimos_5_h2h']['home_wins'] < r['ultimos_5_h2h']['away_wins']:
        print(f"   ✅ Sunderland domina H2H ({r['ultimos_5_h2h']['away_wins']} vs {r['ultimos_5_h2h']['home_wins']})")

