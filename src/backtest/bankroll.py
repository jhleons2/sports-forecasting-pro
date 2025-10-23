def kelly_fraction(p_hat: float, odds: float, kelly_frac: float = 0.25) -> float:
    b = odds - 1.0
    f_star = (b * p_hat - (1 - p_hat)) / b if b != 0 else 0.0
    return max(0.0, kelly_frac * f_star)

def bet_decision(edge: float, threshold: float = 0.02) -> bool:
    return edge >= threshold
