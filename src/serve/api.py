from fastapi import FastAPI
from pydantic import BaseModel
import numpy as np
import pandas as pd
from pathlib import Path
from src.models.poisson_dc import DixonColes

app = FastAPI(title="Sports Forecasting PRO API")
dc = DixonColes()

class Match(BaseModel):
    EloHome: float
    EloAway: float

@app.get("/health")
def health():
    return {"status":"ok"}

@app.post("/predict/1x2")
def predict(m: Match):
    if dc.params_ is None:
        dc.params_ = np.array([0.05,0.05,-0.05,-0.05,0.2,0.0])
    row = {"EloHome":m.EloHome, "EloAway":m.EloAway, "FTHG":0, "FTAG":0}
    df = pd.DataFrame([row])
    proba = dc.predict_1x2(df)
    return dict(pH=float(proba.loc[0,'pH']), pD=float(proba.loc[0,'pD']), pA=float(proba.loc[0,'pA']))
