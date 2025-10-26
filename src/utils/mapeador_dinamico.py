"""
SISTEMA DE MAPEO DINÁMICO DE NOMBRES
====================================

Sistema completamente dinámico que mapea automáticamente cualquier nombre de equipo
entre fixtures y datos históricos usando algoritmos de similitud avanzados.
"""

import pandas as pd
import re
from difflib import SequenceMatcher
from typing import Dict, Tuple, Optional
import numpy as np


class MapeadorDinamicoNombres:
    """
    Mapeador dinámico que funciona con cualquier equipo usando algoritmos de similitud.
    """
    
    def __init__(self):
        self.nombres_historicos = set()
        self.nombres_fixtures = set()
        self.mapeo_cache = {}
        self._cargar_nombres()
    
    def _cargar_nombres(self):
        """Carga todos los nombres únicos de equipos"""
        try:
            # Cargar datos históricos
            df_historico = pd.read_parquet('data/processed/matches.parquet')
            self.nombres_historicos = set(df_historico['HomeTeam'].unique()) | set(df_historico['AwayTeam'].unique())
            
            # Cargar fixtures actuales
            df_fixtures = pd.read_parquet('data/processed/upcoming_fixtures.parquet')
            self.nombres_fixtures = set(df_fixtures['HomeTeam'].unique()) | set(df_fixtures['AwayTeam'].unique())
            
            # MAPEOS MANUALES EXPLÍCITOS (prioridad sobre algoritmo)
            self.mapeos_manuales = {
                'Arsenal FC': 'Arsenal',
                'Paris SG': 'Paris SG',  # Mantener separado
                'Paris FC': 'Paris FC'   # Mantener separado
            }
            
            print(f"OK Mapeador dinámico cargado:")
            print(f"   - {len(self.nombres_historicos)} equipos históricos")
            print(f"   - {len(self.nombres_fixtures)} equipos en fixtures")
            print(f"   - {len(self.mapeos_manuales)} mapeos manuales")
            
        except Exception as e:
            print(f"ADVERTENCIA Error cargando nombres: {e}")
            self.nombres_historicos = set()
            self.nombres_fixtures = set()
            self.mapeos_manuales = {}
    
    def calcular_similitud_avanzada(self, nombre1: str, nombre2: str) -> float:
        """
        Calcula similitud avanzada entre dos nombres usando múltiples algoritmos.
        """
        if not nombre1 or not nombre2:
            return 0.0
        
        # Normalizar nombres
        n1 = self._normalizar_nombre(nombre1)
        n2 = self._normalizar_nombre(nombre2)
        
        # Si son exactamente iguales
        if n1 == n2:
            return 1.0
        
        # 1. Similitud de secuencia (difflib)
        similitud_secuencia = SequenceMatcher(None, n1, n2).ratio()
        
        # 2. Similitud por palabras clave
        similitud_palabras = self._calcular_similitud_palabras(n1, n2)
        
        # 3. Similitud por acrónimos
        similitud_acronimos = self._calcular_similitud_acronimos(nombre1, nombre2)
        
        # 4. Similitud por sufijos comunes
        similitud_sufijos = self._calcular_similitud_sufijos(n1, n2)
        
        # Combinar todas las similitudes con pesos optimizados
        similitud_final = (
            similitud_secuencia * 0.3 +
            similitud_palabras * 0.4 +
            similitud_acronimos * 0.2 +
            similitud_sufijos * 0.1
        )
        
        return min(similitud_final, 1.0)
    
    def _normalizar_nombre(self, nombre: str) -> str:
        """Normaliza un nombre de equipo"""
        if not nombre:
            return ""
        
        # Convertir a minúsculas
        nombre = nombre.lower().strip()
        
        # Remover caracteres especiales comunes
        nombre = re.sub(r'[^\w\s]', '', nombre)
        
        # Normalizar espacios
        nombre = re.sub(r'\s+', ' ', nombre).strip()
        
        return nombre
    
    def _calcular_similitud_palabras(self, n1: str, n2: str) -> float:
        """Calcula similitud basada en palabras comunes"""
        palabras1 = set(re.findall(r'\b\w+\b', n1))
        palabras2 = set(re.findall(r'\b\w+\b', n2))
        
        if not palabras1 or not palabras2:
            return 0.0
        
        # Calcular intersección y unión
        interseccion = palabras1 & palabras2
        union = palabras1 | palabras2
        
        # Score base
        score = len(interseccion) / len(union)
        
        # Bonus por palabras importantes (más específicas)
        palabras_importantes = {
            'united', 'city', 'town', 'fc', 'afc', 'rangers', 'rovers',
            'athletic', 'sporting', 'real', 'club', 'football', 'soccer',
            'manchester', 'liverpool', 'chelsea', 'arsenal', 'tottenham',
            'newcastle', 'villa', 'brighton', 'palace', 'fulham', 'everton',
            'leicester', 'wolves', 'bournemouth', 'brentford', 'sunderland',
            'burnley', 'leeds', 'west', 'ham', 'hampton', 'albion'
        }
        
        palabras_comunes_importantes = interseccion & palabras_importantes
        if palabras_comunes_importantes:
            score += 0.3
        
        # Bonus especial para nombres de ciudades/equipos específicos
        nombres_especificos = {
            'man': ['manchester'],
            'liver': ['liverpool'],
            'chel': ['chelsea'],
            'arse': ['arsenal'],
            'spur': ['tottenham'],
            'newc': ['newcastle'],
            'vill': ['villa'],
            'bright': ['brighton'],
            'palac': ['palace'],
            'fulh': ['fulham'],
            'ever': ['everton'],
            'leic': ['leicester'],
            'wolf': ['wolves'],
            'bourn': ['bournemouth'],
            'brent': ['brentford'],
            'sunder': ['sunderland'],
            'burn': ['burnley'],
            'leed': ['leeds']
        }
        
        for prefijo, nombres in nombres_especificos.items():
            if any(prefijo in palabra for palabra in palabras1) and any(nombre in palabras2 for nombre in nombres):
                score += 0.4
            elif any(prefijo in palabra for palabra in palabras2) and any(nombre in palabras1 for nombre in nombres):
                score += 0.4
        
        return min(score, 1.0)
    
    def _calcular_similitud_acronimos(self, nombre1: str, nombre2: str) -> float:
        """Calcula similitud basada en acrónimos"""
        # Extraer acrónimos (palabras de 1-3 caracteres)
        acronimos1 = set(re.findall(r'\b[A-Z]{1,3}\b', nombre1.upper()))
        acronimos2 = set(re.findall(r'\b[A-Z]{1,3}\b', nombre2.upper()))
        
        if not acronimos1 or not acronimos2:
            return 0.0
        
        interseccion = acronimos1 & acronimos2
        union = acronimos1 | acronimos2
        
        return len(interseccion) / len(union) if union else 0.0
    
    def _calcular_similitud_sufijos(self, n1: str, n2: str) -> float:
        """Calcula similitud basada en sufijos comunes"""
        sufijos_comunes = ['fc', 'afc', 'united', 'city', 'town', 'rovers', 'rangers']
        
        score = 0.0
        for sufijo in sufijos_comunes:
            if n1.endswith(sufijo) and n2.endswith(sufijo):
                score += 0.3
            elif n1.endswith(sufijo) or n2.endswith(sufijo):
                score += 0.1
        
        return min(score, 1.0)
    
    def mapear_nombre_dinamico(self, nombre_fixture: str, umbral: float = 0.4) -> Optional[str]:
        """
        Mapea un nombre de fixture a su equivalente histórico usando algoritmo dinámico.
        
        Parameters:
        -----------
        nombre_fixture : str
            Nombre del equipo en los fixtures
        umbral : float
            Umbral mínimo de similitud (0.0 - 1.0)
            
        Returns:
        --------
        str or None: Nombre histórico mapeado o None si no se encuentra match
        """
        if not nombre_fixture or not self.nombres_historicos:
            return None
        
        # PRIMERO: Verificar mapeos manuales (prioridad máxima)
        if hasattr(self, 'mapeos_manuales') and nombre_fixture in self.mapeos_manuales:
            print(f"   MAPEO MANUAL: {nombre_fixture} -> {self.mapeos_manuales[nombre_fixture]}")
            return self.mapeos_manuales[nombre_fixture]
        
        # Verificar cache primero
        if nombre_fixture in self.mapeo_cache:
            return self.mapeo_cache[nombre_fixture]
        
        mejor_match = None
        mejor_score = 0.0
        
        # Buscar el mejor match entre todos los nombres históricos
        for nombre_historico in self.nombres_historicos:
            score = self.calcular_similitud_avanzada(nombre_fixture, nombre_historico)
            
            if score > mejor_score and score >= umbral:
                mejor_score = score
                mejor_match = nombre_historico
        
        # Guardar en cache
        self.mapeo_cache[nombre_fixture] = mejor_match
        
        if mejor_match:
            print(f"   MAPEO DINAMICO: {nombre_fixture} -> {mejor_match} (score: {mejor_score:.3f})")
        
        return mejor_match
    
    def mapear_equipos_partido(self, equipo_home: str, equipo_away: str) -> Tuple[str, str]:
        """
        Mapea ambos equipos de un partido usando algoritmo dinámico.
        
        Returns:
        --------
        tuple: (equipo_home_mapeado, equipo_away_mapeado)
        """
        home_mapeado = self.mapear_nombre_dinamico(equipo_home) or equipo_home
        away_mapeado = self.mapear_nombre_dinamico(equipo_away) or equipo_away
        
        return home_mapeado, away_mapeado
    
    def regenerar_cache(self):
        """Regenera el cache de mapeos"""
        self.mapeo_cache.clear()
        self._cargar_nombres()
        print("OK Cache de mapeos regenerado")


