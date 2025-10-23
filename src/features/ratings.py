import pandas as pd

class Elo:
    def __init__(self, k=20.0, home_adv=60.0, base=1500.0):
        self.k = k; self.home_adv = home_adv; self.base = base; self.table = {}

    def get(self, t): return self.table.get(t, self.base)

    def expected(self, ra, rb): return 1.0 / (1.0 + 10 ** (-(ra - rb)/400.0))

    def update(self, home, away, s_home):
        ra = self.get(home) + self.home_adv
        rb = self.get(away)
        ea = self.expected(ra, rb)
        self.table[home] = self.get(home) + self.k*(s_home - ea)
        self.table[away] = self.get(away) + self.k*((1 - s_home) - (1 - ea))

def add_elo(df, home='HomeTeam', away='AwayTeam', hg='FTHG', ag='FTAG'):
    elo = Elo()
    outs = []
    for _, r in df.sort_values('Date').iterrows():
        h, a = r[home], r[away]
        rH, rA = elo.get(h), elo.get(a)
        if r[hg] > r[ag]: s = 1.0
        elif r[hg] == r[ag]: s = 0.5
        else: s = 0.0
        elo.update(h, a, s)
        row = r.to_dict()
        row['EloHome'] = rH; row['EloAway'] = rA
        outs.append(row)
    return pd.DataFrame(outs)
