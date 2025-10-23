"""Verificar estructura de reglas"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.predictor_reglas_dinamicas import PredictorReglasDinamicas
from src.features.reglas_dinamicas import calcular_reglas_dinamicas

print("\n" + "="*70)
print("  VERIFICANDO ESTRUCTURA DE REGLAS")
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

print("\n📊 ESTRUCTURA COMPLETA DE REGLAS:")
print(f"Claves principales: {list(reglas.keys())}")

for clave, valor in reglas.items():
    print(f"\n{clave}:")
    if isinstance(valor, dict):
        for subclave, subvalor in valor.items():
            print(f"  {subclave}: {subvalor}")
    else:
        print(f"  {valor}")

print(f"\n✅ ESTRUCTURA VERIFICADA")
