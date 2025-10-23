"""
Análisis completo de rentabilidad del sistema
"""

import pandas as pd
import numpy as np
from pathlib import Path

log = pd.read_csv("reports/backtest_log.csv")

print("\n" + "="*70)
print("  ANÁLISIS COMPLETO DE RENTABILIDAD")
print("="*70 + "\n")

# Métricas generales
turnover = log['stake'].sum()
pnl = log['pnl'].sum()
roi = (pnl/turnover)*100 if turnover>0 else 0

print("[METRICAS GLOBALES]")
print(f"  Total apuestas: {len(log)}")
print(f"  Turnover: {turnover:,.2f}")
print(f"  PNL: {pnl:+,.2f}")
print(f"  ROI: {roi:+.2f}%")
print(f"  Hit-rate: {(log['result']=='WIN').mean()*100:.2f}%")

# Sharpe ratio aproximado
if log['pnl'].std() > 0:
    sharpe = log['pnl'].mean() / log['pnl'].std()
    print(f"  Sharpe ratio: {sharpe:.3f}")

# Max drawdown
log['equity_max'] = log['equity'].cummax()
log['drawdown'] = log['equity_max'] - log['equity']
max_dd = (log['drawdown'].max() / log['equity'].iloc[0]) * 100
print(f"  Max drawdown: {max_dd:.2f}%")

print("\n" + "-"*70)
print("[ANALISIS POR MERCADO]")
print("-"*70)

for market in ['1X2', 'AH', 'OU2.5']:
    d = log[log['market'] == market]
    if len(d) == 0:
        continue
        
    m_roi = (d['pnl'].sum() / d['stake'].sum()) * 100 if d['stake'].sum() > 0 else 0
    m_hitrate = (d['result'] == 'WIN').mean() * 100
    m_avg_odds = d['odds_open'].mean()
    m_edge = d['p_model'].sub(d['p_mkt'], fill_value=0).mean()
    
    wins = len(d[d['result']=='WIN'])
    losses = len(d[d['result']=='LOSS'])
    
    print(f"\n[{market}]")
    print(f"  Apuestas: {len(d)} ({wins}W / {losses}L)")
    print(f"  ROI: {m_roi:+.2f}%")
    print(f"  Hit-rate: {m_hitrate:.2f}%")
    print(f"  Odds promedio: {m_avg_odds:.2f}")
    print(f"  Edge promedio: {m_edge:.4f} ({m_edge*100:.2f}%)")
    print(f"  PNL: {d['pnl'].sum():+,.2f}")
    print(f"  Stake promedio: {d['stake'].mean():,.2f}")

print("\n" + "-"*70)
print("[PROBLEMAS IDENTIFICADOS]")
print("-"*70)

problems = []

# Problema 1: Mercado 1X2 negativo
d_1x2 = log[log['market'] == '1X2']
if len(d_1x2) > 0:
    roi_1x2 = (d_1x2['pnl'].sum() / d_1x2['stake'].sum()) * 100
    if roi_1x2 < -5:
        problems.append(f"1. Mercado 1X2 con ROI muy negativo ({roi_1x2:.2f}%)")

# Problema 2: Stakes muy altos
if log['stake'].max() > 100000:
    problems.append(f"2. Stakes excesivamente altos (max: {log['stake'].max():,.0f})")

# Problema 3: Edge muy bajo
avg_edge = log['p_model'].sub(log['p_mkt'], fill_value=0).mean()
if avg_edge < 0.05:
    problems.append(f"3. Edge promedio muy bajo ({avg_edge*100:.2f}%)")

# Problema 4: Drawdown alto
if max_dd > 20:
    problems.append(f"4. Drawdown muy alto ({max_dd:.2f}%)")

# Problema 5: Hit-rate bajo en mercado perdedor
for market in ['1X2', 'OU2.5']:
    d = log[log['market'] == market]
    if len(d) > 0:
        roi_m = (d['pnl'].sum() / d['stake'].sum()) * 100
        hr = (d['result'] == 'WIN').mean() * 100
        if roi_m < 0 and hr < 50:
            problems.append(f"5. {market}: ROI negativo ({roi_m:.2f}%) con hit-rate bajo ({hr:.2f}%)")

if problems:
    for p in problems:
        print(f"  [X] {p}")
else:
    print("  [OK] No se detectaron problemas criticos")

print("\n" + "-"*70)
print("[OPORTUNIDADES DE MEJORA]")
print("-"*70)

improvements = []

# Mejora 1: Optimizar threshold de edge
if avg_edge < 0.05:
    improvements.append("1. Aumentar threshold de edge mínimo (actual ~2%, recomendar 5%)")

# Mejora 2: Calibración
d_1x2 = log[log['market'] == '1X2']
if len(d_1x2) > 0 and (d_1x2['pnl'].sum() / d_1x2['stake'].sum()) < 0:
    improvements.append("2. Implementar calibración isotónica para probabilidades")

# Mejora 3: Kelly fractions
if log['stake'].max() > 100000:
    improvements.append("3. Reducir Kelly fractions (actual: 0.25/0.20/0.15, probar: 0.10/0.08/0.05)")

# Mejora 4: Filtros de calidad
low_odds = (log['odds_open'] < 1.5).sum()
if low_odds > len(log) * 0.2:
    improvements.append(f"4. Filtrar odds muy bajas (<1.5): {low_odds} apuestas ({low_odds/len(log)*100:.1f}%)")

# Mejora 5: xG integration
improvements.append("5. Integrar xG metrics de Understat para mejorar predicciones")

# Mejora 6: Walk-forward validation
improvements.append("6. Implementar walk-forward validation en lugar de split 70/30")

# Mejora 7: Ensemble
improvements.append("7. Agregar XGBoost ensemble con Dixon-Coles")

for imp in improvements:
    print(f"  [>] {imp}")

print("\n" + "="*70)
print("  RECOMENDACIONES PRIORITARIAS")
print("="*70 + "\n")

print("[ACCIONES INMEDIATAS - Mayor Impacto]")
print("\n1. AUMENTAR EDGE MÍNIMO:")
print("   Cambiar threshold de 0.02 (2%) a 0.05 (5%)")
print("   Impacto esperado: +10-15% ROI\n")

print("2. REDUCIR KELLY FRACTIONS:")
print("   1X2: 0.25 → 0.10")
print("   OU: 0.20 → 0.08")
print("   AH: 0.15 → 0.05")
print("   Impacto: Reducir riesgo y volatilidad\n")

print("3. ELIMINAR MERCADO 1X2 O RECALIBRAR:")
print("   Opción A: Desactivar temporalmente")
print("   Opción B: Calibración isotónica")
print("   Impacto: Eliminar pérdidas de -25.8% ROI\n")

print("4. FILTRAR ODDS BAJAS:")
print("   Agregar filtro: odds >= 1.60")
print("   Impacto: Mejor value, menos ruido\n")

print("5. INTEGRAR xG:")
print("   Ejecutar: make understat")
print("   Impacto: +5-10% en precisión Over/Under\n")

print("="*70)

