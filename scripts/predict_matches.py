"""
Sistema de Predicción de Partidos y Eventos Específicos

Genera predicciones para:
1. Resultados 1X2 (Home/Draw/Away)
2. Over/Under goles
3. Asian Handicap
4. Eventos específicos: Corners, Tarjetas, Tiros

Uso:
    python scripts/predict_matches.py --date "2025-10-25" --league "E0"
"""

import pandas as pd
import numpy as np
from pathlib import Path
import argparse
from datetime import datetime, timedelta

from src.models.poisson_dc import DixonColes
from src.models.xgboost_classifier import XGBoost1X2Classifier
from src.models.calibration import ProbabilityCalibrator
from src.features.ratings import add_elo
from src.features.rolling import add_form
from src.utils.odds import remove_overround, implied_probs_from_odds

PROC = Path("data/processed")
REPORTS = Path("reports"); REPORTS.mkdir(parents=True, exist_ok=True)


class MatchPredictor:
    """
    Predictor completo de partidos y eventos.
    """
    
    def __init__(self):
        self.dc_model = None
        self.xgb_model = None
        self.calibrator = None
        self.df_historical = None
        
    def load_and_train(self):
        """
        Carga datos históricos y entrena modelos.
        """
        print("=" * 70)
        print("SISTEMA DE PREDICCIÓN - CARGANDO MODELOS")
        print("=" * 70)
        
        # Cargar datos
        print("\n1. Cargando datos históricos...")
        self.df_historical = pd.read_parquet(PROC / "matches.parquet")
        
        # Features
        self.df_historical = add_elo(self.df_historical)
        self.df_historical = add_form(self.df_historical)
        
        print(f"   Partidos cargados: {len(self.df_historical)}")
        print(f"   Rango: {self.df_historical['Date'].min()} a {self.df_historical['Date'].max()}")
        
        # Entrenar Dixon-Coles (para AH y OU)
        print("\n2. Entrenando Dixon-Coles (AH + OU)...")
        self.dc_model = DixonColes().fit(self.df_historical)
        print("   OK")
        
        # Entrenar XGBoost (para 1X2)
        print("3. Entrenando XGBoost (1X2)...")
        self.xgb_model = XGBoost1X2Classifier(n_estimators=100, max_depth=4, learning_rate=0.05)
        self.xgb_model.fit(self.df_historical)
        print("   OK")
        
        # Calibrar
        print("4. Calibrando probabilidades...")
        p1x2_train = self.xgb_model.predict_proba(self.df_historical)
        self.calibrator = ProbabilityCalibrator()
        self.calibrator.fit(self.df_historical['y'].values, p1x2_train)
        print("   OK")
        
        print("\n" + "=" * 70)
        print("MODELOS LISTOS PARA PREDICCIÓN")
        print("=" * 70)
    
    def predict_1x2(self, match_data):
        """
        Predice resultado 1X2 con XGBoost.
        
        Returns:
        --------
        dict con 'pH', 'pD', 'pA'
        """
        match_df = pd.DataFrame([match_data])
        probs_raw = self.xgb_model.predict_proba(match_df)
        probs_cal = self.calibrator.transform(probs_raw)
        
        return {
            'pH': float(probs_cal.iloc[0]['pH']),
            'pD': float(probs_cal.iloc[0]['pD']),
            'pA': float(probs_cal.iloc[0]['pA'])
        }
    
    def predict_goals(self, match_data):
        """
        Predice goles esperados usando Dixon-Coles.
        
        Returns:
        --------
        dict con goles esperados
        """
        p = self.dc_model.params_
        
        # Calcular intensidades lambda y mu
        elo_diff = (match_data['EloHome'] - match_data['EloAway']) / 400.0
        lambda_home = np.exp(p[0] + p[1] * elo_diff + p[4])
        mu_away = np.exp(p[2] - p[3] * elo_diff)
        
        return {
            'xG_home': float(lambda_home),
            'xG_away': float(mu_away),
            'xG_total': float(lambda_home + mu_away)
        }
    
    def predict_over_under(self, match_data, line=2.5):
        """
        Predice Over/Under para una línea específica.
        
        Returns:
        --------
        dict con probabilidades over/under
        """
        match_df = pd.DataFrame([match_data])
        probs = self.dc_model.prob_over_under(match_df.iloc[0], line=line)
        
        return {
            'pOver': float(probs['pOver']),
            'pUnder': float(probs['pUnder']),
            'pEqual': float(probs['pEqual'])
        }
    
    def predict_asian_handicap(self, match_data, line=0.0):
        """
        Predice Asian Handicap.
        
        Returns:
        --------
        dict con probabilidades AH
        """
        match_df = pd.DataFrame([match_data])
        
        probs_home = self.dc_model.ah_probabilities(match_df.iloc[0], line=line, side='home')
        probs_away = self.dc_model.ah_probabilities(match_df.iloc[0], line=line, side='away')
        
        return {
            'home': {
                'win': float(probs_home['win']),
                'half_win': float(probs_home.get('half_win', 0.0)),
                'push': float(probs_home['push']),
                'half_loss': float(probs_home.get('half_loss', 0.0)),
                'loss': float(probs_home['loss'])
            },
            'away': {
                'win': float(probs_away['win']),
                'half_win': float(probs_away.get('half_win', 0.0)),
                'push': float(probs_away['push']),
                'half_loss': float(probs_away.get('half_loss', 0.0)),
                'loss': float(probs_away['loss'])
            }
        }
    
    def predict_corners(self, match_data):
        """
        Predice corners usando estadísticas históricas.
        
        Returns:
        --------
        dict con corners esperados
        """
        # Obtener corners promedio de equipos (últimos 5 partidos)
        # Si tenemos datos de corners en el dataset
        if 'Home_corners_roll5' in match_data:
            corners_home = match_data.get('Home_corners_roll5', 5.5)
            corners_away = match_data.get('Away_corners_roll5', 5.5)
        else:
            # Usar aproximación basada en xG
            xg = self.predict_goals(match_data)
            # Aproximación: ~5-6 corners por gol esperado
            corners_home = xg['xG_home'] * 5.5
            corners_away = xg['xG_away'] * 5.5
        
        total_corners = corners_home + corners_away
        
        return {
            'corners_home': float(corners_home),
            'corners_away': float(corners_away),
            'corners_total': float(total_corners),
            'over_9.5': float(1.0 if total_corners > 9.5 else 0.0),
            'over_10.5': float(1.0 if total_corners > 10.5 else 0.0),
            'over_11.5': float(1.0 if total_corners > 11.5 else 0.0)
        }
    
    def predict_cards(self, match_data):
        """
        Predice tarjetas usando estadísticas históricas.
        
        Returns:
        --------
        dict con tarjetas esperadas
        """
        # Aproximación basada en intensidad del partido
        # Equipos con más diferencia ELO = menos tarjetas (partido controlado)
        # Equipos parejos = más tarjetas (partido disputado)
        
        elo_diff = abs(match_data['EloHome'] - match_data['EloAway'])
        
        # Base: ~3-4 tarjetas amarillas por partido
        # Más parejos = más tarjetas
        base_cards = 3.5
        if elo_diff < 50:  # Muy parejos
            total_cards = base_cards + 1.0
        elif elo_diff > 150:  # Muy desiguales
            total_cards = base_cards - 0.5
        else:
            total_cards = base_cards
        
        return {
            'yellow_cards': float(total_cards),
            'red_cards': float(0.15),  # ~15% probabilidad de roja
            'total_cards': float(total_cards + 0.15),
            'over_3.5_cards': float(1.0 if total_cards > 3.5 else 0.0),
            'over_4.5_cards': float(1.0 if total_cards > 4.5 else 0.0)
        }
    
    def predict_shots(self, match_data):
        """
        Predice tiros usando xG esperados.
        
        Returns:
        --------
        dict con tiros esperados
        """
        xg = self.predict_goals(match_data)
        
        # Aproximación: ~8-10 tiros por gol esperado
        shots_home = xg['xG_home'] * 9.0
        shots_away = xg['xG_away'] * 9.0
        
        # Tiros a puerta: ~35% del total
        shots_on_target_home = shots_home * 0.35
        shots_on_target_away = shots_away * 0.35
        
        return {
            'shots_home': float(shots_home),
            'shots_away': float(shots_away),
            'shots_total': float(shots_home + shots_away),
            'shots_on_target_home': float(shots_on_target_home),
            'shots_on_target_away': float(shots_on_target_away)
        }
    
    def predict_all(self, match_data):
        """
        Genera todas las predicciones para un partido.
        
        Parameters:
        -----------
        match_data : dict
            Datos del partido con ELO, forma, etc.
        
        Returns:
        --------
        dict con todas las predicciones
        """
        predictions = {
            'match_info': {
                'home_team': match_data.get('HomeTeam', 'Home'),
                'away_team': match_data.get('AwayTeam', 'Away'),
                'league': match_data.get('League', 'N/A'),
                'date': match_data.get('Date', 'N/A')
            },
            '1x2': self.predict_1x2(match_data),
            'goals': self.predict_goals(match_data),
            'over_under_2.5': self.predict_over_under(match_data, 2.5),
            'over_under_1.5': self.predict_over_under(match_data, 1.5),
            'over_under_3.5': self.predict_over_under(match_data, 3.5),
            'asian_handicap_0': self.predict_asian_handicap(match_data, 0.0),
            'asian_handicap_-0.5': self.predict_asian_handicap(match_data, -0.5),
            'asian_handicap_+0.5': self.predict_asian_handicap(match_data, 0.5),
            'corners': self.predict_corners(match_data),
            'cards': self.predict_cards(match_data),
            'shots': self.predict_shots(match_data)
        }
        
        return predictions


