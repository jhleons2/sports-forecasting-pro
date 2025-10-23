#!/usr/bin/env python3
"""
Sistema de Análisis Automático de Partidos
==========================================

Analiza probabilidades, calcula edges, y genera recomendaciones automáticas
para cada partido basado en las predicciones del modelo.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


# Diccionario de traducciones
TRANSLATIONS = {
    'home': 'Local',
    'draw': 'Empate',
    'away': 'Visitante',
    'Asian Handicap': 'Hándicap Asiático',
    'Over/Under 2.5': 'Más/Menos 2.5 Goles',
    '1X2': 'Resultado Final'
}


def translate_term(term: str) -> str:
    """Traduce términos técnicos al español"""
    return TRANSLATIONS.get(term, term)


class BetRecommendation(Enum):
    """Tipos de recomendación de apuesta"""
    STRONG_VALUE = "STRONG_VALUE"      # Edge > 10%
    VALUE = "VALUE"                    # Edge 5-10%
    WEAK_VALUE = "WEAK_VALUE"          # Edge 2-5%
    NO_VALUE = "NO_VALUE"              # Edge < 2%
    AVOID = "AVOID"                    # Edge negativo


class MatchOutcome(Enum):
    """Posibles resultados del partido"""
    HOME_FAVORITE = "HOME_FAVORITE"
    AWAY_FAVORITE = "AWAY_FAVORITE"
    BALANCED = "BALANCED"
    VERY_UNBALANCED = "VERY_UNBALANCED"


@dataclass
class EdgeAnalysis:
    """Análisis de edge para una apuesta"""
    market: str
    selection: str
    model_prob: float
    implied_prob: float
    odds: float
    edge: float
    recommendation: BetRecommendation
    kelly_fraction: float
    confidence: str


@dataclass
class MatchAnalysis:
    """Análisis completo de un partido"""
    home_team: str
    away_team: str
    match_outcome: MatchOutcome
    favorite_team: str
    favorite_prob: float
    underdog_prob: float
    balanced_score: float
    risk_level: str
    edge_analysis: List[EdgeAnalysis]
    key_insights: List[str]
    recommended_bets: List[Dict]
    avoid_bets: List[Dict]


class MatchAnalyzer:
    """
    Analizador automático de partidos que genera insights y recomendaciones
    """
    
    def __init__(self):
        self.edge_thresholds = {
            BetRecommendation.STRONG_VALUE: 0.10,
            BetRecommendation.VALUE: 0.05,
            BetRecommendation.WEAK_VALUE: 0.02,
            BetRecommendation.NO_VALUE: 0.00,
            BetRecommendation.AVOID: -999
        }
    
    def analyze_match(self, match_data: Dict, predictions: Dict) -> MatchAnalysis:
        """
        Analiza un partido completo y genera recomendaciones
        
        Args:
            match_data: Datos del partido (equipos, ELO, etc.)
            predictions: Predicciones del modelo (1X2, AH, OU, etc.)
            
        Returns:
            MatchAnalysis: Análisis completo del partido
        """
        # Análisis básico del partido
        outcome_analysis = self._analyze_match_outcome(predictions)
        
        # Análisis de edges
        edge_analysis = self._analyze_all_edges(match_data, predictions)
        
        # Generar insights
        insights = self._generate_insights(match_data, predictions, outcome_analysis)
        
        # Recomendaciones finales
        recommended_bets = self._get_recommended_bets(edge_analysis)
        avoid_bets = self._get_avoid_bets(edge_analysis)
        
        return MatchAnalysis(
            home_team=match_data['HomeTeam'],
            away_team=match_data['AwayTeam'],
            match_outcome=outcome_analysis['outcome'],
            favorite_team=outcome_analysis['favorite_team'],
            favorite_prob=outcome_analysis['favorite_prob'],
            underdog_prob=outcome_analysis['underdog_prob'],
            balanced_score=outcome_analysis['balanced_score'],
            risk_level=outcome_analysis['risk_level'],
            edge_analysis=edge_analysis,
            key_insights=insights,
            recommended_bets=recommended_bets,
            avoid_bets=avoid_bets
        )
    
    def _analyze_match_outcome(self, predictions: Dict) -> Dict:
        """Analiza el tipo de partido basado en las probabilidades"""
        
        # Probabilidades 1X2
        home_prob = predictions.get('1x2', {}).get('home', 0.33)
        draw_prob = predictions.get('1x2', {}).get('draw', 0.33)
        away_prob = predictions.get('1x2', {}).get('away', 0.34)
        
        # Determinar favorito
        probs = {'home': home_prob, 'away': away_prob}
        favorite = max(probs, key=probs.get)
        favorite_prob = probs[favorite]
        underdog_prob = min(probs.values())
        
        # Calcular score de equilibrio
        max_prob = max(home_prob, away_prob)
        balanced_score = 1 - abs(max_prob - 0.5) * 2  # 1 = perfectamente equilibrado, 0 = muy desequilibrado
        
        # Determinar tipo de partido
        if max_prob > 0.65:
            outcome = MatchOutcome.VERY_UNBALANCED
            risk_level = "HIGH"
        elif max_prob > 0.55:
            outcome = MatchOutcome.HOME_FAVORITE if favorite == 'home' else MatchOutcome.AWAY_FAVORITE
            risk_level = "MEDIUM"
        else:
            outcome = MatchOutcome.BALANCED
            risk_level = "LOW"
        
        return {
            'outcome': outcome,
            'favorite_team': favorite,
            'favorite_prob': favorite_prob,
            'underdog_prob': underdog_prob,
            'balanced_score': balanced_score,
            'risk_level': risk_level
        }
    
    def _analyze_all_edges(self, match_data: Dict, predictions: Dict) -> List[EdgeAnalysis]:
        """Analiza edges para todos los mercados disponibles"""
        
        edge_analyses = []
        
        # Análisis 1X2
        if '1x2' in predictions:
            edge_analyses.extend(self._analyze_1x2_edges(match_data, predictions['1x2']))
        
        # Análisis Asian Handicap
        if 'asian_handicap_0' in predictions:
            edge_analyses.extend(self._analyze_ah_edges(match_data, predictions['asian_handicap_0']))
        
        # Análisis Over/Under
        if 'over_under' in predictions:
            edge_analyses.extend(self._analyze_ou_edges(match_data, predictions['over_under']))
        
        return edge_analyses
    
    def _analyze_1x2_edges(self, match_data: Dict, predictions: Dict) -> List[EdgeAnalysis]:
        """Analiza edges del mercado 1X2"""
        
        edges = []
        
        # Probabilidades del modelo
        model_probs = {
            'home': predictions.get('home', 0.33),
            'draw': predictions.get('draw', 0.33),
            'away': predictions.get('away', 0.34)
        }
        
        # Calcular odds "justas" con margen de bookmaker (5% de margen)
        # Si no hay cuotas reales, usamos las del modelo con margen
        if 'B365H' not in match_data or match_data.get('B365H') is None or pd.isna(match_data.get('B365H')):
            # Cuotas estimadas con margen del 5%
            margin = 1.05
            implied_odds = {
                'home': (1 / model_probs['home']) * margin if model_probs['home'] > 0.01 else 50.0,
                'draw': (1 / model_probs['draw']) * margin if model_probs['draw'] > 0.01 else 50.0,
                'away': (1 / model_probs['away']) * margin if model_probs['away'] > 0.01 else 50.0
            }
        else:
            # Usar cuotas reales de Bet365
            implied_odds = {
                'home': match_data.get('B365H', 2.50),
                'draw': match_data.get('B365D', 3.30),
                'away': match_data.get('B365A', 2.80)
            }
        
        for selection, model_prob in model_probs.items():
            odds = implied_odds[selection]
            implied_prob = 1 / odds
            edge = model_prob - implied_prob
            
            recommendation = self._get_recommendation(edge)
            kelly_fraction = self._calculate_kelly_fraction(model_prob, odds)
            confidence = self._get_confidence_level(abs(edge))
            
            edges.append(EdgeAnalysis(
                market=translate_term("1X2"),
                selection=translate_term(selection),
                model_prob=model_prob,
                implied_prob=implied_prob,
                odds=odds,
                edge=edge,
                recommendation=recommendation,
                kelly_fraction=kelly_fraction,
                confidence=confidence
            ))
        
        return edges
    
    def _analyze_ah_edges(self, match_data: Dict, predictions: Dict) -> List[EdgeAnalysis]:
        """Analiza edges del Asian Handicap"""
        
        edges = []
        ah_line = match_data.get('AHh', 0.0)
        
        # Probabilidades del modelo para AH
        home_pred = predictions.get('home', {})
        away_pred = predictions.get('away', {})
        
        # Manejar tanto diccionario como float directo
        if isinstance(home_pred, dict):
            home_prob = home_pred.get('win', 0.5)
        else:
            home_prob = home_pred if home_pred is not None else 0.5
            
        if isinstance(away_pred, dict):
            away_prob = away_pred.get('win', 0.5)
        else:
            away_prob = away_pred if away_pred is not None else 0.5
        
        model_probs = {
            'home': home_prob,
            'away': away_prob
        }
        
        # Calcular odds AH
        if 'B365AHH' not in match_data or match_data.get('B365AHH') is None or pd.isna(match_data.get('B365AHH')):
            # Cuotas estimadas con margen del 2-3%
            margin = 1.025
            implied_odds = {
                'home': (1 / home_prob) * margin if home_prob > 0.01 else 50.0,
                'away': (1 / away_prob) * margin if away_prob > 0.01 else 50.0
            }
        else:
            # Usar cuotas reales
            implied_odds = {
                'home': match_data.get('B365AHH', 1.95),
                'away': match_data.get('B365AHA', 1.95)
            }
        
        for selection, model_prob in model_probs.items():
            odds = implied_odds[selection]
            implied_prob = 1 / odds
            edge = model_prob - implied_prob
            
            recommendation = self._get_recommendation(edge)
            kelly_fraction = self._calculate_kelly_fraction(model_prob, odds)
            confidence = self._get_confidence_level(abs(edge))
            
            edges.append(EdgeAnalysis(
                market=translate_term("Asian Handicap"),
                selection=f"{translate_term(selection)} ({ah_line:+.2f})",
                model_prob=model_prob,
                implied_prob=implied_prob,
                odds=odds,
                edge=edge,
                recommendation=recommendation,
                kelly_fraction=kelly_fraction,
                confidence=confidence
            ))
        
        return edges
    
    def _analyze_ou_edges(self, match_data: Dict, predictions: Dict) -> List[EdgeAnalysis]:
        """Analiza edges del Over/Under"""
        
        edges = []
        
        # Probabilidades del modelo
        over_pred = predictions.get('over', 0.5)
        under_pred = predictions.get('under', 0.5)
        
        # Asegurar que son floats
        over_prob = float(over_pred) if over_pred is not None else 0.5
        under_prob = float(under_pred) if under_pred is not None else 0.5
        
        # Traducciones para Over/Under
        ou_translations = {
            'over': 'Más de 2.5',
            'under': 'Menos de 2.5'
        }
        
        model_probs = {
            'over': over_prob,
            'under': under_prob
        }
        
        # Calcular odds O/U
        if 'B365>2.5' not in match_data or match_data.get('B365>2.5') is None or pd.isna(match_data.get('B365>2.5')):
            # Cuotas estimadas con margen del 3-4%
            margin = 1.035
            implied_odds = {
                'over': (1 / over_prob) * margin if over_prob > 0.01 else 50.0,
                'under': (1 / under_prob) * margin if under_prob > 0.01 else 50.0
            }
        else:
            # Usar cuotas reales
            implied_odds = {
                'over': match_data.get('B365>2.5', 2.00),
                'under': match_data.get('B365<2.5', 1.90)
            }
        
        for selection, model_prob in model_probs.items():
            odds = implied_odds[selection]
            implied_prob = 1 / odds
            edge = model_prob - implied_prob
            
            recommendation = self._get_recommendation(edge)
            kelly_fraction = self._calculate_kelly_fraction(model_prob, odds)
            confidence = self._get_confidence_level(abs(edge))
            
            edges.append(EdgeAnalysis(
                market=translate_term("Over/Under 2.5"),
                selection=ou_translations[selection],
                model_prob=model_prob,
                implied_prob=implied_prob,
                odds=odds,
                edge=edge,
                recommendation=recommendation,
                kelly_fraction=kelly_fraction,
                confidence=confidence
            ))
        
        return edges
    
    def _get_recommendation(self, edge: float) -> BetRecommendation:
        """Determina la recomendación basada en el edge"""
        
        if edge >= self.edge_thresholds[BetRecommendation.STRONG_VALUE]:
            return BetRecommendation.STRONG_VALUE
        elif edge >= self.edge_thresholds[BetRecommendation.VALUE]:
            return BetRecommendation.VALUE
        elif edge >= self.edge_thresholds[BetRecommendation.WEAK_VALUE]:
            return BetRecommendation.WEAK_VALUE
        elif edge >= self.edge_thresholds[BetRecommendation.NO_VALUE]:
            return BetRecommendation.NO_VALUE
        else:
            return BetRecommendation.AVOID
    
    def _calculate_kelly_fraction(self, model_prob: float, odds: float) -> float:
        """Calcula la fracción de Kelly para sizing de apuestas"""
        
        if model_prob <= 0 or odds <= 1:
            return 0.0
        
        # Fórmula de Kelly: f = (bp - q) / b
        # donde b = odds - 1, p = probabilidad de ganar, q = probabilidad de perder
        b = odds - 1
        p = model_prob
        q = 1 - p
        
        kelly = (b * p - q) / b
        
        # Limitar Kelly a un máximo del 25% por seguridad
        return max(0, min(kelly, 0.25))
    
    def _get_confidence_level(self, edge_magnitude: float) -> str:
        """Determina el nivel de confianza basado en la magnitud del edge"""
        
        if edge_magnitude >= 0.10:
            return "MUY ALTA"
        elif edge_magnitude >= 0.05:
            return "ALTA"
        elif edge_magnitude >= 0.02:
            return "MEDIA"
        else:
            return "BAJA"
    
    def _generate_insights(self, match_data: Dict, predictions: Dict, outcome_analysis: Dict) -> List[str]:
        """Genera insights automáticos sobre el partido"""
        
        insights = []
        
        # Insight sobre equilibrio
        if outcome_analysis['balanced_score'] > 0.7:
            insights.append(f"Partido muy equilibrado (score: {outcome_analysis['balanced_score']:.2f}) - ideal para estrategias conservadoras")
        elif outcome_analysis['balanced_score'] < 0.3:
            insights.append(f"Partido muy desequilibrado (score: {outcome_analysis['balanced_score']:.2f}) - alto riesgo pero posible alto reward")
        
        # Insight sobre favorito
        favorite = outcome_analysis['favorite_team']
        favorite_prob = outcome_analysis['favorite_prob']
        
        if favorite_prob > 0.6:
            insights.append(f"{favorite.title()} es favorito claro ({favorite_prob:.1%}) - buscar value en underdog")
        elif favorite_prob < 0.52:
            insights.append("Partido sin favorito claro - todas las opciones tienen chances similares")
        
        # Insight sobre ELO
        elo_diff = match_data.get('EloHome', 1500) - match_data.get('EloAway', 1500)
        if abs(elo_diff) > 100:
            insights.append(f"Gran diferencia de ELO ({elo_diff:+.0f}) - el modelo tiene alta confianza")
        elif abs(elo_diff) < 25:
            insights.append("Equipos muy parejos según ELO - predicciones más inciertas")
        
        # Insight sobre Asian Handicap
        ah_line = match_data.get('AHh', 0.0)
        if abs(ah_line) >= 1.5:
            insights.append(f"Handicap grande ({ah_line:+.2f}) - oportunidades en AH para equipos fuertes")
        elif abs(ah_line) <= 0.25:
            insights.append("Handicap pequeño - partido muy equilibrado")
        
        return insights
    
    def _get_recommended_bets(self, edge_analyses: List[EdgeAnalysis]) -> List[Dict]:
        """Obtiene las mejores apuestas recomendadas"""
        
        recommended = []
        
        for analysis in edge_analyses:
            if analysis.recommendation in [BetRecommendation.STRONG_VALUE, BetRecommendation.VALUE]:
                recommended.append({
                    'market': analysis.market,
                    'selection': analysis.selection,
                    'edge': f"{analysis.edge:.1%}",
                    'odds': analysis.odds,
                    'kelly': f"{analysis.kelly_fraction:.1%}",
                    'confidence': analysis.confidence,
                    'recommendation': analysis.recommendation.value
                })
        
        # Ordenar por edge descendente
        recommended.sort(key=lambda x: float(x['edge'].replace('%', '')), reverse=True)
        
        return recommended
    
    def _get_avoid_bets(self, edge_analyses: List[EdgeAnalysis]) -> List[Dict]:
        """Obtiene las apuestas a evitar"""
        
        avoid = []
        
        for analysis in edge_analyses:
            if analysis.recommendation == BetRecommendation.AVOID:
                avoid.append({
                    'market': analysis.market,
                    'selection': analysis.selection,
                    'edge': f"{analysis.edge:.1%}",
                    'odds': analysis.odds,
                    'reason': "Edge negativo - no recomendado"
                })
        
        return avoid


def analyze_single_match(match_data: Dict, predictions: Dict) -> MatchAnalysis:
    """
    Función helper para analizar un solo partido
    
    Args:
        match_data: Datos del partido
        predictions: Predicciones del modelo
        
    Returns:
        MatchAnalysis: Análisis completo
    """
    analyzer = MatchAnalyzer()
    return analyzer.analyze_match(match_data, predictions)


if __name__ == "__main__":
    # Ejemplo de uso
    match_data_example = {
        'HomeTeam': 'Chelsea FC',
        'AwayTeam': 'Sunderland AFC',
        'EloHome': 1500,
        'EloAway': 1500,
        'AHh': 0.0,
        'B365H': 3.50,
        'B365D': 3.20,
        'B365A': 2.10,
        'B365AHH': 1.95,
        'B365AHA': 1.95,
        'B365>2.5': 2.00,
        'B365<2.5': 1.90
    }
    
    predictions_example = {
        '1x2': {
            'home': 0.261,
            'draw': 0.268,
            'away': 0.471
        },
        'asian_handicap_0': {
            'home': {'win': 0.50},
            'away': {'win': 0.50}
        },
        'over_under': {
            'over': 0.52,
            'under': 0.48
        }
    }
    
    analysis = analyze_single_match(match_data_example, predictions_example)
    
    print("=== ANÁLISIS DEL PARTIDO ===")
    print(f"Partido: {analysis.home_team} vs {analysis.away_team}")
    print(f"Favorito: {analysis.favorite_team} ({analysis.favorite_prob:.1%})")
    print(f"Nivel de riesgo: {analysis.risk_level}")
    print(f"Score de equilibrio: {analysis.balanced_score:.2f}")
    
    print("\n=== INSIGHTS ===")
    for insight in analysis.key_insights:
        print(f"• {insight}")
    
    print("\n=== RECOMENDACIONES ===")
    for bet in analysis.recommended_bets:
        print(f"✅ {bet['market']} - {bet['selection']} @ {bet['odds']} (Edge: {bet['edge']})")
    
    print("\n=== EVITAR ===")
    for bet in analysis.avoid_bets:
        print(f"❌ {bet['market']} - {bet['selection']} @ {bet['odds']} (Edge: {bet['edge']})")
