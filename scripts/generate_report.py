from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from src.reporting.metrics import summarize_log

REPORTS = Path("reports"); REPORTS.mkdir(parents=True, exist_ok=True)

def plot_equity(df, out_png):
    if df.empty: return
    plt.figure()
    df['equity'].plot()
    plt.title("Curva de Equity")
    plt.xlabel("Apuesta"); plt.ylabel("Equity")
    plt.tight_layout(); plt.savefig(out_png); plt.close()

def band(x):
    if pd.isna(x): return "N/A"
    if x < 2.0: return "<2.0"
    if x < 3.0: return "2.0–2.99"
    if x < 5.0: return "3.0–4.99"
    return ">=5.0"

def main():
    log_fp = REPORTS / "backtest_log.csv"
    if not log_fp.exists():
        raise SystemExit("No existe reports/backtest_log.csv — corre scripts/backtest_all_markets.py primero.")

    df = pd.read_csv(log_fp, parse_dates=['date'])
    s = summarize_log(df); monthly = df.groupby(df['date'].dt.to_period('M')).agg(turnover=('stake','sum'), pnl=('pnl','sum'), bets=('stake','count')).reset_index()
    monthly['roi'] = monthly['pnl'] / monthly['turnover']

    per_market = df.groupby('market', as_index=False).agg(turnover=('stake','sum'), pnl=('pnl','sum'), bets=('stake','count'))
    per_market['roi'] = per_market['pnl'] / per_market['turnover']

    bm = df.copy(); bm['odds_band'] = bm['odds_open'].apply(band)
    band_market = bm.groupby(['market','odds_band'], as_index=False).agg(turnover=('stake','sum'), pnl=('pnl','sum'), bets=('stake','count'))
    band_market['roi'] = band_market['pnl'] / band_market['turnover']

    png = REPORTS / "equity.png"
    plot_equity(df, png)

    html = f"""
    <html><head><meta charset='utf-8'><title>Backtest Report</title>
      <style>body{{font-family:Arial;margin:24px}} table{{border-collapse:collapse;width:100%}} th,td{{border:1px solid #ddd;padding:6px;text-align:right}} th{{background:#f4f4f4}}</style>
    </head><body>
      <h1>Backtest Report</h1>
      <p>Apuestas: {s['n_bets']} | Turnover: {s['turnover']:.2f} | PnL: {s['pnl']:.2f} | ROI: {s['roi']*100:.2f}% | Hit-rate: {s['hit_rate']*100:.2f}% | Max DD: {s['max_drawdown']:.2f} ({s['max_drawdown_pct']*100:.2f}%)</p>
      <h2>Curva de equity</h2>
      <img src="equity.png" style="max-width:100%"/>
      <h2>ROI mensual</h2>
      {monthly.to_html(index=False)}
      <h2>KPIs por mercado</h2>
      {per_market.to_html(index=False)}
      <h2>ROI por banda de cuota y mercado</h2>
      {band_market.to_html(index=False)}
    </body></html>
    """
    (REPORTS / "backtest_report.html").write_text(html, encoding="utf-8")
    print("Reporte:", REPORTS / "backtest_report.html")

if __name__ == "__main__":
    main()
