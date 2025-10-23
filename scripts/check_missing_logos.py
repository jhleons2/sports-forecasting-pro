#!/usr/bin/env python3
"""
Script para verificar qué equipos no tienen logos asignados
"""

import pandas as pd
import yaml
from pathlib import Path

def load_team_logos():
    """Carga los logos de equipos desde el archivo YAML"""
    try:
        with open('config/team_logos.yaml', 'r', encoding='utf-8') as file:
            data = yaml.safe_load(file)
            # Combinar todas las ligas en un solo diccionario
            all_logos = {}
            for league, teams in data.items():
                all_logos.update(teams)
            return all_logos
    except Exception as e:
        print(f"Error cargando logos: {e}")
        return {}

def check_upcoming_fixtures():
    """Verifica qué equipos en los próximos partidos no tienen logos"""
    try:
        # Cargar fixtures
        fixtures_df = pd.read_parquet('data/processed/upcoming_fixtures.parquet')
        
        # Cargar logos
        team_logos = load_team_logos()
        
        print("=== ANÁLISIS DE LOGOS FALTANTES ===\n")
        
        # Obtener equipos únicos
        home_teams = set(fixtures_df['HomeTeam'].unique())
        away_teams = set(fixtures_df['AwayTeam'].unique())
        all_teams = home_teams.union(away_teams)
        
        print(f"Total de equipos únicos: {len(all_teams)}")
        print(f"Logos disponibles: {len(team_logos)}")
        
        # Equipos sin logo
        teams_without_logos = []
        teams_with_logos = []
        
        for team in sorted(all_teams):
            if team in team_logos:
                teams_with_logos.append(team)
            else:
                teams_without_logos.append(team)
        
        print(f"\n✅ Equipos CON logo: {len(teams_with_logos)}")
        for team in teams_with_logos:
            print(f"  - {team}")
        
        print(f"\n❌ Equipos SIN logo: {len(teams_without_logos)}")
        for team in teams_without_logos:
            print(f"  - {team}")
        
        # Sugerir logos para equipos faltantes
        if teams_without_logos:
            print(f"\n🔍 SUGERENCIAS DE LOGOS:")
            print("Agregar estos equipos al archivo config/team_logos.yaml:")
            print()
            for team in teams_without_logos:
                print(f"  {team}: \"https://logos-world.net/wp-content/uploads/2020/06/{team.replace(' ', '-')}-Logo.png\"")
        
        return teams_without_logos, teams_with_logos
        
    except Exception as e:
        print(f"Error: {e}")
        return [], []

if __name__ == "__main__":
    check_upcoming_fixtures()
