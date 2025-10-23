from pathlib import Path
import pandas as pd
import numpy as np
from src.models.poisson_dc import DixonColes
from src.features.ratings import add_elo
from src.features.rolling import add_form
from src.utils.odds import market_probs_1x2
from src.models.ensemble import fit_blender, predict_blend
from src.models.calibration import isotonic_multiclass
from sklearn.isotonic import IsotonicRegression

PROC = Path("data/processed"); REPORTS = Path("reports"); REPORTS.mkdir(parents=True, exist_ok=True)

df0 = pd.read_parquet(PROC / "matches.parquet").sort_values("Date")
df  = add_elo(df0); df = add_form(df)
split = df['Date'].quantile(0.7)

train = df[df['Date']<=split].copy()
test  = df[df['Date']> split].copy()

dc = DixonColes().fit(train)
# calibration split
split_cal = train['Date'].quantile(0.85)
tr_core = train[train['Date']<=split_cal].copy()
cal     = train[train['Date']> split_cal].copy()
dc = DixonColes().fit(tr_core)

p_cal = dc.predict_1x2(cal)
q_cal = cal.apply(market_probs_1x2, axis=1, result_type='expand'); q_cal.columns=['pH_mkt','pD_mkt','pA_mkt']
lr = fit_blender(p_cal[['pH','pD','pA']], q_cal[['pH_mkt','pD_mkt','pA_mkt']], cal['y'])

p_raw_test = dc.predict_1x2(test)
q_test = test.apply(market_probs_1x2, axis=1, result_type='expand'); q_test.columns=['pH_mkt','pD_mkt','pA_mkt']
p_blend_test = predict_blend(lr, p_raw_test[['pH','pD','pA']], q_test[['pH_mkt','pD_mkt','pA_mkt']]).to_numpy()

# Isotonic per class
p_blend_cal = predict_blend(lr, p_cal[['pH','pD','pA']], q_cal[['pH_mkt','pD_mkt','pA_mkt']]).to_numpy()
IRs = []
for k in range(3):
    ir = IsotonicRegression(out_of_bounds='clip')
    ir.fit(p_blend_cal[:,k], (cal['y'].to_numpy()==k).astype(int))
    IRs.append(ir)

p_calib = np.zeros_like(p_blend_test)
for k in range(3):
    p_calib[:,k] = IRs[k].transform(p_blend_test[:,k])
p_calib /= p_calib.sum(axis=1, keepdims=True)

out = test[["Date","League","HomeTeam","AwayTeam","FTHG","FTAG","y"]].reset_index(drop=True)
out[["pH_raw","pD_raw","pA_raw"]]   = p_raw_test[["pH","pD","pA"]].to_numpy()
out[["pH_bl","pD_bl","pA_bl"]]     = p_blend_test
out[["pH_cal","pD_cal","pA_cal"]]  = p_calib
out.to_csv(REPORTS / "probs_compare_raw_blend_cal.csv", index=False)
print("Guardado:", REPORTS / "probs_compare_raw_blend_cal.csv")
