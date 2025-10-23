"""
SISTEMA DE LESIONES - FANTASY PREMIER LEAGUE API (GRATUITA)
===========================================================

Sistema completamente gratuito para obtener datos de lesiones de Premier League.
"""

import requests
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional
import json


class SistemaLesionesFPL:
    """
    Sistema gratuito para obtener lesiones usando Fantasy Premier League API.
    """
    
    def __init__(self):
        self.base_url = "https://fantasy.premierleague.com/api"
        self.elements_data = None
        self.teams_data = None
        self._cargar_datos_iniciales()
    
    def _cargar_datos_iniciales(self):
        """Cargar datos iniciales de FPL API"""
        try:
            # Obtener datos de elementos (jugadores)
            response = requests.get(f"{self.base_url}/bootstrap-static/")
            if response.status_code == 200:
                data = response.json()
                self.elements_data = data['elements']
                self.teams_data = data['teams']
                print(f"OK Datos FPL cargados: {len(self.elements_data)} jugadores")
            else:
                print(f"ERROR Error cargando datos FPL: {response.status_code}")
        except Exception as e:
            print(f"ERROR Error conexion FPL: {e}")
    
    def obtener_lesiones_equipo(self, nombre_equipo: str) -> List[Dict]:
        """
        Obtener lesiones de un equipo específico.
        
        Parameters:
        -----------
        nombre_equipo : str
            Nombre del equipo (ej: 'Arsenal', 'Chelsea')
            
        Returns:
        --------
        List[Dict]: Lista de jugadores lesionados
        """
        if not self.elements_data or not self.teams_data:
            return []
        
        # Buscar ID del equipo
        equipo_id = None
        for team in self.teams_data:
            if team['name'].lower() == nombre_equipo.lower():
                equipo_id = team['id']
                break
        
        if not equipo_id:
            print(f"ADVERTENCIA Equipo '{nombre_equipo}' no encontrado")
            return []
        
        # Filtrar jugadores lesionados del equipo
        jugadores_lesionados = []
        for jugador in self.elements_data:
            if (jugador['team'] == equipo_id and 
                jugador['status'] in ['i', 'd']):  # 'i' = injured, 'd' = doubtful
                
                jugadores_lesionados.append({
                    'nombre': jugador['web_name'],
                    'nombre_completo': jugador['first_name'] + ' ' + jugador['second_name'],
                    'posicion': self._convertir_posicion(jugador['element_type']),
                    'status': jugador['status'],
                    'status_text': self._convertir_status(jugador['status']),
                    'news': self._traducir_noticia_lesion(jugador.get('news', '')),
                    'news_added': jugador.get('news_added', ''),
                    'chance_of_playing_next_round': jugador.get('chance_of_playing_next_round'),
                    'chance_of_playing_this_round': jugador.get('chance_of_playing_this_round')
                })
        
        return jugadores_lesionados
    
    def _convertir_posicion(self, element_type: int) -> str:
        """Convertir código de posición a texto en español"""
        posiciones = {
            1: 'Portero',
            2: 'Defensor', 
            3: 'Mediocampista',
            4: 'Delantero'
        }
        return posiciones.get(element_type, 'Desconocido')
    
    def _convertir_status(self, status: str) -> str:
        """Convertir código de status a texto en español"""
        status_map = {
            'a': 'Disponible',
            'd': 'Dudoso', 
            'i': 'Lesionado',
            's': 'Suspendido',
            'u': 'No disponible',
            'n': 'No en plantilla'
        }
        return status_map.get(status, 'Desconocido')
    
    def _traducir_noticia_lesion(self, news: str) -> str:
        """Traducir noticias de lesiones al español"""
        if not news:
            return ""
        
        # Diccionario de traducciones comunes
        traducciones = {
            'ankle injury': 'lesión de tobillo',
            'knee injury': 'lesión de rodilla',
            'muscle injury': 'lesión muscular',
            'hamstring injury': 'lesión de isquiotibiales',
            'calf injury': 'lesión de pantorrilla',
            'thigh injury': 'lesión de muslo',
            'groin injury': 'lesión de ingle',
            'knock': 'golpe/contusión',
            'anterior cruciate ligament': 'ligamento cruzado anterior',
            'unknown return date': 'fecha de regreso desconocida',
            'expected back': 'regreso esperado',
            'chance of playing': 'probabilidad de jugar',
            '%': '%'
        }
        
        # Convertir a minúsculas para buscar
        news_lower = news.lower()
        
        # Aplicar traducciones
        for ingles, espanol in traducciones.items():
            news_lower = news_lower.replace(ingles, espanol)
        
        # Capitalizar la primera letra
        return news_lower.capitalize()
    
    def procesar_lesiones_para_reglas(self, lesiones: List[Dict]) -> Dict:
        """
        Procesar lesiones para integrar con las 5 reglas dinámicas.
        
        Parameters:
        -----------
        lesiones : List[Dict]
            Lista de lesiones de FPL API
            
        Returns:
        --------
        Dict: Datos procesados para REGLA 5
        """
        if not lesiones:
            return {
                'total_lesiones': 0,
                'jugadores_clave_lesionados': 0,
                'lesiones_por_posicion': {},
                'probabilidad_jugar': 0.0,
                'impacto_estimado': 0.0
            }
        
        # Procesar lesiones
        total_lesiones = len(lesiones)
        jugadores_clave = 0
        lesiones_por_posicion = {}
        probabilidades_jugar = []
        
        # Posiciones clave (mayor impacto)
        posiciones_clave = ['Portero', 'Defensor', 'Mediocampista', 'Delantero']
        
        for lesion in lesiones:
            # Contar jugadores clave
            if lesion['posicion'] in posiciones_clave:
                jugadores_clave += 1
            
            # Agrupar por posición
            posicion = lesion['posicion']
            lesiones_por_posicion[posicion] = lesiones_por_posicion.get(posicion, 0) + 1
            
            # Probabilidad de jugar
            prob_jugar = lesion.get('chance_of_playing_next_round', 0)
            if prob_jugar is not None:
                probabilidades_jugar.append(prob_jugar)
        
        # Calcular impacto estimado (CORREGIDO)
        impacto_total = 0.0
        
        for lesion in lesiones:
            # Impacto base según tipo de lesión
            if lesion['status'] == 'i':  # Injured
                impacto_base_lesion = 0.20  # 20% por lesión grave
            elif lesion['status'] == 'd':  # Doubtful
                impacto_base_lesion = 0.10  # 10% por lesión dudosa
            else:
                impacto_base_lesion = 0.05  # 5% por otros casos
            
            # Ajustar por posición (jugadores clave tienen más impacto)
            if lesion['posicion'] in ['Portero', 'Defensor']:
                multiplicador_posicion = 1.5  # Porteros y defensores son más críticos
            elif lesion['posicion'] in ['Mediocampista', 'Delantero']:
                multiplicador_posicion = 1.2  # Mediocampistas y atacantes
            else:
                multiplicador_posicion = 1.0
            
            # Ajustar por probabilidad de jugar
            prob_jugar = lesion.get('chance_of_playing_next_round', 50)
            if prob_jugar is not None:
                # Si tiene 25% de jugar, impacto alto. Si tiene 75%, impacto bajo
                multiplicador_probabilidad = (100 - prob_jugar) / 100
            else:
                multiplicador_probabilidad = 0.5  # Valor por defecto
            
            # Calcular impacto de esta lesión
            impacto_lesion = impacto_base_lesion * multiplicador_posicion * multiplicador_probabilidad
            impacto_total += impacto_lesion
        
        # Limitar impacto máximo a 60% (nunca más del 60% por lesiones)
        impacto_total = min(impacto_total, 0.60)
        
        # Calcular probabilidad promedio de jugar
        prob_promedio = sum(probabilidades_jugar) / len(probabilidades_jugar) if probabilidades_jugar else 0
        
        return {
            'total_lesiones': total_lesiones,
            'jugadores_clave_lesionados': jugadores_clave,
            'lesiones_por_posicion': lesiones_por_posicion,
            'probabilidad_jugar': prob_promedio,
            'impacto_estimado': impacto_total
        }
    
    def obtener_lesiones_partido(self, equipo_home: str, equipo_away: str) -> Dict:
        """
        Obtener lesiones para ambos equipos de un partido.
        
        Parameters:
        -----------
        equipo_home : str
            Nombre del equipo local
        equipo_away : str
            Nombre del equipo visitante
            
        Returns:
        --------
        Dict: Datos de REGLA 5 para ambos equipos
        """
        lesiones_home = self.obtener_lesiones_equipo(equipo_home)
        lesiones_away = self.obtener_lesiones_equipo(equipo_away)
        
        regla5_home = self.procesar_lesiones_para_reglas(lesiones_home)
        regla5_away = self.procesar_lesiones_para_reglas(lesiones_away)
        
        return {
            'home': {
                'equipo': equipo_home,
                'lesiones_detalle': lesiones_home,
                'regla5': regla5_home
            },
            'away': {
                'equipo': equipo_away,
                'lesiones_detalle': lesiones_away,
                'regla5': regla5_away
            }
        }


