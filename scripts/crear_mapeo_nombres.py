"""Mapeo automático de nombres entre fixtures y datos históricos"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import re

def crear_mapeo_nombres():
    """Crea mapeo automático entre nombres de fixtures y datos históricos"""
    
    # Cargar datos
    df_historico = pd.read_parquet('data/processed/matches.parquet')
    df_fixtures = pd.read_parquet('data/processed/upcoming_fixtures.parquet')
    
    # Obtener nombres únicos
    nombres_historicos = set(df_historico['HomeTeam'].unique()) | set(df_historico['AwayTeam'].unique())
    nombres_fixtures = set(df_fixtures['HomeTeam'].unique()) | set(df_fixtures['AwayTeam'].unique())
    
    print(f"Nombres históricos: {len(nombres_historicos)}")
    print(f"Nombres fixtures: {len(nombres_fixtures)}")
    
    # Crear mapeo automático
    mapeo = {}
    
    # MAPEOS MANUALES ESPECÍFICOS (para casos que el algoritmo automático no detecta)
    mapeos_manuales = {
        'Manchester City FC': 'Man City',
        'Manchester United FC': 'Man United',
        'Liverpool FC': 'Liverpool',
        'Chelsea FC': 'Chelsea',
        'Arsenal FC': 'Arsenal',
        'Tottenham Hotspur FC': 'Tottenham',
        'Newcastle United FC': 'Newcastle',
        'Aston Villa FC': 'Aston Villa',
        'West Ham United FC': 'West Ham',
        'Leeds United FC': 'Leeds',
        'Brighton & Hove Albion FC': 'Brighton',
        'Crystal Palace FC': 'Crystal Palace',
        'Fulham FC': 'Fulham',
        'Everton FC': 'Everton',
        'Leicester City FC': 'Leicester',
        'Wolverhampton Wanderers FC': 'Wolves',
        'AFC Bournemouth': 'Bournemouth',
        'Brentford FC': 'Brentford',
        'Sunderland AFC': 'Sunderland',
        'Nottingham Forest FC': "Nott'm Forest",
        'Burnley FC': 'Burnley'
    }
    
    # Aplicar mapeos manuales primero
    for fixture, historico in mapeos_manuales.items():
        if fixture in nombres_fixtures and historico in nombres_historicos:
            mapeo[fixture] = historico
    
    # Luego aplicar algoritmo automático para el resto
    for nombre_fixture in nombres_fixtures:
        if nombre_fixture in mapeo:  # Ya mapeado manualmente
            continue
            
        mejor_match = None
        mejor_score = 0
        
        for nombre_historico in nombres_historicos:
            # Calcular similitud
            score = calcular_similitud(nombre_fixture, nombre_historico)
            if score > mejor_score and score > 0.6:  # Umbral mínimo
                mejor_score = score
                mejor_match = nombre_historico
        
        if mejor_match:
            mapeo[nombre_fixture] = mejor_match
    
    return mapeo

def calcular_similitud(nombre1, nombre2):
    """Calcula similitud entre dos nombres de equipos"""
    
    # Normalizar nombres
    n1 = nombre1.lower().strip()
    n2 = nombre2.lower().strip()
    
    # Si son exactamente iguales
    if n1 == n2:
        return 1.0
    
    # Si uno contiene al otro
    if n1 in n2 or n2 in n1:
        return 0.9
    
    # Extraer palabras clave
    palabras1 = set(re.findall(r'\b\w+\b', n1))
    palabras2 = set(re.findall(r'\b\w+\b', n2))
    
    # Calcular intersección
    interseccion = palabras1 & palabras2
    union = palabras1 | palabras2
    
    if len(union) == 0:
        return 0.0
    
    # Score basado en palabras comunes
    score_palabras = len(interseccion) / len(union)
    
    # Bonus por palabras importantes
    palabras_importantes = {'united', 'city', 'town', 'fc', 'afc', 'rangers', 'rovers'}
    palabras_comunes_importantes = interseccion & palabras_importantes
    
    if palabras_comunes_importantes:
        score_palabras += 0.2
    
    return min(score_palabras, 1.0)

def aplicar_mapeo_a_fixtures(df_fixtures, mapeo):
    """Aplica el mapeo a los fixtures"""
    
    df_mapeado = df_fixtures.copy()
    
    # Mapear nombres
    df_mapeado['HomeTeam_Original'] = df_mapeado['HomeTeam']
    df_mapeado['AwayTeam_Original'] = df_mapeado['AwayTeam']
    
    df_mapeado['HomeTeam'] = df_mapeado['HomeTeam'].map(mapeo).fillna(df_mapeado['HomeTeam'])
    df_mapeado['AwayTeam'] = df_mapeado['AwayTeam'].map(mapeo).fillna(df_mapeado['AwayTeam'])
    
    return df_mapeado

if __name__ == "__main__":
    print("\n" + "="*70)
    print("  CREANDO MAPEO DE NOMBRES")
    print("="*70)
    
    # Crear mapeo
    mapeo = crear_mapeo_nombres()
    
    print(f"\nMAPEO CREADO:")
    for fixture, historico in mapeo.items():
        print(f"   {fixture} -> {historico}")
    
    # Aplicar mapeo a fixtures
    df_fixtures = pd.read_parquet('data/processed/upcoming_fixtures.parquet')
    df_mapeado = aplicar_mapeo_a_fixtures(df_fixtures, mapeo)
    
    # Guardar fixtures mapeados
    df_mapeado.to_parquet('data/processed/upcoming_fixtures_mapeado.parquet', index=False)
    
    print(f"\nOK MAPEO APLICADO Y GUARDADO")
    print(f"   Archivo: data/processed/upcoming_fixtures_mapeado.parquet")
    
    # Verificar algunos ejemplos
    print(f"\nEJEMPLOS DE MAPEO:")
    ejemplos = ['Newcastle United FC', 'Fulham FC', 'Chelsea FC', 'Sunderland AFC', 'Manchester City FC']
    for ejemplo in ejemplos:
        if ejemplo in mapeo:
            print(f"   {ejemplo} -> {mapeo[ejemplo]}")
        else:
            print(f"   {ejemplo} -> NO MAPEADO")
