"""
PREPARACIÓN DE DATASET CON FEATURES PROFESIONALES
=================================================

Versión mejorada de prepare_dataset_pro.py que incluye:
✅ Todas las features originales (ELO, rolling básico, xG)
✅ NUEVAS features profesionales:
   - Head-to-Head (H2H)
   - Rendimiento Casa/Fuera separado
   - Múltiples ventanas temporales (5, 10, 15)
   - Motivación y streaks
   - xG rolling avanzado

Uso:
    python scripts/prepare_dataset_professional.py
    
Genera:
    data/processed/matches_professional.parquet
"""

import sys
from pathlib import Path

# Añadir el directorio raíz al path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import pandas as pd
from src.etl.prepare_dataset_pro import load_football_data, load_understat_xg, merge_xg
from src.features.ratings import add_elo
from src.features.rolling import add_form
from src.features.professional_features import add_all_professional_features

PROC = Path("data/processed")

def main():
    print("\n" + "=" * 70)
    print("  PREPARACIÓN DE DATASET PROFESIONAL")
    print("=" * 70)
    
    # 1. Cargar datos base
    print("\n[PASO 1/4] Cargando datos base...")
    print("-" * 70)
    fd = load_football_data()
    print(f"✅ {len(fd)} partidos cargados de Football-Data")
    
    # 2. Merge xG (opcional)
    print("\n[PASO 2/4] Merge con xG (Understat)...")
    print("-" * 70)
    uxg = load_understat_xg()
    df = merge_xg(fd, uxg)
    
    if uxg is not None:
        xg_count = df['xG_home'].notna().sum()
        print(f"✅ xG disponible para {xg_count}/{len(df)} partidos ({xg_count/len(df)*100:.1f}%)")
    else:
        print("⚠️  xG no disponible (Understat)")
    
    # 3. Features originales (ELO + Rolling básico)
    print("\n[PASO 3/4] Features originales...")
    print("-" * 70)
    print("  - Añadiendo ELO ratings...")
    df = add_elo(df)
    print("  - Añadiendo rolling form (ventana 5)...")
    df = add_form(df, window=5)
    print(f"✅ Features originales añadidos")
    
    # 4. NUEVAS Features Profesionales
    print("\n[PASO 4/4] FEATURES PROFESIONALES...")
    print("-" * 70)
    df = add_all_professional_features(
        df,
        h2h_matches=5,           # Últimos 5 enfrentamientos directos
        form_window=5,           # Forma casa/fuera últimos 5
        multi_windows=[5, 10],   # Ventanas 5 y 10 (15 opcional si tienes muchos datos)
        enable_xg=True           # xG rolling si disponible
    )
    
    # 5. Guardar dataset profesional
    print("\n" + "=" * 70)
    print("  GUARDANDO DATASET")
    print("=" * 70)
    
    PROC.mkdir(parents=True, exist_ok=True)
    output_file = PROC / "matches_professional.parquet"
    df.to_parquet(output_file, index=False)
    
    print(f"\n✅ Dataset profesional guardado:")
    print(f"   Archivo: {output_file}")
    print(f"   Partidos: {len(df)}")
    print(f"   Columnas: {len(df.columns)}")
    print(f"   Tamaño: {output_file.stat().st_size / 1024 / 1024:.2f} MB")
    
    # Resumen de features disponibles
    print("\n" + "-" * 70)
    print("RESUMEN DE FEATURES:")
    print("-" * 70)
    
    feature_categories = {
        'Básicas': ['Date', 'HomeTeam', 'AwayTeam', 'FTHG', 'FTAG', 'League'],
        'Odds': [c for c in df.columns if 'B365' in c or 'Avg' in c],
        'ELO': [c for c in df.columns if 'Elo' in c],
        'Rolling Básico': [c for c in df.columns if 'roll5' in c and 'as_' not in c],
        'H2H': [c for c in df.columns if 'H2H' in c],
        'Casa/Fuera': [c for c in df.columns if 'as_home' in c or 'as_away' in c],
        'Multi-Window': [c for c in df.columns if 'roll10' in c or 'roll15' in c],
        'Motivación': [c for c in df.columns if 'motivation' in c or 'streak' in c or 'position' in c],
        'xG': [c for c in df.columns if 'xG' in c]
    }
    
    for category, cols in feature_categories.items():
        if cols:
            print(f"  {category:20s}: {len(cols):3d} columnas")
    
    print("\n" + "=" * 70)
    print("  ✅ DATASET PROFESIONAL LISTO")
    print("=" * 70)
    print("""
    Siguiente paso:
    
    # Backtest con dataset profesional
    python scripts/backtest_optimal_ah_professional.py
    
    # O usar el dataset en predicciones
    python scripts/predict_matches_professional.py
    """)


if __name__ == "__main__":
    main()

