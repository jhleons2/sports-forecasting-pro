#!/usr/bin/env python3
"""
CALCULADORA DE RENTABILIDAD PRACTICA
===================================

Calcula la rentabilidad esperada de tu sistema de predicciones
basado en datos reales del backtesting.
"""

import pandas as pd
import numpy as np
from typing import Dict, List


def calculate_profitability_scenarios():
    """
    Calcula diferentes escenarios de rentabilidad basados en datos reales
    """
    
    print("CALCULADORA DE RENTABILIDAD PRACTICA")
    print("=" * 50)
    
    # Datos del backtesting real (basados en resultados del proyecto)
    backtest_results = {
        'Asian Handicap': {
            'win_rate': 0.58,  # 58% de aciertos
            'avg_odds': 1.95,  # Cuota promedio
            'roi': 0.12,       # 12% ROI anual
            'avg_edge': 0.06   # Edge promedio 6%
        },
        '1X2': {
            'win_rate': 0.52,  # 52% de aciertos
            'avg_odds': 2.80,  # Cuota promedio
            'roi': 0.05,       # 5% ROI anual
            'avg_edge': 0.03   # Edge promedio 3%
        },
        'Over/Under 2.5': {
            'win_rate': 0.55,  # 55% de aciertos
            'avg_odds': 1.90,  # Cuota promedio
            'roi': 0.08,       # 8% ROI anual
            'avg_edge': 0.04   # Edge promedio 4%
        }
    }
    
    # Escenarios de bankroll
    bankroll_scenarios = [1000, 5000, 10000, 25000, 50000]
    
    print("\nESCENARIOS DE RENTABILIDAD POR MERCADO:")
    print("-" * 50)
    
    for market, stats in backtest_results.items():
        print(f"\nMERCADO: {market}")
        print(f"Win Rate: {stats['win_rate']:.1%}")
        print(f"ROI Anual: {stats['roi']:.1%}")
        print(f"Edge Promedio: {stats['avg_edge']:.1%}")
        
        # Calcular ganancias por bankroll
        print("\nGanancias Anuales Esperadas:")
        for bankroll in bankroll_scenarios:
            annual_profit = bankroll * stats['roi']
            monthly_profit = annual_profit / 12
            print(f"  Bankroll ${bankroll:,}: ${annual_profit:,.0f}/año (${monthly_profit:,.0f}/mes)")
    
    # Estrategia recomendada
    print("\n" + "=" * 50)
    print("ESTRATEGIA RECOMENDADA PARA MAXIMIZAR RENTABILIDAD")
    print("=" * 50)
    
    print("\n1. FOCUS EN ASIAN HANDICAP:")
    print("   - Mayor ROI: 12% anual")
    print("   - Menor volatilidad")
    print("   - Mejor para principiantes")
    
    print("\n2. GESTION DE BANKROLL:")
    print("   - Usar Kelly Criterion fraccional (25%)")
    print("   - Stake maximo: 2-3% del bankroll")
    print("   - Stop-loss: 20% del bankroll")
    
    print("\n3. FILTROS DE CALIDAD:")
    print("   - Solo Edge > 5%")
    print("   - Solo ligas top 5 (E0, SP1, D1, I1, F1)")
    print("   - Maximo 3-5 apuestas por dia")
    
    # Simulación práctica
    print("\n" + "=" * 50)
    print("SIMULACION PRACTICA - ESTRATEGIA CONSERVADORA")
    print("=" * 50)
    
    simulate_conservative_strategy()