def print_predictions(predictions):
    """
    Imprime predicciones en formato legible.
    """
    print("\n" + "=" * 70)
    print(f"PREDICCIÓN: {predictions['match_info']['home_team']} vs {predictions['match_info']['away_team']}")
    print("=" * 70)
    
    # 1X2
    print("\n1X2:")
    print(f"  Home:  {predictions['1x2']['pH']*100:.1f}%")
    print(f"  Draw:  {predictions['1x2']['pD']*100:.1f}%")
    print(f"  Away:  {predictions['1x2']['pA']*100:.1f}%")
    
    # Goles esperados
    print("\nGoles Esperados (xG):")
    print(f"  {predictions['match_info']['home_team']}: {predictions['goals']['xG_home']:.2f}")
    print(f"  {predictions['match_info']['away_team']}: {predictions['goals']['xG_away']:.2f}")
    print(f"  Total: {predictions['goals']['xG_total']:.2f}")
    
    # Over/Under
    print("\nOver/Under 2.5:")
    print(f"  Over:   {predictions['over_under_2.5']['pOver']*100:.1f}%")
    print(f"  Under:  {predictions['over_under_2.5']['pUnder']*100:.1f}%")
    
    # Asian Handicap
    print("\nAsian Handicap 0.0:")
    print(f"  Home Win:  {predictions['asian_handicap_0']['home']['win']*100:.1f}%")
    print(f"  Push:      {predictions['asian_handicap_0']['home']['push']*100:.1f}%")
    print(f"  Away Win:  {predictions['asian_handicap_0']['away']['win']*100:.1f}%")
    
    # Corners
    print("\nCorners Esperados:")
    print(f"  {predictions['match_info']['home_team']}: {predictions['corners']['corners_home']:.1f}")
    print(f"  {predictions['match_info']['away_team']}: {predictions['corners']['corners_away']:.1f}")
    print(f"  Total: {predictions['corners']['corners_total']:.1f}")
    
    # Tarjetas
    print("\nTarjetas Esperadas:")
    print(f"  Amarillas: {predictions['cards']['yellow_cards']:.1f}")
    print(f"  Rojas:     {predictions['cards']['red_cards']:.2f}")
    print(f"  Total:     {predictions['cards']['total_cards']:.1f}")
    
    # Tiros
    print("\nTiros Esperados:")
    print(f"  {predictions['match_info']['home_team']}: {predictions['shots']['shots_home']:.1f}")
    print(f"  {predictions['match_info']['away_team']}: {predictions['shots']['shots_away']:.1f}")
    print(f"  A puerta (Home): {predictions['shots']['shots_on_target_home']:.1f}")
    print(f"  A puerta (Away): {predictions['shots']['shots_on_target_away']:.1f}")
    
    print("\n" + "=" * 70)


