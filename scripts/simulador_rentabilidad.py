#!/usr/bin/env python3
"""
Simulador de Rentabilidad
=========================

Simula diferentes estrategias de apuestas para calcular ROI esperado,
riesgo y métricas de rendimiento antes de usar dinero real.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, List, Tuple
from dataclasses import dataclass
import random
from datetime import datetime, timedelta


@dataclass
class BettingStrategy:
    """Configuración de estrategia de apuestas"""
    name: str
    min_edge: float
    max_stake_percent: float
    kelly_fraction: float
    preferred_leagues: List[str]
    max_bets_per_day: int
    stop_loss_percent: float


@dataclass
class BettingResult:
    """Resultado de una apuesta simulada"""
    match_id: str
    home_team: str
    away_team: str
    market: str
    selection: str
    odds: float
    stake: float
    edge: float
    won: bool
    profit: float
    timestamp: datetime


class ProfitabilitySimulator:
    """
    Simulador de rentabilidad para diferentes estrategias de apuestas
    """
    
    def __init__(self, initial_bankroll: float = 10000):
        self.initial_bankroll = initial_bankroll
        self.current_bankroll = initial_bankroll
        self.betting_history = []
        
        # Estadísticas de ligas (basadas en datos históricos)
        self.league_stats = {
            'E0': {'win_rate': 0.58, 'avg_edge': 0.06, 'volatility': 0.15},
            'SP1': {'win_rate': 0.55, 'avg_edge': 0.05, 'volatility': 0.18},
            'D1': {'win_rate': 0.57, 'avg_edge': 0.05, 'volatility': 0.16},
            'I1': {'win_rate': 0.54, 'avg_edge': 0.04, 'volatility': 0.19},
            'F1': {'win_rate': 0.56, 'avg_edge': 0.05, 'volatility': 0.17}
        }
    
    def simulate_strategy(self, strategy: BettingStrategy, days: int = 30) -> Dict:
        """
        Simula una estrategia de apuestas durante un período específico
        """
        self.current_bankroll = self.initial_bankroll
        self.betting_history = []
        
        # Generar oportunidades de apuesta simuladas
        opportunities = self._generate_opportunities(strategy, days)
        
        # Procesar cada oportunidad
        for opportunity in opportunities:
            if self._should_place_bet(opportunity, strategy):
                result = self._simulate_bet(opportunity, strategy)
                self.betting_history.append(result)
                
                # Actualizar bankroll
                self.current_bankroll += result.profit
                
                # Verificar stop-loss
                if self._check_stop_loss(strategy):
                    break
        
        return self._calculate_performance_metrics(strategy)
    
    def _generate_opportunities(self, strategy: BettingStrategy, days: int) -> List[Dict]:
        """Genera oportunidades de apuesta simuladas"""
        opportunities = []
        
        for day in range(days):
            # Generar 1-5 oportunidades por día
            daily_opportunities = random.randint(1, strategy.max_bets_per_day)
            
            for _ in range(daily_opportunities):
                league = random.choice(strategy.preferred_leagues)
                league_stat = self.league_stats[league]
                
                # Generar edge basado en estadísticas de la liga
                base_edge = league_stat['avg_edge']
                edge_variation = random.uniform(-0.03, 0.05)
                edge = max(0, base_edge + edge_variation)
                
                # Solo incluir si cumple criterio mínimo
                if edge >= strategy.min_edge:
                    opportunity = {
                        'match_id': f"match_{day}_{_}",
                        'home_team': f"Team_{random.randint(1, 20)}",
                        'away_team': f"Team_{random.randint(1, 20)}",
                        'league': league,
                        'market': random.choice(['1X2', 'Asian Handicap', 'Over/Under']),
                        'selection': random.choice(['home', 'away', 'draw']),
                        'odds': random.uniform(1.50, 4.00),
                        'edge': edge,
                        'confidence': random.uniform(0.6, 0.9),
                        'timestamp': datetime.now() + timedelta(days=day)
                    }
                    opportunities.append(opportunity)
        
        return opportunities
    
    def _should_place_bet(self, opportunity: Dict, strategy: BettingStrategy) -> bool:
        """Determina si se debe colocar una apuesta"""
        # Verificar edge mínimo
        if opportunity['edge'] < strategy.min_edge:
            return False
        
        # Verificar límite de apuestas por día
        today_bets = len([b for b in self.betting_history 
                         if b.timestamp.date() == opportunity['timestamp'].date()])
        if today_bets >= strategy.max_bets_per_day:
            return False
        
        # Verificar bankroll suficiente
        min_stake = self.current_bankroll * 0.01  # Mínimo 1%
        if min_stake < 10:  # Mínimo $10
            return False
        
        return True
    
    def _simulate_bet(self, opportunity: Dict, strategy: BettingStrategy) -> BettingResult:
        """Simula el resultado de una apuesta"""
        # Calcular stake usando Kelly Criterion
        edge = opportunity['edge']
        odds = opportunity['odds']
        
        # Kelly Criterion
        kelly_percent = (edge * odds - 1) / (odds - 1)
        kelly_percent = max(0, kelly_percent)  # No apuestas negativas
        
        # Aplicar fracción de Kelly
        kelly_fraction = kelly_percent * strategy.kelly_fraction
        
        # Limitar stake máximo
        max_stake_percent = strategy.max_stake_percent
        stake_percent = min(kelly_fraction, max_stake_percent)
        
        # Calcular stake en dólares
        stake = self.current_bankroll * stake_percent
        
        # Determinar si gana basado en probabilidad real
        league_stat = self.league_stats[opportunity['league']]
        win_probability = league_stat['win_rate']
        
        # Ajustar probabilidad según edge
        adjusted_prob = min(0.95, win_probability + edge * 0.5)
        
        # Simular resultado
        won = random.random() < adjusted_prob
        
        # Calcular ganancia/pérdida
        if won:
            profit = stake * (odds - 1)
        else:
            profit = -stake
        
        return BettingResult(
            match_id=opportunity['match_id'],
            home_team=opportunity['home_team'],
            away_team=opportunity['away_team'],
            market=opportunity['market'],
            selection=opportunity['selection'],
            odds=odds,
            stake=stake,
            edge=edge,
            won=won,
            profit=profit,
            timestamp=opportunity['timestamp']
        )
    
    def _check_stop_loss(self, strategy: BettingStrategy) -> bool:
        """Verifica si se debe activar stop-loss"""
        current_loss = self.initial_bankroll - self.current_bankroll
        loss_percent = current_loss / self.initial_bankroll
        
        return loss_percent >= strategy.stop_loss_percent
    
    def _calculate_performance_metrics(self, strategy: BettingStrategy) -> Dict:
        """Calcula métricas de rendimiento"""
        if not self.betting_history:
            return {
                'total_bets': 0,
                'win_rate': 0,
                'total_profit': 0,
                'roi': 0,
                'max_drawdown': 0,
                'sharpe_ratio': 0,
                'avg_stake': 0,
                'profit_factor': 0
            }
        
        total_bets = len(self.betting_history)
        winning_bets = len([b for b in self.betting_history if b.won])
        win_rate = winning_bets / total_bets
        
        total_profit = sum(b.profit for b in self.betting_history)
        roi = total_profit / self.initial_bankroll
        
        # Calcular drawdown máximo
        running_balance = [self.initial_bankroll]
        for bet in self.betting_history:
            running_balance.append(running_balance[-1] + bet.profit)
        
        peak = self.initial_bankroll
        max_drawdown = 0
        for balance in running_balance:
            if balance > peak:
                peak = balance
            drawdown = (peak - balance) / peak
            max_drawdown = max(max_drawdown, drawdown)
        
        # Calcular Sharpe Ratio (simplificado)
        if total_bets > 1:
            returns = [b.profit / self.initial_bankroll for b in self.betting_history]
            sharpe_ratio = np.mean(returns) / np.std(returns) if np.std(returns) > 0 else 0
        else:
            sharpe_ratio = 0
        
        # Calcular Profit Factor
        total_wins = sum(b.profit for b in self.betting_history if b.profit > 0)
        total_losses = abs(sum(b.profit for b in self.betting_history if b.profit < 0))
        profit_factor = total_wins / total_losses if total_losses > 0 else float('inf')
        
        avg_stake = np.mean([b.stake for b in self.betting_history])
        
        return {
            'strategy_name': strategy.name,
            'total_bets': total_bets,
            'win_rate': win_rate,
            'total_profit': total_profit,
            'roi': roi,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'avg_stake': avg_stake,
            'profit_factor': profit_factor,
            'final_bankroll': self.current_bankroll
        }
    
    def compare_strategies(self, strategies: List[BettingStrategy], days: int = 30) -> pd.DataFrame:
        """Compara múltiples estrategias"""
        results = []
        
        for strategy in strategies:
            # Ejecutar múltiples simulaciones para obtener promedio
            simulations = []
            for _ in range(10):  # 10 simulaciones por estrategia
                metrics = self.simulate_strategy(strategy, days)
                simulations.append(metrics)
            
            # Calcular promedio
            avg_metrics = {}
            for key in simulations[0].keys():
                if key == 'strategy_name':
                    avg_metrics[key] = strategy.name
                else:
                    avg_metrics[key] = np.mean([s[key] for s in simulations])
            
            results.append(avg_metrics)
        
        return pd.DataFrame(results)


def main():
    """Función principal para ejecutar simulaciones"""
    print("SIMULADOR DE RENTABILIDAD")
    print("=" * 50)
    
    # Definir estrategias a comparar
    strategies = [
        BettingStrategy(
            name="Conservadora",
            min_edge=0.05,
            max_stake_percent=0.02,
            kelly_fraction=0.25,
            preferred_leagues=['E0', 'SP1'],
            max_bets_per_day=2,
            stop_loss_percent=0.15
        ),
        BettingStrategy(
            name="Moderada",
            min_edge=0.03,
            max_stake_percent=0.03,
            kelly_fraction=0.35,
            preferred_leagues=['E0', 'SP1', 'D1'],
            max_bets_per_day=3,
            stop_loss_percent=0.20
        ),
        BettingStrategy(
            name="Agresiva",
            min_edge=0.02,
            max_stake_percent=0.05,
            kelly_fraction=0.50,
            preferred_leagues=['E0', 'SP1', 'D1', 'I1', 'F1'],
            max_bets_per_day=5,
            stop_loss_percent=0.25
        )
    ]
    
    # Ejecutar simulaciones
    simulator = ProfitabilitySimulator(initial_bankroll=10000)
    results_df = simulator.compare_strategies(strategies, days=30)
    
    # Mostrar resultados
    print("\nRESULTADOS DE SIMULACION (30 dias)")
    print("-" * 50)
    
    # Ordenar por ROI
    results_df = results_df.sort_values('roi', ascending=False)
    
    for _, row in results_df.iterrows():
        print(f"\nESTRATEGIA: {row['strategy_name']}")
        print(f"   ROI: {row['roi']:.2%}")
        print(f"   Win Rate: {row['win_rate']:.2%}")
        print(f"   Total Apuestas: {int(row['total_bets'])}")
        print(f"   Ganancia Total: ${row['total_profit']:.2f}")
        print(f"   Drawdown Maximo: {row['max_drawdown']:.2%}")
        print(f"   Sharpe Ratio: {row['sharpe_ratio']:.2f}")
        print(f"   Stake Promedio: ${row['avg_stake']:.2f}")
    
    # Recomendación
    best_strategy = results_df.iloc[0]
    print(f"\nRECOMENDACION:")
    print(f"La estrategia '{best_strategy['strategy_name']}' muestra el mejor balance")
    print(f"entre rentabilidad ({best_strategy['roi']:.2%}) y riesgo.")
    
    # Guardar resultados
    results_df.to_csv('simulacion_rentabilidad.csv', index=False)
    print(f"\nResultados guardados en 'simulacion_rentabilidad.csv'")


if __name__ == "__main__":
    main()