# Mapeo de nombres de equipos comunes
EQUIPOS_FPL = {
    'Arsenal': 'Arsenal',
    'Chelsea': 'Chelsea', 
    'Liverpool': 'Liverpool',
    'Manchester City': 'Man City',
    'Manchester United': 'Man Utd',
    'Tottenham': 'Spurs',
    'Newcastle': 'Newcastle',
    'Aston Villa': 'Aston Villa',
    'West Ham': 'West Ham',
    'Brighton': 'Brighton',
    'Crystal Palace': 'Crystal Palace',
    'Fulham': 'Fulham',
    'Everton': 'Everton',
    'Leicester': 'Leicester',
    'Wolves': 'Wolves',
    'Bournemouth': 'Bournemouth',
    'Brentford': 'Brentford',
    'Sunderland': 'Sunderland',
    'Burnley': 'Burnley',
    'Nottingham Forest': 'Nott\'m Forest'
}


def integrar_lesiones_fpl_con_reglas(equipo_home: str, equipo_away: str) -> Dict:
    """
    Función de conveniencia para integrar lesiones FPL con reglas dinámicas.
    
    Parameters:
    -----------
    equipo_home : str
        Nombre del equipo local
    equipo_away : str
        Nombre del equipo visitante
        
    Returns:
    --------
    Dict: Datos completos de REGLA 5
    """
    sistema = SistemaLesionesFPL()
    
    # Mapear nombres si es necesario
    home_fpl = EQUIPOS_FPL.get(equipo_home, equipo_home)
    away_fpl = EQUIPOS_FPL.get(equipo_away, equipo_away)
    
    return sistema.obtener_lesiones_partido(home_fpl, away_fpl)


