from pathlib import Path
import pandas as pd
from src.models.poisson_dc import DixonColes
from src.features.ratings import add_elo
from src.features.rolling import add_form

PROC = Path("data/processed"); REPORTS = Path("reports"); REPORTS.mkdir(parents=True, exist_ok=True)

# Cargar y crear features ANTES del split
df0 = pd.read_parquet(PROC / "matches.parquet").sort_values("Date")
df = add_elo(df0); df = add_form(df)

split = df["Date"].quantile(0.7)
train = df[df["Date"] <= split].copy()
test  = df[df["Date"] >  split].copy()

dc = DixonColes().fit(train)
p = dc.predict_1x2(test)
out = test[["Date","League","HomeTeam","AwayTeam","FTHG","FTAG"]].reset_index(drop=True)
out[["pH","pD","pA"]] = p[["pH","pD","pA"]].to_numpy()
out.to_csv(REPORTS / "probabilities_1x2_test.csv", index=False)
print("Guardado:", REPORTS / "probabilities_1x2_test.csv")
