import pandas as pd
import numpy as np
from sklearn.metrics import log_loss

def brier_multiclass(y_true, proba):
    K = proba.shape[1]
    y_ovr = np.eye(K)[y_true]
    return np.mean(np.sum((proba - y_ovr)**2, axis=1))

def walk_forward_eval(df, proba_cols=('pH','pD','pA'), y_col='y', date_col='Date', folds=5):
    df = df.sort_values(date_col).reset_index(drop=True)
    n = len(df)
    fold_sizes = np.full(folds, n//folds); fold_sizes[:n%folds]+=1
    idx = 0; mets = []
    for i, size in enumerate(fold_sizes):
        start, stop = idx, idx+size
        train = df.iloc[:stop]; test = df.iloc[stop:stop+size] if i<folds-1 else df.iloc[stop:]
        if len(test)==0: break
        y = test[y_col].to_numpy(); proba = test[list(proba_cols)].to_numpy()
        mets.append(dict(fold=i+1, logloss=log_loss(y, proba, labels=[0,1,2]), brier=brier_multiclass(y, proba), n=len(test)))
        idx = stop
    return pd.DataFrame(mets)
