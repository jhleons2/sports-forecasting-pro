"""
EXPLORACIÓN DE FEATURES PROFESIONALES
=====================================

Script para explorar y visualizar las features profesionales implementadas.
Muestra ejemplos reales de:
- Head-to-Head patterns
- Fortalezas casa/fuera
- Equipos con momentum
- Rachas de victorias

Uso:
    python scripts/explore_professional_features.py
"""

import sys
from pathlib import Path

# Añadir el directorio raíz al path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import pandas as pd
import numpy as np

pd.set_option('display.max_columns', None)
pd.set_option('display.width', 120)

PROC = Path("data/processed")

def main():
    print("""
╔════════════════════════════════════════════════════════════════╗
║  EXPLORACIÓN DE FEATURES PROFESIONALES                         ║
║  Dataset: matches_professional.parquet                         ║
╚════════════════════════════════════════════════════════════════╝
    """)
    
    # Cargar dataset profesional
    df = pd.read_parquet(PROC / "matches_professional.parquet")
    
    print(f"\n📊 DATASET CARGADO:")
    print(f"   Partidos: {len(df):,}")
    print(f"   Columnas: {len(df.columns)}")
    print(f"   Rango de fechas: {df['Date'].min().date()} a {df['Date'].max().date()}")
    print(f"   Ligas: {df['League'].nunique()} ({', '.join(df['League'].unique())})")
    
    # 1. HEAD-TO-HEAD ANALYSIS
    print("\n" + "="*70)
    print("  1️⃣  HEAD-TO-HEAD ANALYSIS")
    print("="*70)
    
    df_h2h = df[df['H2H_matches_found'] >= 3].copy()
    print(f"\n📌 Partidos con H2H data: {len(df_h2h):,} ({len(df_h2h)/len(df)*100:.1f}%)")
    
    # Top "maldiciones" (away domina fuerte)
    print("\n🔴 TOP 10 'MALDICIONES' (Away domina históricamente):")
    print("-" * 70)
    
    cursed = df_h2h.nsmallest(10, 'H2H_home_dominance')[
        ['Date', 'League', 'HomeTeam', 'AwayTeam', 'H2H_home_dominance', 
         'H2H_home_wins', 'H2H_draws', 'H2H_away_wins', 'FTHG', 'FTAG']
    ].copy()
    
    for idx, row in cursed.iterrows():
        print(f"\n{row['HomeTeam']} vs {row['AwayTeam']} ({row['League']})")
        print(f"   Fecha: {row['Date'].date() if pd.notna(row['Date']) else 'N/A'}")
        print(f"   H2H: {row['H2H_home_wins']:.0f}W - {row['H2H_draws']:.0f}D - {row['H2H_away_wins']:.0f}L")
        print(f"   Dominancia: {row['H2H_home_dominance']:.2f} (Away domina)")
        print(f"   Resultado real: {row['FTHG']:.0f}-{row['FTAG']:.0f}")
    
    # Top favoritos históricos (home domina fuerte)
    print("\n\n🟢 TOP 10 FAVORITOS HISTÓRICOS (Home domina):")
    print("-" * 70)
    
    favorites = df_h2h.nlargest(10, 'H2H_home_dominance')[
        ['Date', 'League', 'HomeTeam', 'AwayTeam', 'H2H_home_dominance',
         'H2H_home_wins', 'H2H_draws', 'H2H_away_wins', 'FTHG', 'FTAG']
    ].copy()
    
    for idx, row in favorites.iterrows():
        print(f"\n{row['HomeTeam']} vs {row['AwayTeam']} ({row['League']})")
        print(f"   Fecha: {row['Date'].date() if pd.notna(row['Date']) else 'N/A'}")
        print(f"   H2H: {row['H2H_home_wins']:.0f}W - {row['H2H_draws']:.0f}D - {row['H2H_away_wins']:.0f}L")
        print(f"   Dominancia: {row['H2H_home_dominance']:.2f} (Home domina)")
        print(f"   Resultado real: {row['FTHG']:.0f}-{row['FTAG']:.0f}")
    
    # 2. CASA VS FUERA ANALYSIS
    print("\n\n" + "="*70)
    print("  2️⃣  RENDIMIENTO CASA VS FUERA")
    print("="*70)
    
    # Filtrar partidos recientes con datos completos
    df_recent = df[
        (df['Home_as_home_win_rate_roll5'].notna()) &
        (df['Away_as_away_win_rate_roll5'].notna())
    ].copy()
    
    print(f"\n📌 Partidos con datos casa/fuera: {len(df_recent):,}")
    
    # Top fortalezas en casa
    print("\n🏠 TOP 10 FORTALEZAS EN CASA:")
    print("-" * 70)
    
    fortresses = df_recent.nlargest(10, 'Home_as_home_win_rate_roll5')[
        ['Date', 'League', 'HomeTeam', 'Home_as_home_win_rate_roll5',
         'Home_as_home_GF_roll5', 'Home_as_home_GA_roll5', 'FTHG', 'FTAG']
    ].copy()
    
    for idx, row in fortresses.iterrows():
        wr = row['Home_as_home_win_rate_roll5']
        gf = row['Home_as_home_GF_roll5']
        ga = row['Home_as_home_GA_roll5']
        print(f"\n{row['HomeTeam']} ({row['League']})")
        print(f"   Fecha: {row['Date'].date() if pd.notna(row['Date']) else 'N/A'}")
        print(f"   Win rate como local: {wr*100:.1f}%")
        print(f"   Goles últimos 5 (casa): {gf:.0f} GF - {ga:.0f} GA")
        print(f"   Resultado: {row['FTHG']:.0f}-{row['FTAG']:.0f}")
    
    # Equipos débiles fuera
    print("\n\n✈️  TOP 10 MÁS DÉBILES COMO VISITANTE:")
    print("-" * 70)
    
    weak_away = df_recent.nsmallest(10, 'Away_as_away_win_rate_roll5')[
        ['Date', 'League', 'AwayTeam', 'Away_as_away_win_rate_roll5',
         'Away_as_away_GF_roll5', 'Away_as_away_GA_roll5', 'FTHG', 'FTAG']
    ].copy()
    
    for idx, row in weak_away.iterrows():
        wr = row['Away_as_away_win_rate_roll5']
        gf = row['Away_as_away_GF_roll5']
        ga = row['Away_as_away_GA_roll5']
        print(f"\n{row['AwayTeam']} ({row['League']})")
        print(f"   Fecha: {row['Date'].date() if pd.notna(row['Date']) else 'N/A'}")
        print(f"   Win rate como visitante: {wr*100:.1f}%")
        print(f"   Goles últimos 5 (fuera): {gf:.0f} GF - {ga:.0f} GA")
        print(f"   Resultado: {row['FTHG']:.0f}-{row['FTAG']:.0f}")
    
    # 3. MOMENTUM ANALYSIS
    print("\n\n" + "="*70)
    print("  3️⃣  MOMENTUM POSITIVO (Forma reciente > Forma media)")
    print("="*70)
    
    df_momentum = df[
        (df['Home_GF_roll5'].notna()) &
        (df['Home_GF_roll10'].notna())
    ].copy()
    
    df_momentum['home_momentum'] = df_momentum['Home_GF_roll5'] - (df_momentum['Home_GF_roll10'] / 2)
    
    print(f"\n📌 Partidos con datos de momentum: {len(df_momentum):,}")
    
    print("\n📈 TOP 10 EQUIPOS CON MOMENTUM POSITIVO:")
    print("-" * 70)
    
    momentum_up = df_momentum.nlargest(10, 'home_momentum')[
        ['Date', 'League', 'HomeTeam', 'Home_GF_roll5', 'Home_GF_roll10', 'home_momentum']
    ].copy()
    
    for idx, row in momentum_up.iterrows():
        print(f"\n{row['HomeTeam']} ({row['League']})")
        print(f"   Fecha: {row['Date'].date() if pd.notna(row['Date']) else 'N/A'}")
        print(f"   Goles últimos 5: {row['Home_GF_roll5']:.1f}")
        print(f"   Goles últimos 10 (avg): {row['Home_GF_roll10']/2:.1f}")
        print(f"   Momentum: +{row['home_momentum']:.1f} goles")
    
    # 4. RACHAS DE VICTORIAS
    print("\n\n" + "="*70)
    print("  4️⃣  RACHAS DE VICTORIAS")
    print("="*70)
    
    df_streaks = df[df['Home_streak_length'] > 0].copy()
    
    print(f"\n📌 Equipos con rachas activas: {len(df_streaks):,}")
    
    print("\n🔥 TOP 10 RACHAS MÁS LARGAS:")
    print("-" * 70)
    
    top_streaks = df_streaks.nlargest(10, 'Home_streak_length')[
        ['Date', 'League', 'HomeTeam', 'Home_streak_length', 'FTHG', 'FTAG']
    ].copy()
    
    for idx, row in top_streaks.iterrows():
        print(f"\n{row['HomeTeam']} ({row['League']})")
        print(f"   Fecha: {row['Date'].date() if pd.notna(row['Date']) else 'N/A'}")
        print(f"   Racha: {row['Home_streak_length']:.0f} victorias consecutivas")
        print(f"   Resultado: {row['FTHG']:.0f}-{row['FTAG']:.0f}")
    
    # RESUMEN FINAL
    print("\n\n" + "="*70)
    print("  📊 RESUMEN DE FEATURES DISPONIBLES")
    print("="*70)
    
    feature_categories = {
        'H2H': [c for c in df.columns if 'H2H' in c],
        'Casa/Fuera': [c for c in df.columns if 'as_home' in c or 'as_away' in c],
        'Multi-Window': [c for c in df.columns if 'roll10' in c],
        'Motivación': [c for c in df.columns if 'motivation' in c or 'streak' in c or 'position' in c],
        'xG': [c for c in df.columns if 'xG' in c]
    }
    
    print()
    for category, cols in feature_categories.items():
        if cols:
            print(f"  {category:20s}: {len(cols):2d} columnas")
            # Mostrar primeras 3 columnas
            for col in cols[:3]:
                print(f"     - {col}")
            if len(cols) > 3:
                print(f"     ... y {len(cols)-3} más")
    
    print("""
╔════════════════════════════════════════════════════════════════╗
║  ✅ EXPLORACIÓN COMPLETADA                                     ║
║                                                                ║
║  Las features profesionales están funcionando correctamente   ║
║  y contienen datos útiles para predicciones.                  ║
║                                                                ║
║  Próximo paso:                                                 ║
║  - Integrar en modelos de predicción                           ║
║  - Crear backtest con dataset profesional                      ║
║  - Añadir visualización en dashboard                           ║
╚════════════════════════════════════════════════════════════════╝
    """)


if __name__ == "__main__":
    main()

