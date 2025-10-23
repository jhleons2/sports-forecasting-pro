import pandas as pd
from xgboost import XGBClassifier

def train_boosting(X: pd.DataFrame, y, params=None):
    params = params or dict(
        n_estimators=300, max_depth=5, learning_rate=0.05, subsample=0.8, colsample_bytree=0.8,
        objective='multi:softprob', num_class=3, eval_metric='mlogloss'
    )
    model = XGBClassifier(**params)
    model.fit(X, y)
    return model
