"""
DEMOSTRACIÓN DE JUSTIFICACIÓN DE PORCENTAJES
============================================

Este script muestra cómo el sistema justifica los porcentajes
de predicción basándose en las 5 reglas dinámicas.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.predictor_reglas_dinamicas_corregido_simple import PredictorReglasDinamicasCorregido

def mostrar_justificacion(equipo_home, equipo_away, liga='E0'):
    """Muestra la justificación completa de una predicción"""
    
    print("\n" + "="*80)
    print(f"  PREDICCIÓN CON JUSTIFICACIÓN: {equipo_home} vs {equipo_away}")
    print("="*80)
    
    # Crear predictor
    predictor = PredictorReglasDinamicasCorregido()
    predictor.load_and_train()
    
    # Hacer predicción
    resultado = predictor.predict_con_reglas_dinamicas(equipo_home, equipo_away, liga)
    reglas = resultado['reglas']
    
    # Mostrar porcentajes
    print(f"\n🎯 PREDICCIÓN:")
    print(f"   {equipo_home}: {resultado['1x2']['pH']*100:.1f}%")
    print(f"   Empate: {resultado['1x2']['pD']*100:.1f}%")
    print(f"   {equipo_away}: {resultado['1x2']['pA']*100:.1f}%")
    
    # Justificación
    print(f"\n" + "="*80)
    print("  ¿POR QUÉ ESTOS PORCENTAJES?")
    print("="*80)
    
    # Regla 1
    print(f"\n📊 REGLA 1: Forma reciente (últimos 8 partidos)")
    print(f"   {equipo_home}: {reglas['ultimos_8_total']['home']['pts']}/24 pts ({reglas['ultimos_8_total']['home']['efectividad']:.1f}%)")
    print(f"   {equipo_away}: {reglas['ultimos_8_total']['away']['pts']}/24 pts ({reglas['ultimos_8_total']['away']['efectividad']:.1f}%)")
    
    diferencia = reglas['ultimos_8_total']['home']['pts'] - reglas['ultimos_8_total']['away']['pts']
    if diferencia > 0:
        print(f"   → {equipo_home} tiene MEJOR forma (+{diferencia} pts)")
    elif diferencia < 0:
        print(f"   → {equipo_away} tiene MEJOR forma ({diferencia} pts)")
    else:
        print(f"   → Ambos equipos tienen forma SIMILAR")
    
    # Regla 2
    print(f"\n🏠 REGLA 2: Rendimiento local")
    print(f"   {equipo_home} en casa: {reglas['ultimos_5_local']['gf']} GF - {reglas['ultimos_5_local']['ga']} GA")
    print(f"   Goal difference: {reglas['ultimos_5_local']['gd']:+d}")
    print(f"   Win rate: {reglas['ultimos_5_local']['win_rate']:.1f}%")
    
    if reglas['ultimos_5_local']['win_rate'] >= 60:
        print(f"   → {equipo_home} es MUY FUERTE en casa")
    elif reglas['ultimos_5_local']['win_rate'] >= 40:
        print(f"   → {equipo_home} es REGULAR en casa")
    else:
        print(f"   → {equipo_home} es DÉBIL en casa")
    
    # Regla 3
    print(f"\n✈️  REGLA 3: Rendimiento visitante")
    print(f"   {equipo_away} fuera: {reglas['ultimos_5_visitante']['gf']} GF - {reglas['ultimos_5_visitante']['ga']} GA")
    print(f"   Goal difference: {reglas['ultimos_5_visitante']['gd']:+d}")
    print(f"   Win rate: {reglas['ultimos_5_visitante']['win_rate']:.1f}%")
    
    if reglas['ultimos_5_visitante']['win_rate'] >= 60:
        print(f"   → {equipo_away} es MUY FUERTE fuera")
    elif reglas['ultimos_5_visitante']['win_rate'] >= 40:
        print(f"   → {equipo_away} es REGULAR fuera")
    else:
        print(f"   → {equipo_away} es DÉBIL fuera")
    
    # Regla 4
    print(f"\n🔄 REGLA 4: Enfrentamientos directos (H2H)")
    if reglas['ultimos_5_h2h']['partidos'] > 0:
        print(f"   Partidos encontrados: {reglas['ultimos_5_h2h']['partidos']}")
        print(f"   {equipo_home}: {reglas['ultimos_5_h2h']['home_wins']}W - {reglas['ultimos_5_h2h']['draws']}D - {reglas['ultimos_5_h2h']['away_wins']}L")
        
        if reglas['ultimos_5_h2h']['dominancia'] > 0.2:
            print(f"   → {equipo_home} DOMINA el H2H")
        elif reglas['ultimos_5_h2h']['dominancia'] < -0.2:
            print(f"   → {equipo_away} DOMINA el H2H")
        else:
            print(f"   → Enfrentamientos EQUILIBRADOS")
    else:
        print(f"   Sin enfrentamientos previos recientes")
    
    # Regla 5
    print(f"\n🚑 REGLA 5: Bajas de jugadores")
    print(f"   {equipo_home}: {reglas['bajas_jugadores']['home_bajas']} bajas")
    print(f"   {equipo_away}: {reglas['bajas_jugadores']['away_bajas']} bajas")
    if reglas['bajas_jugadores']['home_bajas'] == 0 and reglas['bajas_jugadores']['away_bajas'] == 0:
        print(f"   → Ambos equipos SIN bajas importantes")
    
    # Conclusión
    print(f"\n" + "="*80)
    print("  CONCLUSIÓN:")
    print("="*80)
    
    favorito = None
    if resultado['1x2']['pH'] > resultado['1x2']['pD'] and resultado['1x2']['pH'] > resultado['1x2']['pA']:
        favorito = equipo_home
        prob = resultado['1x2']['pH']*100
    elif resultado['1x2']['pA'] > resultado['1x2']['pH'] and resultado['1x2']['pA'] > resultado['1x2']['pD']:
        favorito = equipo_away
        prob = resultado['1x2']['pA']*100
    else:
        favorito = "Empate"
        prob = resultado['1x2']['pD']*100
    
    print(f"\n🏆 FAVORITO: {favorito} ({prob:.1f}%)")
    
    if favorito != "Empate":
        print(f"\n📝 RAZONES:")
        if favorito == equipo_home:
            if diferencia > 0:
                print(f"   ✅ Mejor forma reciente (+{diferencia} pts)")
            if reglas['ultimos_5_local']['win_rate'] >= 40:
                print(f"   ✅ Buen rendimiento en casa ({reglas['ultimos_5_local']['win_rate']:.1f}%)")
            if reglas['ultimos_5_visitante']['win_rate'] < 40:
                print(f"   ✅ Rival débil fuera ({reglas['ultimos_5_visitante']['win_rate']:.1f}%)")
        else:
            if diferencia < 0:
                print(f"   ✅ Mejor forma reciente ({abs(diferencia)} pts ventaja)")
            if reglas['ultimos_5_visitante']['win_rate'] >= 40:
                print(f"   ✅ Buen rendimiento fuera ({reglas['ultimos_5_visitante']['win_rate']:.1f}%)")
            if reglas['ultimos_5_local']['win_rate'] < 40:
                print(f"   ✅ Rival débil en casa ({reglas['ultimos_5_local']['win_rate']:.1f}%)")
    
    print(f"\n🎯 Predicción calculada dinámicamente desde {reglas['fecha_calculo']}")
    print(f"✅ Basada 100% en TUS 5 REGLAS DINÁMICAS")
    
    print(f"\n" + "="*80)
    print(f"  Ver en dashboard: http://localhost:5000/predict/{liga}/[índice]")
    print("="*80)

if __name__ == "__main__":
    # Ejemplo 1: Newcastle vs Fulham
    mostrar_justificacion('Newcastle United FC', 'Fulham FC', 'E0')
    
    # Ejemplo 2: Chelsea vs Sunderland
    print("\n\n")
    mostrar_justificacion('Chelsea FC', 'Sunderland AFC', 'E0')