def main():
    parser = argparse.ArgumentParser(description='Predecir partidos')
    parser.add_argument('--home', type=str, help='Equipo local')
    parser.add_argument('--away', type=str, help='Equipo visitante')
    parser.add_argument('--league', type=str, default='E0', help='Liga (E0, SP1, etc.)')
    
    args = parser.parse_args()
    
    # Crear predictor
    predictor = MatchPredictor()
    predictor.load_and_train()
    
    # Si no se especifican equipos, usar ejemplo
    if not args.home or not args.away:
        print("\nEJEMPLO: Manchester City vs Liverpool")
        print("(Usa --home y --away para tu propio partido)")
        
        # Datos de ejemplo - usar partido real del dataset
        df = predictor.df_historical
        last_match = df.tail(1).iloc[0].to_dict()
        
        match_data = {
            'HomeTeam': last_match.get('HomeTeam', 'Manchester City'),
            'AwayTeam': last_match.get('AwayTeam', 'Liverpool'),
            'League': last_match.get('League', 'E0'),
            'Date': '2025-10-25',
            'EloHome': last_match.get('EloHome', 2000),
            'EloAway': last_match.get('EloAway', 1950),
            'Home_GD_roll5': last_match.get('Home_GD_roll5', 8),
            'Away_GD_roll5': last_match.get('Away_GD_roll5', 6),
            'B365H': last_match.get('B365H', 1.85),
            'B365D': last_match.get('B365D', 3.60),
            'B365A': last_match.get('B365A', 4.20),
            'Home_GF_roll5': last_match.get('Home_GF_roll5', 10),
            'Home_GA_roll5': last_match.get('Home_GA_roll5', 4),
            'Away_GF_roll5': last_match.get('Away_GF_roll5', 8),
            'Away_GA_roll5': last_match.get('Away_GA_roll5', 5)
        }
    else:
        # Buscar equipos en el dataset
        df = predictor.df_historical
        home_matches = df[df['HomeTeam'] == args.home].tail(1)
        away_matches = df[df['AwayTeam'] == args.away].tail(1)
        
        if len(home_matches) == 0 or len(away_matches) == 0:
            print(f"\nERROR: No se encontraron datos para {args.home} o {args.away}")
            return
        
        match_data = {
            'HomeTeam': args.home,
            'AwayTeam': args.away,
            'League': args.league,
            'Date': datetime.now().strftime('%Y-%m-%d'),
            'EloHome': home_matches.iloc[0]['EloHome'],
            'EloAway': away_matches.iloc[0]['EloAway'],
            'Home_GD_roll5': home_matches.iloc[0].get('Home_GD_roll5', 0),
            'Away_GD_roll5': away_matches.iloc[0].get('Away_GD_roll5', 0),
            'B365H': 2.00,
            'B365D': 3.40,
            'B365A': 3.80
        }
    
    # Hacer predicción
    predictions = predictor.predict_all(match_data)
    print_predictions(predictions)
    
    # Guardar
    output_file = REPORTS / f"prediction_{match_data['HomeTeam']}_vs_{match_data['AwayTeam']}.json"
    import json
    with open(output_file, 'w') as f:
        json.dump(predictions, f, indent=2)
    
    print(f"\nPredicción guardada en: {output_file}")


if __name__ == "__main__":
    main()

