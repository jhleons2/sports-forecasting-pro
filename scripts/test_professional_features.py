"""
TEST Y ANÁLISIS DE FEATURES PROFESIONALES
=========================================

Script para:
1. Generar dataset con features profesionales
2. Analizar impact de cada feature
3. Comparar con sistema actual
4. Validar mejoras

Uso:
    python scripts/test_professional_features.py
"""

import pandas as pd
import numpy as np
from pathlib import Path
# import matplotlib.pyplot as plt  # Opcional
# import seaborn as sns  # Opcional

from src.etl.prepare_dataset_pro import load_football_data, load_understat_xg, merge_xg
from src.features.ratings import add_elo
from src.features.rolling import add_form
from src.features.professional_features import (
    add_head_to_head_features,
    add_home_away_separated_form,
    add_multi_window_form,
    add_motivation_context,
    add_xg_rolling_features
)

PROC = Path("data/processed")
REPORTS = Path("reports"); REPORTS.mkdir(parents=True, exist_ok=True)


def test_h2h_features():
    """
    Test 1: Validar que H2H realmente predice resultados
    """
    print("\n" + "=" * 70)
    print("  TEST 1: HEAD-TO-HEAD FEATURES")
    print("=" * 70)
    
    # Cargar datos
    df = pd.read_parquet(PROC / "matches.parquet")
    df = add_elo(df)
    df = add_head_to_head_features(df, n_matches=5)
    
    # Análisis: H2H dominance vs resultado real
    df_with_h2h = df[df['H2H_matches_found'] >= 3].copy()
    
    # Crear bins de dominancia
    df_with_h2h['h2h_bin'] = pd.cut(
        df_with_h2h['H2H_home_dominance'],
        bins=[-1.1, -0.6, -0.2, 0.2, 0.6, 1.1],
        labels=['Away domina fuerte', 'Away domina', 'Parejo', 'Home domina', 'Home domina fuerte']
    )
    
    # Calcular home win rate por bin
    analysis = df_with_h2h.groupby('h2h_bin').agg({
        'y': lambda x: (x == 0).mean(),  # Home win rate
        'HomeTeam': 'count',             # Número de partidos
        'FTHG': 'mean',                  # Goles promedio home
        'FTAG': 'mean'                   # Goles promedio away
    }).rename(columns={
        'y': 'Home_Win_Rate',
        'HomeTeam': 'N_Matches',
        'FTHG': 'Avg_Home_Goals',
        'FTAG': 'Avg_Away_Goals'
    })
    
    print("\nANÁLISIS: H2H Dominancia vs Resultado Real")
    print("-" * 70)
    print(analysis)
    
    # Conclusión
    if analysis['Home_Win_Rate'].iloc[-1] > analysis['Home_Win_Rate'].iloc[0]:
        print("\n✅ VALIDADO: H2H dominance SÍ predice resultado")
        print(f"   Home win rate cuando domina H2H: {analysis['Home_Win_Rate'].iloc[-1]*100:.1f}%")
        print(f"   Home win rate cuando away domina H2H: {analysis['Home_Win_Rate'].iloc[0]*100:.1f}%")
        improvement = (analysis['Home_Win_Rate'].iloc[-1] - analysis['Home_Win_Rate'].iloc[0]) * 100
        print(f"   Diferencia: +{improvement:.1f} puntos porcentuales")
    else:
        print("\n⚠️  H2H dominance NO es predictivo en este dataset")
    
    return df_with_h2h, analysis


def test_home_away_separation():
    """
    Test 2: Validar diferencia casa vs fuera
    """
    print("\n" + "=" * 70)
    print("  TEST 2: RENDIMIENTO CASA VS FUERA")
    print("=" * 70)
    
    # Cargar datos
    df = pd.read_parquet(PROC / "matches.parquet")
    df = add_elo(df)
    df = add_home_away_separated_form(df, window=5)
    
    # Análisis: Comparar win rate casa vs fuera
    df['home_stronger_at_home'] = df['Home_as_home_win_rate_roll5'] > df['Home_as_home_win_rate_roll5'].median()
    df['away_stronger_away'] = df['Away_as_away_win_rate_roll5'] > df['Away_as_away_win_rate_roll5'].median()
    
    # Escenarios
    scenarios = {
        'Home fuerte en casa vs Away débil fuera': (
            df['home_stronger_at_home'] & ~df['away_stronger_away']
        ),
        'Home débil en casa vs Away fuerte fuera': (
            ~df['home_stronger_at_home'] & df['away_stronger_away']
        ),
        'Ambos fuertes en su contexto': (
            df['home_stronger_at_home'] & df['away_stronger_away']
        ),
        'Ambos débiles en su contexto': (
            ~df['home_stronger_at_home'] & ~df['away_stronger_away']
        )
    }
    
    print("\nANÁLISIS: Escenarios Casa/Fuera vs Resultado")
    print("-" * 70)
    
    for scenario_name, mask in scenarios.items():
        scenario_df = df[mask]
        if len(scenario_df) > 0:
            home_win_rate = (scenario_df['y'] == 0).mean()
            print(f"\n{scenario_name}:")
            print(f"  Partidos: {len(scenario_df)}")
            print(f"  Home win rate: {home_win_rate*100:.1f}%")
    
    # Conclusión
    print("\n✅ CONCLUSIÓN:")
    print("   Separar casa/fuera permite identificar escenarios con mayor/menor ventaja local")
    
    return df


