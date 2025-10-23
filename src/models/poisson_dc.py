import numpy as np
from math import log
from scipy.optimize import minimize
import pandas as pd

def dc_tau(x, y, lam, mu, rho):
    if x == 0 and y == 0: return 1 - (lam * mu * rho)
    elif x == 0 and y == 1: return 1 + (lam * rho)
    elif x == 1 and y == 0: return 1 + (mu * rho)
    elif x == 1 and y == 1: return 1 - rho
    else: return 1.0

class DixonColes:
    def __init__(self, init=None):
        self.params_ = None
        self.init = init or np.array([0.05,0.05,-0.05,-0.05,0.2,0.0])

    def _intensity(self, r, p):
        elo_diff = (r['EloHome'] - r['EloAway'])/400.0
        lam = np.exp(p[0] + p[1]*elo_diff + p[4])
        mu  = np.exp(p[2] - p[3]*elo_diff)
        return lam, mu

    def _nll(self, p, df):
        ll = 0.0
        for _, r in df.iterrows():
            from math import factorial
            x, y = int(r['FTHG']), int(r['FTAG'])
            lam, mu = self._intensity(r, p)
            ll += (-lam + x*np.log(lam) - np.log(factorial(x))
                   -mu + y*np.log(mu) - np.log(factorial(y))
                   + np.log(dc_tau(x,y,lam,mu,p[5])))
        return -ll

    def fit(self, df):
        res = minimize(self._nll, self.init, args=(df,), method='L-BFGS-B')
        self.params_ = res.x
        return self

    def score_matrix(self, row, max_goals=10):
        from math import factorial
        p = self.params_
        lam, mu = self._intensity(row, p)
        mat = np.zeros((max_goals+1, max_goals+1))
        for x in range(max_goals+1):
            for y in range(max_goals+1):
                px = np.exp(-lam) * (lam**x) / factorial(x)
                py = np.exp(-mu)  * (mu**y)  / factorial(y)
                mat[x,y] = px*py*dc_tau(x,y,lam,mu,p[5])
        mat /= mat.sum()
        return mat

    def predict_1x2(self, df, max_goals=10):
        outs = []
        for _, r in df.iterrows():
            m = self.score_matrix(r, max_goals)
            pH = np.tril(m, -1).sum()
            pD = np.trace(m)
            pA = np.triu(m, 1).sum()
            outs.append({'pH':pH,'pD':pD,'pA':pA})
        return pd.DataFrame(outs)

    def prob_over_under(self, row, line=2.5, max_goals=10):
        m = self.score_matrix(row, max_goals)
        over = 0.0; under = 0.0
        G = m.shape[0]-1
        for x in range(G+1):
            for y in range(G+1):
                t = x+y
                if t > line: over += m[x,y]
                elif t < line: under += m[x,y]
        equal = 1.0 - (over+under)
        return dict(pOver=over, pUnder=under, pEqual=equal)

    def ah_probabilities(self, row, line=0.0, side='home', max_goals=10):
        m = self.score_matrix(row, max_goals)
        from collections import defaultdict
        diff = defaultdict(float)
        G = m.shape[0]-1
        for x in range(G+1):
            for y in range(G+1):
                diff[x-y] += m[x,y]
        h = float(line)
        if side=='away': h = -h
        def base(hh):
            pW = sum(v for d,v in diff.items() if d >  hh)
            pU = sum(v for d,v in diff.items() if d == hh)
            pL = sum(v for d,v in diff.items() if d <  hh)
            return pW, pU, pL
        frac = h - int(h)
        if abs(frac) in (0.0, 0.5):
            w,u,l = base(h)
            return dict(win=w, half_win=0.0, push=u, half_loss=0.0, loss=l)
        elif abs(frac) in (0.25, 0.75):
            if frac>0:
                h1 = (int(h) + (0.5 if abs(frac)==0.75 else 0.0))
                h2 = (int(h) + (1.0 if abs(frac)==0.75 else 0.5))
            else:
                if abs(frac)==0.25:
                    h1, h2 = int(h) - 0.5, int(h) + 0.0
                else:
                    h1, h2 = int(h) - 1.0, int(h) - 0.5
            w1,u1,l1 = base(h1); w2,u2,l2 = base(h2)
            win = 0.5*(w1+w2)
            push = 0.5*(u1+u2)
            half_win  = 0.5*(w1*u2 + w2*u1)
            half_loss = 0.5*(l1*u2 + l2*u1)
            loss = 0.5*(l1+l2)
            s = win+half_win+push+half_loss+loss
            if abs(1-s)>1e-8: push += (1-s)
            return dict(win=win, half_win=half_win, push=push, half_loss=half_loss, loss=loss)
        else:
            w,u,l = base(round(h*2)/2.0)
            return dict(win=w, half_win=0.0, push=u, half_loss=0.0, loss=l)
