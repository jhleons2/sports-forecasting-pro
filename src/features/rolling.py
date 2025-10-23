import pandas as pd

def add_form(df, window=5):
    df = df.sort_values('Date').copy()
    def team_roll(team_col, gf_col, ga_col, prefix):
        grp = df.groupby(team_col)
        df[f'{prefix}_GF_roll{window}'] = grp[gf_col].rolling(window).sum().reset_index(level=0, drop=True)
        df[f'{prefix}_GA_roll{window}'] = grp[ga_col].rolling(window).sum().reset_index(level=0, drop=True)
        df[f'{prefix}_GD_roll{window}'] = grp.apply(lambda g: (g[gf_col]-g[ga_col]).rolling(window).sum()).reset_index(level=0, drop=True)
    team_roll('HomeTeam', 'FTHG', 'FTAG', 'Home')
    team_roll('AwayTeam', 'FTAG', 'FTHG', 'Away')
    return df