# Instancia global del mapeador dinámico
mapeador_dinamico = MapeadorDinamicoNombres()


def mapear_nombres_dinamico(equipo_home: str, equipo_away: str) -> Tuple[str, str]:
    """
    Función de conveniencia para mapear nombres usando el sistema dinámico.
    
    Parameters:
    -----------
    equipo_home : str
        Nombre del equipo local
    equipo_away : str
        Nombre del equipo visitante
        
    Returns:
    --------
    tuple: (equipo_home_mapeado, equipo_away_mapeado)
    """
    return mapeador_dinamico.mapear_equipos_partido(equipo_home, equipo_away)


if __name__ == "__main__":
    print("\n" + "="*70)
    print("  SISTEMA DE MAPEO DINÁMICO DE NOMBRES")
    print("="*70)
    
    # Crear instancia del mapeador
    mapeador = MapeadorDinamicoNombres()
    
    # Probar con algunos ejemplos
    ejemplos = [
        ("Manchester City FC", "Man City"),
        ("Liverpool FC", "Liverpool"),
        ("Chelsea FC", "Chelsea"),
        ("Arsenal FC", "Arsenal"),
        ("Tottenham Hotspur FC", "Tottenham"),
        ("Newcastle United FC", "Newcastle"),
        ("Aston Villa FC", "Aston Villa"),
        ("West Ham United FC", "West Ham"),
        ("Brighton & Hove Albion FC", "Brighton"),
        ("Crystal Palace FC", "Crystal Palace"),
        ("Fulham FC", "Fulham"),
        ("Everton FC", "Everton"),
        ("Leicester City FC", "Leicester"),
        ("Wolverhampton Wanderers FC", "Wolves"),
        ("AFC Bournemouth", "Bournemouth"),
        ("Brentford FC", "Brentford"),
        ("Sunderland AFC", "Sunderland"),
        ("Nottingham Forest FC", "Nott'm Forest"),
        ("Burnley FC", "Burnley")
    ]
    
    print(f"\nPROBANDO MAPEO DINAMICO:")
    print("-" * 50)
    
    for fixture, esperado in ejemplos:
        mapeado = mapeador.mapear_nombre_dinamico(fixture)
        status = "OK" if mapeado == esperado else "ERROR"
        print(f"{status} {fixture} -> {mapeado} (esperado: {esperado})")
    
    print(f"\nESTADISTICAS:")
    print(f"   - Equipos históricos: {len(mapeador.nombres_historicos)}")
    print(f"   - Equipos en fixtures: {len(mapeador.nombres_fixtures)}")
    print(f"   - Mapeos en cache: {len(mapeador.mapeo_cache)}")
    
    print(f"\nOK SISTEMA DINAMICO LISTO")
