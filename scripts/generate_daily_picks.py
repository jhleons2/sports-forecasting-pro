"""
Generador de Picks Diarios

Genera automáticamente picks de valor para los próximos partidos.
Incluye todos los mercados: 1X2, AH, OU, Corners, Tarjetas

Uso:
    python scripts/generate_daily_picks.py --days 7 --min-edge 0.05
"""

import pandas as pd
import numpy as np
from pathlib import Path
import argparse
from datetime import datetime, timedelta

from scripts.predict_matches import MatchPredictor

REPORTS = Path("reports"); REPORTS.mkdir(parents=True, exist_ok=True)


def calculate_value_bet(prob_model, odds, min_edge=0.05):
    """
    Calcula si hay value en una apuesta.
    
    Parameters:
    -----------
    prob_model : float
        Probabilidad del modelo
    odds : float
        Cuota ofrecida
    min_edge : float
        Edge mínimo requerido
    
    Returns:
    --------
    dict con info de value bet o None
    """
    prob_implied = 1.0 / odds
    edge = prob_model - prob_implied
    
    if edge >= min_edge:
        ev = prob_model * (odds - 1.0) - (1.0 - prob_model)
        return {
            'edge': edge,
            'ev': ev,
            'prob_model': prob_model,
            'prob_implied': prob_implied,
            'odds': odds
        }
    return None


