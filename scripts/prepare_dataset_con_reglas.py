"""
PREPARACIÓN DE DATASET CON REGLAS ESPECÍFICAS
==============================================

Genera dataset siguiendo las 5 reglas exactas:
1. Últimos 8 partidos total (misma liga)
2. Últimos 5 de visitante (misma liga)
3. Últimos 5 de local (misma liga)
4. 5 entre sí (H2H)
5. Bajas de jugadores (placeholder)

Uso:
    python scripts/prepare_dataset_con_reglas.py
"""

import sys
from pathlib import Path

# Añadir el directorio raíz al path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import pandas as pd
from src.etl.prepare_dataset_pro import load_football_data, load_understat_xg, merge_xg
from src.features.ratings import add_elo
from src.features.reglas_analisis import add_reglas_analisis

PROC = Path("data/processed")

def main():
    print("""
╔════════════════════════════════════════════════════════════════╗
║  PREPARACIÓN DE DATASET CON REGLAS ESPECÍFICAS                ║
╚════════════════════════════════════════════════════════════════╝
    """)
    
    # 1. Cargar datos base
    print("\n[PASO 1/4] Cargando datos base...")
    print("-" * 70)
    fd = load_football_data()
    print(f"✅ {len(fd)} partidos cargados")
    
    # 2. Merge xG
    print("\n[PASO 2/4] Merge con xG (opcional)...")
    print("-" * 70)
    uxg = load_understat_xg()
    df = merge_xg(fd, uxg)
    
    if uxg is not None:
        xg_count = df['xG_home'].notna().sum()
        print(f"✅ xG disponible: {xg_count}/{len(df)} ({xg_count/len(df)*100:.1f}%)")
    else:
        print("⚠️  xG no disponible")
    
    # 3. Features base (ELO)
    print("\n[PASO 3/4] Añadiendo ELO ratings...")
    print("-" * 70)
    df = add_elo(df)
    print("✅ ELO ratings añadidos")
    
    # 4. APLICAR REGLAS ESPECÍFICAS
    print("\n[PASO 4/4] Aplicando TUS 5 REGLAS...")
    print("-" * 70)
    df = add_reglas_analisis(df)
    
    # 5. Guardar
    print("\n" + "=" * 70)
    print("  GUARDANDO DATASET")
    print("=" * 70)
    
    PROC.mkdir(parents=True, exist_ok=True)
    output_file = PROC / "matches_con_reglas.parquet"
    df.to_parquet(output_file, index=False)
    
    print(f"\n✅ Dataset con reglas guardado:")
    print(f"   Archivo: {output_file}")
    print(f"   Partidos: {len(df)}")
    print(f"   Columnas: {len(df.columns)}")
    print(f"   Tamaño: {output_file.stat().st_size / 1024 / 1024:.2f} MB")
    
    # Resumen de columnas por regla
    print("\n" + "-" * 70)
    print("COLUMNAS POR REGLA:")
    print("-" * 70)
    
    reglas = {
        'REGLA 1 (Últimos 8 total)': [c for c in df.columns if 'ultimos8_liga' in c],
        'REGLA 2 (Últimos 5 local)': [c for c in df.columns if 'local5_liga' in c],
        'REGLA 3 (Últimos 5 visitante)': [c for c in df.columns if 'visitante5_liga' in c],
        'REGLA 4 (H2H 5)': [c for c in df.columns if 'H2H5' in c],
        'REGLA 5 (Bajas)': [c for c in df.columns if 'jugadores' in c or 'suspendidos' in c]
    }
    
    for regla, cols in reglas.items():
        if cols:
            print(f"\n  {regla}:")
            print(f"    {len(cols)} columnas")
            for col in cols[:3]:
                print(f"      - {col}")
            if len(cols) > 3:
                print(f"      ... y {len(cols)-3} más")
    
    print("\n" + "=" * 70)
    print("  ✅ DATASET CON REGLAS LISTO")
    print("=" * 70)
    print("""
    Próximo paso:
    
    # Probar análisis de un partido
    python scripts/test_analisis_con_reglas.py
    
    # O integrar en dashboard
    # Modificar app_argon.py para usar este dataset
    """)


if __name__ == "__main__":
    main()

