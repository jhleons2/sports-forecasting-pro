import pandas as pd
import numpy as np

def drawdown(equity: pd.Series) -> pd.DataFrame:
    run_max = equity.cummax()
    dd = equity - run_max
    dd_pct = dd / run_max.replace(0, np.nan)
    return pd.DataFrame({'equity':equity,'run_max':run_max,'drawdown':dd,'drawdown_pct':dd_pct})

def summarize_log(df: pd.DataFrame) -> dict:
    if df.empty:
        return dict(n_bets=0, turnover=0.0, pnl=0.0, roi=0.0, hit_rate=0.0, max_drawdown=0.0, max_drawdown_pct=0.0)
    turnover = df['stake'].sum()
    pnl = df['pnl'].sum()
    roi = pnl/turnover if turnover>0 else 0.0
    hit_rate = (df['result']=='WIN').mean() if len(df)>0 else 0.0
    dd = drawdown(df['equity'])
    return dict(n_bets=int(len(df)), turnover=float(turnover), pnl=float(pnl), roi=float(roi),
                hit_rate=float(hit_rate), max_drawdown=float(dd['drawdown'].min()), max_drawdown_pct=float(dd['drawdown_pct'].min()))
