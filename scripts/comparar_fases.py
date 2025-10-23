"""
Comparar resultados entre fases
"""
import pandas as pd

log = pd.read_csv("reports/backtest_log.csv")

print("\n" + "="*70)
print("  RESULTADOS FASE 2 - CON CALIBRACIÓN ISOTÓNICA")
print("="*70 + "\n")

# Métricas globales
turnover = log['stake'].sum()
pnl = log['pnl'].sum()
roi = (pnl/turnover)*100 if turnover>0 else 0

print("[METRICAS GLOBALES]")
print(f"  Total apuestas: {len(log)}")
print(f"  ROI Global: {roi:+.2f}%")
print(f"  Hit-rate: {(log['result']=='WIN').mean()*100:.2f}%")

if log['pnl'].std() > 0:
    sharpe = log['pnl'].mean() / log['pnl'].std()
    print(f"  Sharpe ratio: {sharpe:.3f}")

print("\n" + "-"*70)
print("[POR MERCADO]")
print("-"*70)

for market in ['1X2', 'AH', 'OU2.5']:
    d = log[log['market'] == market]
    if len(d) == 0:
        continue
        
    m_roi = (d['pnl'].sum() / d['stake'].sum()) * 100 if d['stake'].sum() > 0 else 0
    m_hitrate = (d['result'] == 'WIN').mean() * 100
    m_avg_odds = d['odds_open'].mean()
    
    wins = len(d[d['result']=='WIN'])
    losses = len(d[d['result']=='LOSS'])
    
    print(f"\n{market}:")
    print(f"  Apuestas: {len(d)} ({wins}W / {losses}L)")
    print(f"  ROI: {m_roi:+.2f}%")
    print(f"  Hit-rate: {m_hitrate:.2f}%")
    print(f"  Odds promedio: {m_avg_odds:.2f}")
    print(f"  PNL: {d['pnl'].sum():+,.2f}")

print("\n" + "="*70)
print("  COMPARATIVA FASES")
print("="*70 + "\n")

print("FASE 1 (Sin 1X2):")
print("  ROI:       +56.75%")
print("  Apuestas:  497")
print("  Mercados:  AH + OU")
print()
print("FASE 2 (Con calibración + 1X2):")
print(f"  ROI:       {roi:+.2f}%")
print(f"  Apuestas:  {len(log)}")
print("  Mercados:  1X2 + AH + OU")
print()

d_1x2 = log[log['market'] == '1X2']
if len(d_1x2) > 0:
    roi_1x2 = (d_1x2['pnl'].sum() / d_1x2['stake'].sum()) * 100
    print(f"MERCADO 1X2 REACTIVADO:")
    print(f"  ROI: {roi_1x2:+.2f}%")
    print(f"  Apuestas: {len(d_1x2)}")
    if roi_1x2 > 0:
        print("  Estado: RENTABLE ✓")
    else:
        print("  Estado: Aun negativo")

print("\n" + "="*70)

