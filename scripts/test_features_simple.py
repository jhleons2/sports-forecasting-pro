"""
TEST SIMPLIFICADO DE FEATURES PROFESIONALES
===========================================

Valida que las features profesionales funcionan correctamente.
"""

import sys
from pathlib import Path

# Añadir el directorio raíz al path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import pandas as pd
import numpy as np

print("""
╔════════════════════════════════════════════════════════════╗
║  TEST DE FEATURES PROFESIONALES - Versión Simplificada    ║
╚════════════════════════════════════════════════════════════╝
""")

PROC = Path("data/processed")

# Test 1: Cargar dataset base
print("\n[TEST 1] Cargando dataset base...")
try:
    df = pd.read_parquet(PROC / "matches.parquet")
    print(f"✅ Dataset cargado: {len(df)} partidos, {len(df.columns)} columnas")
except Exception as e:
    print(f"❌ ERROR: {e}")
    sys.exit(1)

# Test 2: Importar módulo de features profesionales
print("\n[TEST 2] Importando módulo de features profesionales...")
try:
    from src.features.professional_features import (
        add_head_to_head_features,
        add_home_away_separated_form,
        add_multi_window_form,
        add_motivation_context,
        add_all_professional_features
    )
    print("✅ Módulo importado correctamente")
except Exception as e:
    print(f"❌ ERROR: {e}")
    sys.exit(1)

# Test 3: Añadir H2H features
print("\n[TEST 3] Añadiendo H2H features...")
try:
    df_test = df.head(100).copy()  # Solo primeros 100 para velocidad
    df_test = add_head_to_head_features(df_test, n_matches=5)
    
    h2h_cols = [c for c in df_test.columns if 'H2H' in c]
    matches_with_h2h = (df_test['H2H_matches_found'] > 0).sum()
    
    print(f"✅ H2H features añadidos: {len(h2h_cols)} columnas")
    print(f"   Partidos con H2H data: {matches_with_h2h}/{len(df_test)}")
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Añadir Casa/Fuera separado
print("\n[TEST 4] Añadiendo Casa/Fuera separado...")
try:
    df_test = df.head(100).copy()
    df_test = add_home_away_separated_form(df_test, window=5)
    
    ha_cols = [c for c in df_test.columns if 'as_home' in c or 'as_away' in c]
    
    print(f"✅ Casa/Fuera features añadidos: {len(ha_cols)} columnas")
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 5: Añadir múltiples ventanas
print("\n[TEST 5] Añadiendo múltiples ventanas...")
try:
    df_test = df.head(100).copy()
    
    # Primero necesitamos añadir ELO y rolling básico
    from src.features.ratings import add_elo
    from src.features.rolling import add_form
    
    df_test = add_elo(df_test)
    df_test = add_form(df_test, window=5)
    df_test = add_multi_window_form(df_test, windows=[5, 10])
    
    mw_cols = [c for c in df_test.columns if 'roll10' in c]
    
    print(f"✅ Multi-window features añadidos: {len(mw_cols)} columnas")
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 6: Añadir motivación
print("\n[TEST 6] Añadiendo motivación y streaks...")
try:
    df_test = df.head(100).copy()
    df_test = add_motivation_context(df_test)
    
    mot_cols = [c for c in df_test.columns if 'motivation' in c or 'streak' in c or 'position' in c]
    
    print(f"✅ Motivación features añadidos: {len(mot_cols)} columnas")
    
    # Mostrar algunos streaks
    streaks = df_test[df_test['Home_streak_length'] > 0][['HomeTeam', 'Home_streak_length']].drop_duplicates()
    if len(streaks) > 0:
        print(f"   Ejemplo de streaks encontrados: {len(streaks)}")
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 7: Función maestra (todas las features)
print("\n[TEST 7] Añadiendo TODAS las features profesionales...")
try:
    df_test = df.head(50).copy()  # Solo 50 para velocidad
    
    # Añadir ELO y rolling base primero
    from src.features.ratings import add_elo
    from src.features.rolling import add_form
    
    df_test = add_elo(df_test)
    df_test = add_form(df_test, window=5)
    
    cols_antes = len(df_test.columns)
    
    df_test = add_all_professional_features(
        df_test,
        h2h_matches=5,
        form_window=5,
        multi_windows=[5, 10],
        enable_xg=True
    )
    
    cols_despues = len(df_test.columns)
    cols_nuevas = cols_despues - cols_antes
    
    print(f"✅ Función maestra completada")
    print(f"   Columnas antes: {cols_antes}")
    print(f"   Columnas después: {cols_despues}")
    print(f"   Columnas añadidas: {cols_nuevas}")
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Resumen final
print("\n" + "=" * 70)
print("  RESUMEN DE TESTS")
print("=" * 70)
print("""
✅ TEST 1: Dataset base - PASS
✅ TEST 2: Importar módulo - PASS
✅ TEST 3: H2H features - PASS
✅ TEST 4: Casa/Fuera separado - PASS
✅ TEST 5: Multi-window - PASS
✅ TEST 6: Motivación - PASS
✅ TEST 7: Función maestra - PASS

Total: 7/7 tests exitosos
""")

print("🎉 FEATURES PROFESIONALES VALIDADOS")
print("   Listos para generar dataset completo")

print("""
╔════════════════════════════════════════════════════════════╗
║  PRÓXIMO PASO                                              ║
║  python scripts/prepare_dataset_professional.py            ║
╚════════════════════════════════════════════════════════════╝
""")

