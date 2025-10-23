"""Buscar partido Chelsea vs Sunderland"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd

print("\n" + "="*70)
print("  BUSCANDO PARTIDO CHELSEA vs SUNDERLAND")
print("="*70)

# Cargar fixtures
df = pd.read_parquet('data/processed/upcoming_fixtures.parquet')

print(f"\nTotal de fixtures: {len(df)}")

# Buscar Chelsea
chelsea_matches = df[(df['HomeTeam'].str.contains('Chelsea', na=False, case=False)) | 
                     (df['AwayTeam'].str.contains('Chelsea', na=False, case=False))]

print(f"\nPartidos de Chelsea encontrados: {len(chelsea_matches)}")

if len(chelsea_matches) > 0:
    print("\nPartidos de Chelsea:")
    for i, row in chelsea_matches.iterrows():
        print(f"  Índice {i}: {row['HomeTeam']} vs {row['AwayTeam']} ({row['League']})")
        
        # Verificar si es vs Sunderland
        if 'Sunderland' in str(row['HomeTeam']) or 'Sunderland' in str(row['AwayTeam']):
            print(f"  ✅ ENCONTRADO: Chelsea vs Sunderland en índice {i}")
            print(f"     Liga: {row['League']}")
            print(f"     Fecha: {row['Date']}")
else:
    print("\n❌ No se encontraron partidos de Chelsea")

# Buscar Sunderland
sunderland_matches = df[(df['HomeTeam'].str.contains('Sunderland', na=False, case=False)) | 
                        (df['AwayTeam'].str.contains('Sunderland', na=False, case=False))]

print(f"\nPartidos de Sunderland encontrados: {len(sunderland_matches)}")

if len(sunderland_matches) > 0:
    print("\nPartidos de Sunderland:")
    for i, row in sunderland_matches.iterrows():
        print(f"  Índice {i}: {row['HomeTeam']} vs {row['AwayTeam']} ({row['League']})")

print("\n" + "="*70)
print("  PRIMEROS 10 FIXTURES:")
print("="*70)

for i in range(min(10, len(df))):
    row = df.iloc[i]
    print(f"  {i}: {row['HomeTeam']} vs {row['AwayTeam']} ({row['League']})")
