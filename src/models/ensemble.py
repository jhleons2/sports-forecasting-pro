import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

def logit(p):
    p = np.clip(p, 1e-6, 1-1e-6)
    return np.log(p/(1-p))

def fit_blender(p_model: pd.DataFrame, p_mkt: pd.DataFrame, y):
    X = pd.concat([p_model.add_prefix('m_').apply(logit),
                   p_mkt.add_prefix('mk_').apply(logit)], axis=1)
    lr = LogisticRegression(max_iter=200, multi_class='multinomial')
    lr.fit(X, y)
    return lr

def predict_blend(lr, p_model: pd.DataFrame, p_mkt: pd.DataFrame):
    X = pd.concat([p_model.add_prefix('m_').apply(logit),
                   p_mkt.add_prefix('mk_').apply(logit)], axis=1)
    proba = lr.predict_proba(X)
    return pd.DataFrame(proba, columns=['pH','pD','pA'])