if __name__ == "__main__":
    print("\n" + "="*70)
    print("  SISTEMA DE LESIONES - FANTASY PREMIER LEAGUE (GRATUITO)")
    print("="*70)
    
    # Probar con equipos reales
    print(f"\nPROBANDO CON ARSENAL vs CHELSEA...")
    
    try:
        regla5_data = integrar_lesiones_fpl_con_reglas('Arsenal', 'Chelsea')
        
        print(f"\nRESULTADOS:")
        print(f"Arsenal - Lesiones: {regla5_data['home']['regla5']['total_lesiones']}")
        print(f"Chelsea - Lesiones: {regla5_data['away']['regla5']['total_lesiones']}")
        print(f"Arsenal - Impacto: {regla5_data['home']['regla5']['impacto_estimado']:.1%}")
        print(f"Chelsea - Impacto: {regla5_data['away']['regla5']['impacto_estimado']:.1%}")
        
        # Mostrar detalles de lesiones
        if regla5_data['home']['lesiones_detalle']:
            print(f"\nLESIONES ARSENAL:")
            for lesion in regla5_data['home']['lesiones_detalle']:
                print(f"  - {lesion['nombre_completo']} ({lesion['posicion']}) - {lesion['status_text']}")
                if lesion['news']:
                    print(f"    Noticia: {lesion['news']}")
        
        if regla5_data['away']['lesiones_detalle']:
            print(f"\nLESIONES CHELSEA:")
            for lesion in regla5_data['away']['lesiones_detalle']:
                print(f"  - {lesion['nombre_completo']} ({lesion['posicion']}) - {lesion['status_text']}")
                if lesion['news']:
                    print(f"    Noticia: {lesion['news']}")
        
        print(f"\nOK SISTEMA FPL FUNCIONANDO")
        
    except Exception as e:
        print(f"ERROR: {e}")
        print(f"\nNOTA: Este sistema es 100% gratuito y no requiere API key")
        print(f"   Solo funciona con equipos de Premier League")