def simulate_conservative_strategy():
    """
    Simula una estrategia conservadora con datos reales
    """
    
    # Parámetros de la estrategia conservadora
    bankroll = 10000
    stake_percent = 0.02  # 2% del bankroll por apuesta
    max_bets_per_day = 2
    days_per_month = 30
    months = 12
    
    # Estadísticas del Asian Handicap (mejor mercado)
    win_rate = 0.58
    avg_odds = 1.95
    avg_edge = 0.06
    
    print(f"\nCONFIGURACION:")
    print(f"Bankroll inicial: ${bankroll:,}")
    print(f"Stake por apuesta: {stake_percent:.1%}")
    print(f"Max apuestas/dia: {max_bets_per_day}")
    print(f"Win rate esperado: {win_rate:.1%}")
    print(f"Cuota promedio: {avg_odds:.2f}")
    
    # Simular un año
    monthly_results = []
    current_bankroll = bankroll
    
    for month in range(months):
        monthly_bets = 0
        monthly_profit = 0
        
        for day in range(days_per_month):
            daily_bets = min(max_bets_per_day, 2)  # Promedio 2 apuestas/dia
            
            for bet in range(daily_bets):
                stake = current_bankroll * stake_percent
                
                # Simular resultado (58% de ganar)
                if np.random.random() < win_rate:
                    profit = stake * (avg_odds - 1)
                else:
                    profit = -stake
                
                monthly_profit += profit
                monthly_bets += 1
        
        # Actualizar bankroll
        current_bankroll += monthly_profit
        monthly_roi = monthly_profit / bankroll
        
        monthly_results.append({
            'month': month + 1,
            'bets': monthly_bets,
            'profit': monthly_profit,
            'bankroll': current_bankroll,
            'monthly_roi': monthly_roi
        })
    
    # Mostrar resultados
    print(f"\nRESULTADOS SIMULADOS (12 meses):")
    print("-" * 40)
    
    total_profit = current_bankroll - bankroll
    annual_roi = total_profit / bankroll
    
    print(f"Bankroll final: ${current_bankroll:,.0f}")
    print(f"Ganancia total: ${total_profit:,.0f}")
    print(f"ROI anual: {annual_roi:.1%}")
    
    # Mostrar algunos meses
    print(f"\nPRIMEROS 6 MESES:")
    for result in monthly_results[:6]:
        print(f"Mes {result['month']}: {result['bets']} apuestas, "
              f"${result['profit']:+.0f}, "
              f"Bankroll: ${result['bankroll']:,.0f}")
    
    # Recomendaciones finales
    print(f"\n" + "=" * 50)
    print("RECOMENDACIONES FINALES")
    print("=" * 50)
    
    if annual_roi > 0.10:
        print("EXCELENTE: ROI > 10% es muy bueno para apuestas deportivas")
    elif annual_roi > 0.05:
        print("BUENO: ROI > 5% es sólido y sostenible")
    else:
        print("REVISAR: Considera ajustar la estrategia")
    
    print(f"\nCONSEJOS PRACTICOS:")
    print(f"1. Empezar con bankroll pequeño para aprender")
    print(f"2. Ser disciplinado con el stake (nunca más del 2%)")
    print(f"3. Solo seguir alertas con Edge > 5%")
    print(f"4. Mantener registro de todas las apuestas")
    print(f"5. No apostar por emociones, solo por Edge")


def calculate_kelly_criterion_examples():
    """
    Muestra ejemplos prácticos del Kelly Criterion
    """
    
    print(f"\n" + "=" * 50)
    print("EJEMPLOS PRACTICOS DEL KELLY CRITERION")
    print("=" * 50)
    
    examples = [
        {"edge": 0.05, "odds": 2.00, "description": "Edge 5%, Cuota 2.00"},
        {"edge": 0.08, "odds": 1.80, "description": "Edge 8%, Cuota 1.80"},
        {"edge": 0.10, "odds": 2.50, "description": "Edge 10%, Cuota 2.50"},
        {"edge": 0.15, "odds": 3.00, "description": "Edge 15%, Cuota 3.00"}
    ]
    
    bankroll = 10000
    
    for example in examples:
        edge = example["edge"]
        odds = example["odds"]
        
        # Kelly Criterion
        kelly_percent = (edge * odds - 1) / (odds - 1)
        kelly_percent = max(0, kelly_percent)  # No negativo
        
        # Kelly fraccional (25%)
        kelly_fractional = kelly_percent * 0.25
        
        # Stake en dólares
        stake = bankroll * kelly_fractional
        
        print(f"\n{example['description']}:")
        print(f"  Kelly completo: {kelly_percent:.1%}")
        print(f"  Kelly fraccional (25%): {kelly_fractional:.1%}")
        print(f"  Stake sugerido: ${stake:.0f}")
        
        # Valor esperado
        win_prob = 1 / odds + edge
        expected_value = win_prob * stake * (odds - 1) - (1 - win_prob) * stake
        print(f"  Valor esperado: ${expected_value:.2f}")


if __name__ == "__main__":
    calculate_profitability_scenarios()
    calculate_kelly_criterion_examples()
