def settle_1x2(idx_pick, y, stake, odds):
    if y == idx_pick:
        return stake*(odds-1.0), "WIN"
    return -stake, "LOSS"

def settle_ou(selection, fthg, ftag, stake, odds, line=2.5):
    total = int(fthg) + int(ftag)
    if selection=='Over':
        return (stake*(odds-1.0), "WIN") if total>line else (-stake, "LOSS")
    else:
        return (stake*(odds-1.0), "WIN") if total<line else (-stake, "LOSS")

def settle_ah(selection, h, fthg, ftag, stake, odds):
    d = int(fthg) - int(ftag)
    side = 'home' if selection=='Home' else 'away'
    h_eff = h if side=='home' else -h
    frac = h_eff - int(h_eff)
    if abs(frac) in (0.0, 0.5):
        if d > h_eff:  return stake*(odds-1.0), "WIN"
        if d == h_eff: return 0.0, "PUSH"
        return -stake, "LOSS"
    elif abs(frac) in (0.25, 0.75):
        if frac>0:
            h1 = (int(h_eff) + (0.5 if abs(frac)==0.75 else 0.0))
            h2 = (int(h_eff) + (1.0 if abs(frac)==0.75 else 0.5))
        else:
            if abs(frac)==0.25: h1,h2 = int(h_eff)-0.5, int(h_eff)+0.0
            else:               h1,h2 = int(h_eff)-1.0, int(h_eff)-0.5
        def half(hh, st):
            if d > hh:  return st*(odds-1.0)
            if d == hh: return 0.0
            return -st
        pnl = half(h1, stake*0.5) + half(h2, stake*0.5)
        return pnl, "WIN" if pnl>0 else ("LOSS" if pnl<0 else "PUSH")
    else:
        hh = round(h_eff*2)/2.0
        if d > hh:  return stake*(odds-1.0), "WIN"
        if d == hh: return 0.0, "PUSH"
        return -stake, "LOSS"