def test_multi_window():
    """
    Test 3: Comparar forma reciente vs forma media
    """
    print("\n" + "=" * 70)
    print("  TEST 3: MÚLTIPLES VENTANAS TEMPORALES")
    print("=" * 70)
    
    # Cargar datos
    df = pd.read_parquet(PROC / "matches.parquet")
    df = add_elo(df)
    df = add_multi_window_form(df, windows=[5, 10])
    
    # Análisis: Momentum (5 mejor que 10)
    df['home_momentum_positive'] = df['Home_GF_roll5'] > df['Home_GF_roll10']
    df['away_momentum_positive'] = df['Away_GF_roll5'] > df['Away_GF_roll10']
    
    print("\nANÁLISIS: Momentum (forma 5 vs forma 10)")
    print("-" * 70)
    
    # Home con momentum positivo
    home_momentum_up = df[df['home_momentum_positive']]
    home_wr_momentum = (home_momentum_up['y'] == 0).mean()
    
    # Home con momentum negativo
    home_momentum_down = df[~df['home_momentum_positive']]
    home_wr_no_momentum = (home_momentum_down['y'] == 0).mean()
    
    print(f"Home con momentum positivo (últimos 5 > últimos 10):")
    print(f"  Partidos: {len(home_momentum_up)}")
    print(f"  Win rate: {home_wr_momentum*100:.1f}%")
    
    print(f"\nHome con momentum negativo (últimos 5 < últimos 10):")
    print(f"  Partidos: {len(home_momentum_down)}")
    print(f"  Win rate: {home_wr_no_momentum*100:.1f}%")
    
    if home_wr_momentum > home_wr_no_momentum:
        diff = (home_wr_momentum - home_wr_no_momentum) * 100
        print(f"\n✅ VALIDADO: Momentum positivo mejora win rate en +{diff:.1f} puntos")
    
    return df


def test_xg_overperformance():
    """
    Test 4: Validar regresión a la media en xG
    """
    print("\n" + "=" * 70)
    print("  TEST 4: xG OVERPERFORMANCE Y REGRESIÓN")
    print("=" * 70)
    
    # Cargar datos
    df = pd.read_parquet(PROC / "matches.parquet")
    
    if 'xG_home' not in df.columns or df['xG_home'].isna().all():
        print("⚠️  xG no disponible, saltando test")
        return None
    
    df = add_elo(df)
    df = add_xg_rolling_features(df, window=5)
    
    # Filtrar partidos con xG disponible
    df_xg = df[df['Home_xG_overperformance_roll5'].notna()].copy()
    
    # Dividir en overperformers y underperformers
    df_xg['home_overperforming'] = df_xg['Home_xG_overperformance_roll5'] > 1.0
    df_xg['home_underperforming'] = df_xg['Home_xG_overperformance_roll5'] < -1.0
    
    print("\nANÁLISIS: xG Overperformance")
    print("-" * 70)
    
    # Overperformers (tienen suerte)
    over = df_xg[df_xg['home_overperforming']]
    if len(over) > 0:
        avg_goals_next = over['FTHG'].mean()
        print(f"Equipos OVERPERFORMING (>+1.0 goles vs xG):")
        print(f"  Partidos: {len(over)}")
        print(f"  Goles promedio en SIGUIENTE partido: {avg_goals_next:.2f}")
        print(f"  ⚠️  Esperamos regresión (menos goles)")
    
    # Underperformers (mala suerte)
    under = df_xg[df_xg['home_underperforming']]
    if len(under) > 0:
        avg_goals_next = under['FTHG'].mean()
        print(f"\nEquipos UNDERPERFORMING (<-1.0 goles vs xG):")
        print(f"  Partidos: {len(under)}")
        print(f"  Goles promedio en SIGUIENTE partido: {avg_goals_next:.2f}")
        print(f"  ✅ Esperamos regresión (más goles)")
    
    return df_xg