class DailyPicksGenerator:
    """
    Generador automático de picks diarios.
    """
    
    def __init__(self, min_edge=0.05):
        self.predictor = MatchPredictor()
        self.min_edge = min_edge
        self.picks = []
        
    def load_upcoming_matches(self):
        """
        Carga próximos partidos.
        
        En producción, esto vendría de una API (football-data.org, etc.)
        Por ahora, usamos los últimos del dataset como ejemplo.
        """
        print("Cargando próximos partidos...")
        
        # Cargar datos
        df = pd.read_parquet(Path("data/processed/matches.parquet"))
        
        # Por ahora, usar últimos 20 partidos como "próximos"
        # En producción, reemplazar con API de fixtures
        upcoming = df.tail(20).copy()
        
        print(f"  {len(upcoming)} partidos cargados")
        return upcoming
    
    def analyze_match(self, match_data):
        """
        Analiza un partido y encuentra picks de valor.
        
        Parameters:
        -----------
        match_data : dict/Series
            Datos del partido
        
        Returns:
        --------
        list de picks encontrados
        """
        picks = []
        
        # Hacer predicciones
        predictions = self.predictor.predict_all(match_data)
        
        # ===================================================================
        # MERCADO 1X2
        # ===================================================================
        odds_1x2 = {
            'H': match_data.get('B365H', 2.5),
            'D': match_data.get('B365D', 3.3),
            'A': match_data.get('B365A', 3.2)
        }
        
        for outcome, odds in odds_1x2.items():
            prob_key = {'H': 'pH', 'D': 'pD', 'A': 'pA'}[outcome]
            prob = predictions['1x2'][prob_key]
            
            value = calculate_value_bet(prob, odds, self.min_edge)
            if value and odds >= 2.20:  # Filtro adicional
                picks.append({
                    'market': '1X2',
                    'selection': {'H': 'Home', 'D': 'Draw', 'A': 'Away'}[outcome],
                    **value,
                    'match_info': predictions['match_info']
                })
        
        # ===================================================================
        # MERCADO OVER/UNDER 2.5
        # ===================================================================
        ou_odds = {
            'Over': match_data.get('B365>2.5', 2.0),
            'Under': match_data.get('B365<2.5', 2.0)
        }
        
        for outcome, odds in ou_odds.items():
            prob_key = 'pOver' if outcome == 'Over' else 'pUnder'
            prob = predictions['over_under_2.5'][prob_key]
            
            value = calculate_value_bet(prob, odds, self.min_edge)
            if value and odds >= 1.85:
                picks.append({
                    'market': 'OU 2.5',
                    'selection': outcome,
                    **value,
                    'match_info': predictions['match_info']
                })
        
        # ===================================================================
        # MERCADO ASIAN HANDICAP
        # ===================================================================
        ah_line = match_data.get('AHh', 0.0)
        ah_odds = {
            'Home': match_data.get('B365AHH', 1.95),
            'Away': match_data.get('B365AHA', 1.95)
        }
        
        for side, odds in ah_odds.items():
            prob = predictions['asian_handicap_0'][side.lower()]['win']
            
            value = calculate_value_bet(prob, odds, self.min_edge)
            if value and odds >= 1.90:
                picks.append({
                    'market': f'AH {ah_line}',
                    'selection': side,
                    **value,
                    'match_info': predictions['match_info']
                })
        
        # ===================================================================
        # MERCADO CORNERS (OVER/UNDER)
        # ===================================================================
        total_corners = predictions['corners']['corners_total']
        
        # Over 10.5 corners
        if total_corners > 10.5:
            prob = min(0.95, (total_corners - 10.5) / 2.0 + 0.50)
            value = calculate_value_bet(prob, 2.0, self.min_edge)
            if value:
                picks.append({
                    'market': 'Corners O/U',
                    'selection': 'Over 10.5',
                    **value,
                    'match_info': predictions['match_info'],
                    'expected_corners': total_corners
                })
        else:
            prob = min(0.95, 0.50 + (10.5 - total_corners) / 2.0)
            value = calculate_value_bet(prob, 1.90, self.min_edge)
            if value:
                picks.append({
                    'market': 'Corners O/U',
                    'selection': 'Under 10.5',
                    **value,
                    'match_info': predictions['match_info'],
                    'expected_corners': total_corners
                })
        
        # ===================================================================
        # MERCADO TARJETAS (OVER/UNDER)
        # ===================================================================
        total_cards = predictions['cards']['total_cards']
        
        # Over 3.5 cards
        if total_cards > 3.5:
            prob = min(0.90, (total_cards - 3.5) / 1.5 + 0.55)
            value = calculate_value_bet(prob, 2.10, self.min_edge)
            if value:
                picks.append({
                    'market': 'Cards O/U',
                    'selection': 'Over 3.5',
                    **value,
                    'match_info': predictions['match_info'],
                    'expected_cards': total_cards
                })
        
        return picks
    
    def generate_picks(self):
        """
        Genera todos los picks.
        """
        print("\n" + "=" * 70)
        print("GENERADOR DE PICKS DIARIOS")
        print("=" * 70)
        
        # Cargar y entrenar modelos
        self.predictor.load_and_train()
        
        # Cargar próximos partidos
        upcoming_matches = self.load_upcoming_matches()
        
        print(f"\nAnalizando {len(upcoming_matches)} partidos...")
        print(f"Edge mínimo: {self.min_edge*100:.0f}%")
        print("")
        
        # Analizar cada partido
        all_picks = []
        for idx, match in upcoming_matches.iterrows():
            picks = self.analyze_match(match)
            all_picks.extend(picks)
        
        # Ordenar por EV (Expected Value)
        all_picks.sort(key=lambda x: x['ev'], reverse=True)
        
        print(f"\n{len(all_picks)} PICKS DE VALOR ENCONTRADOS:")
        print("=" * 70)
        
        # Mostrar picks
        for i, pick in enumerate(all_picks[:20], 1):  # Top 20
            info = pick['match_info']
            print(f"\n{i}. {info['home_team']} vs {info['away_team']}")
            print(f"   Liga: {info['league']}")
            print(f"   Mercado: {pick['market']} - {pick['selection']}")
            print(f"   Probabilidad modelo: {pick['prob_model']*100:.1f}%")
            print(f"   Cuota: {pick['odds']:.2f}")
            print(f"   Edge: {pick['edge']*100:.1f}%")
            print(f"   EV: {pick['ev']*100:.1f}%")
            
            if 'expected_corners' in pick:
                print(f"   Corners esperados: {pick['expected_corners']:.1f}")
            if 'expected_cards' in pick:
                print(f"   Tarjetas esperadas: {pick['expected_cards']:.1f}")
        
        print("\n" + "=" * 70)
        
        # Guardar en CSV
        if all_picks:
            df_picks = pd.DataFrame(all_picks)
            output_file = REPORTS / f"daily_picks_{datetime.now().strftime('%Y%m%d')}.csv"
            df_picks.to_csv(output_file, index=False)
            print(f"\nPicks guardados en: {output_file}")
        
        return all_picks


def main():
    parser = argparse.ArgumentParser(description='Generar picks diarios')
    parser.add_argument('--min-edge', type=float, default=0.05, 
                       help='Edge mínimo requerido (default: 0.05 = 5%)')
    parser.add_argument('--days', type=int, default=7,
                       help='Días hacia adelante (default: 7)')
    
    args = parser.parse_args()
    
    # Generar picks
    generator = DailyPicksGenerator(min_edge=args.min_edge)
    picks = generator.generate_picks()
    
    print(f"\nTotal picks de valor: {len(picks)}")
    print("Listo para apostar!")


if __name__ == "__main__":
    main()

