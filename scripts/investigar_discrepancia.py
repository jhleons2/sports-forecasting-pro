"""Verificar discrepancia entre dashboard y sistema"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.predictor_reglas_dinamicas import PredictorReglasDinamicas

print("\n" + "="*70)
print("  INVESTIGACIÓN: Dashboard vs Sistema")
print("="*70)

print("\n📊 Dashboard muestra:")
print("   Chelsea: 24.3%")
print("   Empate: 23.2%")
print("   Sunderland: 52.6%")

predictor = PredictorReglasDinamicas()
predictor.load_and_train()

resultado = predictor.predict_con_reglas_dinamicas('Chelsea', 'Sunderland', 'E0')

print("\n🔧 Sistema calcula:")
print(f"   Chelsea: {resultado['1x2']['pH']*100:.1f}%")
print(f"   Empate: {resultado['1x2']['pD']*100:.1f}%")
print(f"   Sunderland: {resultado['1x2']['pA']*100:.1f}%")

print("\n" + "="*70)
print("  ANÁLISIS DE DISCREPANCIA:")
print("="*70)

# Verificar si coinciden
chelsea_diff = abs(resultado['1x2']['pH']*100 - 24.3)
empate_diff = abs(resultado['1x2']['pD']*100 - 23.2)
sunderland_diff = abs(resultado['1x2']['pA']*100 - 52.6)

print(f"\nDiferencias:")
print(f"   Chelsea: {chelsea_diff:.1f} puntos")
print(f"   Empate: {empate_diff:.1f} puntos")
print(f"   Sunderland: {sunderland_diff:.1f} puntos")

if chelsea_diff < 0.1 and empate_diff < 0.1 and sunderland_diff < 0.1:
    print("\n✅ COINCIDEN - Dashboard usa sistema correcto")
else:
    print("\n❌ NO COINCIDEN - Dashboard usa sistema diferente")
    print("\n🔍 Posibles causas:")
    print("   1. Dashboard usa app_argon.py (sistema viejo)")
    print("   2. Dashboard usa app_argon_con_reglas.py (sistema nuevo)")
    print("   3. Cache de datos antiguos")
    print("   4. Modelos diferentes")

print("\n" + "="*70)
print("  VERIFICAR QUÉ APP ESTÁ CORRIENDO:")
print("="*70)

import os
import psutil

# Buscar procesos Python corriendo
python_processes = []
for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
    try:
        if 'python' in proc.info['name'].lower():
            cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
            if 'app_argon' in cmdline:
                python_processes.append({
                    'pid': proc.info['pid'],
                    'cmdline': cmdline
                })
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass

if python_processes:
    print(f"\n🔍 Procesos Flask encontrados:")
    for proc in python_processes:
        print(f"   PID {proc['pid']}: {proc['cmdline']}")
        
        if 'app_argon_con_reglas.py' in proc['cmdline']:
            print(f"   ✅ CORRECTO: Usando sistema con reglas dinámicas")
        elif 'app_argon.py' in proc['cmdline']:
            print(f"   ❌ PROBLEMA: Usando sistema viejo sin reglas")
else:
    print("\n⚠️  No se encontraron procesos Flask corriendo")

print("\n" + "="*70)
print("  SOLUCIÓN:")
print("="*70)

print("\n1. Detener dashboard actual:")
print("   Ctrl+C en terminal donde corre Flask")

print("\n2. Ejecutar sistema correcto:")
print("   python app_argon_con_reglas.py")

print("\n3. Verificar en:")
print("   http://localhost:5000")

print("\n4. Debería mostrar:")
print("   Chelsea: ~89% (no 24.3%)")
print("   Sunderland: ~4% (no 52.6%)")