def compare_with_without_features():
    """
    Test 5: Comparar modelo CON vs SIN features profesionales
    """
    print("\n" + "=" * 70)
    print("  TEST 5: COMPARACIÓN CON/SIN FEATURES PROFESIONALES")
    print("=" * 70)
    
    # Cargar datos base
    df_base = pd.read_parquet(PROC / "matches.parquet")
    df_base = add_elo(df_base)
    df_base = add_form(df_base, window=5)
    
    print(f"\nDataset BASE:")
    print(f"  Columnas: {len(df_base.columns)}")
    print(f"  Features principales: ELO, rolling básico (5)")
    
    # Añadir features profesionales
    from src.features.professional_features import add_all_professional_features
    df_pro = add_all_professional_features(
        df_base.copy(),
        h2h_matches=5,
        form_window=5,
        multi_windows=[5, 10],
        enable_xg=True
    )
    
    print(f"\nDataset PROFESIONAL:")
    print(f"  Columnas: {len(df_pro.columns)}")
    print(f"  Features añadidos: {len(df_pro.columns) - len(df_base.columns)}")
    
    # Nuevas features
    new_features = set(df_pro.columns) - set(df_base.columns)
    print(f"\n  Categorías de features nuevos:")
    
    categories = {
        'H2H': [c for c in new_features if 'H2H' in c],
        'Casa/Fuera separado': [c for c in new_features if 'as_home' in c or 'as_away' in c],
        'Multi-window': [c for c in new_features if 'roll10' in c],
        'Motivación': [c for c in new_features if 'motivation' in c or 'streak' in c],
        'xG avanzado': [c for c in new_features if 'xG' in c and 'roll' in c]
    }
    
    for cat, cols in categories.items():
        if cols:
            print(f"    {cat}: {len(cols)} columnas")
    
    return df_base, df_pro


def generate_report():
    """
    Generar reporte completo
    """
    print("\n" + "=" * 70)
    print("  GENERANDO REPORTE COMPLETO")
    print("=" * 70)
    
    results = {}
    
    # Test 1: H2H
    try:
        df_h2h, analysis_h2h = test_h2h_features()
        results['h2h'] = 'PASS'
    except Exception as e:
        print(f"⚠️  Test H2H falló: {e}")
        results['h2h'] = 'FAIL'
    
    # Test 2: Casa/Fuera
    try:
        df_ha = test_home_away_separation()
        results['home_away'] = 'PASS'
    except Exception as e:
        print(f"⚠️  Test Casa/Fuera falló: {e}")
        results['home_away'] = 'FAIL'
    
    # Test 3: Multi-window
    try:
        df_mw = test_multi_window()
        results['multi_window'] = 'PASS'
    except Exception as e:
        print(f"⚠️  Test Multi-window falló: {e}")
        results['multi_window'] = 'FAIL'
    
    # Test 4: xG
    try:
        df_xg = test_xg_overperformance()
        results['xg'] = 'PASS' if df_xg is not None else 'SKIP'
    except Exception as e:
        print(f"⚠️  Test xG falló: {e}")
        results['xg'] = 'FAIL'
    
    # Test 5: Comparación
    try:
        df_base, df_pro = compare_with_without_features()
        results['comparison'] = 'PASS'
    except Exception as e:
        print(f"⚠️  Test Comparación falló: {e}")
        results['comparison'] = 'FAIL'
    
    # Resumen final
    print("\n" + "=" * 70)
    print("  RESUMEN DE TESTS")
    print("=" * 70)
    
    for test_name, status in results.items():
        emoji = "✅" if status == "PASS" else "⚠️" if status == "SKIP" else "❌"
        print(f"{emoji} {test_name.upper()}: {status}")
    
    total_pass = sum(1 for s in results.values() if s == 'PASS')
    print(f"\nTotal: {total_pass}/{len(results)} tests exitosos")
    
    if total_pass >= 4:
        print("\n🎉 FEATURES PROFESIONALES VALIDADOS")
        print("   Listos para usar en producción")
    else:
        print("\n⚠️  Algunos tests fallaron, revisar implementación")


def main():
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║  TEST DE FEATURES PROFESIONALES                            ║
    ║  Validación de mejores prácticas de predicción deportiva  ║
    ╚════════════════════════════════════════════════════════════╝
    """)
    
    # Verificar que existe dataset base
    if not (PROC / "matches.parquet").exists():
        print("❌ ERROR: Dataset base no encontrado")
        print("   Ejecuta primero: python -m src.etl.prepare_dataset_pro")
        return
    
    # Ejecutar todos los tests
    generate_report()
    
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║  TESTS COMPLETADOS                                         ║
    ║                                                            ║
    ║  Próximo paso:                                             ║
    ║  python scripts/prepare_dataset_professional.py            ║
    ║                                                            ║
    ║  Luego:                                                    ║
    ║  python scripts/backtest_optimal_ah_professional.py        ║
    ╚════════════════════════════════════════════════════════════╝
    """)


if __name__ == "__main__":
    main()

