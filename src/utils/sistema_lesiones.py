"""
SISTEMA DE LESIONES - API-FOOTBALL INTEGRATION
==============================================

Sistema para obtener datos de lesiones usando API-Football con tier gratuito.
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import time
import json


class SistemaLesiones:
    """
    Sistema para obtener y procesar datos de lesiones usando API-Football.
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api-football-v1.p.rapidapi.com/v3"
        self.headers = {
            "X-RapidAPI-Key": api_key,
            "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
        }
        self.request_count = 0
        self.daily_limit = 100  # Tier gratuito
        self.last_reset = datetime.now().date()
    
    def _check_rate_limit(self):
        """Verificar límites de rate limiting"""
        today = datetime.now().date()
        
        # Reset contador diario
        if today != self.last_reset:
            self.request_count = 0
            self.last_reset = today
        
        # Verificar límite diario
        if self.request_count >= self.daily_limit:
            print(f"⚠️ Límite diario alcanzado ({self.daily_limit} requests)")
            return False
        
        return True
    
    def _make_request(self, endpoint: str, params: Dict) -> Optional[Dict]:
        """Hacer request con control de rate limiting"""
        if not self._check_rate_limit():
            return None
        
        url = f"{self.base_url}/{endpoint}"
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            self.request_count += 1
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Error API: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error request: {e}")
            return None
    
    def obtener_lesiones_equipo(self, equipo_id: int, fecha: str = None) -> List[Dict]:
        """
        Obtener lesiones de un equipo específico.
        
        Parameters:
        -----------
        equipo_id : int
            ID del equipo en API-Football
        fecha : str, optional
            Fecha en formato YYYY-MM-DD (default: hoy)
            
        Returns:
        --------
        List[Dict]: Lista de lesiones
        """
        if fecha is None:
            fecha = datetime.now().strftime("%Y-%m-%d")
        
        params = {
            "team": equipo_id,
            "date": fecha
        }
        
        data = self._make_request("injuries", params)
        
        if data and "response" in data:
            return data["response"]
        else:
            return []
    
    def obtener_lesiones_liga(self, liga_id: int, fecha: str = None) -> Dict[int, List[Dict]]:
        """
        Obtener lesiones de todos los equipos de una liga.
        
        Parameters:
        -----------
        liga_id : int
            ID de la liga en API-Football
        fecha : str, optional
            Fecha en formato YYYY-MM-DD
            
        Returns:
        --------
        Dict[int, List[Dict]]: Diccionario con equipo_id -> lista de lesiones
        """
        if fecha is None:
            fecha = datetime.now().strftime("%Y-%m-%d")
        
        params = {
            "league": liga_id,
            "date": fecha
        }
        
        data = self._make_request("injuries", params)
        
        if data and "response" in data:
            # Agrupar por equipo
            lesiones_por_equipo = {}
            for lesion in data["response"]:
                equipo_id = lesion["team"]["id"]
                if equipo_id not in lesiones_por_equipo:
                    lesiones_por_equipo[equipo_id] = []
                lesiones_por_equipo[equipo_id].append(lesion)
            
            return lesiones_por_equipo
        else:
            return {}
    
    def procesar_lesiones_para_reglas(self, lesiones: List[Dict]) -> Dict:
        """
        Procesar lesiones para integrar con las 5 reglas dinámicas.
        
        Parameters:
        -----------
        lesiones : List[Dict]
            Lista de lesiones de API-Football
            
        Returns:
        --------
        Dict: Datos procesados para REGLA 5
        """
        if not lesiones:
            return {
                'total_lesiones': 0,
                'jugadores_clave_lesionados': 0,
                'lesiones_por_posicion': {},
                'tiempo_promedio_recuperacion': 0,
                'impacto_estimado': 0.0
            }
        
        # Procesar lesiones
        total_lesiones = len(lesiones)
        jugadores_clave = 0
        lesiones_por_posicion = {}
        tiempo_recuperacion = []
        
        # Posiciones clave (mayor impacto)
        posiciones_clave = ['Goalkeeper', 'Defender', 'Midfielder', 'Attacker']
        
        for lesion in lesiones:
            # Contar jugadores clave
            if lesion.get('player', {}).get('position') in posiciones_clave:
                jugadores_clave += 1
            
            # Agrupar por posición
            posicion = lesion.get('player', {}).get('position', 'Unknown')
            lesiones_por_posicion[posicion] = lesiones_por_posicion.get(posicion, 0) + 1
            
            # Tiempo de recuperación estimado
            tipo_lesion = lesion.get('type', '').lower()
            if 'muscle' in tipo_lesion:
                tiempo_recuperacion.append(14)  # 2 semanas
            elif 'knee' in tipo_lesion or 'ankle' in tipo_lesion:
                tiempo_recuperacion.append(21)  # 3 semanas
            elif 'hamstring' in tipo_lesion:
                tiempo_recuperacion.append(10)  # 1.5 semanas
            else:
                tiempo_recuperacion.append(7)   # 1 semana
        
        # Calcular impacto estimado
        impacto_base = total_lesiones * 0.1  # 10% por lesión
        impacto_clave = jugadores_clave * 0.2  # 20% por jugador clave
        impacto_total = min(impacto_base + impacto_clave, 1.0)  # Máximo 100%
        
        return {
            'total_lesiones': total_lesiones,
            'jugadores_clave_lesionados': jugadores_clave,
            'lesiones_por_posicion': lesiones_por_posicion,
            'tiempo_promedio_recuperacion': sum(tiempo_recuperacion) / len(tiempo_recuperacion) if tiempo_recuperacion else 0,
            'impacto_estimado': impacto_total
        }
    
    def obtener_stats_requests(self) -> Dict:
        """Obtener estadísticas de uso de API"""
        return {
            'requests_hoy': self.request_count,
            'limite_diario': self.daily_limit,
            'requests_restantes': self.daily_limit - self.request_count,
            'ultimo_reset': self.last_reset.isoformat()
        }


def integrar_lesiones_con_reglas(equipo_home_id: int, equipo_away_id: int, 
                                api_key: str) -> Dict:
    """
    Integrar datos de lesiones con las 5 reglas dinámicas.
    
    Parameters:
    -----------
    equipo_home_id : int
        ID del equipo local en API-Football
    equipo_away_id : int
        ID del equipo visitante en API-Football
    api_key : str
        API key de RapidAPI
        
    Returns:
    --------
    Dict: Datos de REGLA 5 para ambos equipos
    """
    sistema = SistemaLesiones(api_key)
    
    # Obtener lesiones de ambos equipos
    lesiones_home = sistema.obtener_lesiones_equipo(equipo_home_id)
    lesiones_away = sistema.obtener_lesiones_equipo(equipo_away_id)
    
    # Procesar para reglas
    regla5_home = sistema.procesar_lesiones_para_reglas(lesiones_home)
    regla5_away = sistema.procesar_lesiones_para_reglas(lesiones_away)
    
    return {
        'home': regla5_home,
        'away': regla5_away,
        'stats_api': sistema.obtener_stats_requests()
    }


# IDs de equipos comunes en API-Football (Premier League)
EQUIPOS_PREMIER_LEAGUE = {
    'Arsenal': 42,
    'Chelsea': 49,
    'Liverpool': 40,
    'Manchester City': 50,
    'Manchester United': 33,
    'Tottenham': 47,
    'Newcastle': 34,
    'Aston Villa': 66,
    'West Ham': 48,
    'Brighton': 51,
    'Crystal Palace': 52,
    'Fulham': 36,
    'Everton': 45,
    'Leicester': 46,
    'Wolves': 39,
    'Bournemouth': 35,
    'Brentford': 55,
    'Sunderland': 71,
    'Burnley': 44,
    'Nottingham Forest': 65
}


if __name__ == "__main__":
    print("\n" + "="*70)
    print("  SISTEMA DE LESIONES - API-FOOTBALL")
    print("="*70)
    
    # Ejemplo de uso (necesitas tu API key)
    API_KEY = "TU_API_KEY_AQUI"  # Reemplazar con tu API key
    
    if API_KEY == "TU_API_KEY_AQUI":
        print("\n⚠️ CONFIGURACIÓN REQUERIDA:")
        print("1. Registrarse en RapidAPI: https://rapidapi.com/api-sports/api/api-football")
        print("2. Obtener API key gratuita (100 requests/día)")
        print("3. Reemplazar 'TU_API_KEY_AQUI' con tu API key real")
        print("\n📊 EJEMPLO DE USO:")
        print("""
        # Obtener lesiones de Arsenal vs Chelsea
        arsenal_id = EQUIPOS_PREMIER_LEAGUE['Arsenal']  # 42
        chelsea_id = EQUIPOS_PREMIER_LEAGUE['Chelsea']  # 49
        
        regla5_data = integrar_lesiones_con_reglas(arsenal_id, chelsea_id, API_KEY)
        
        print(f"Arsenal lesiones: {regla5_data['home']['total_lesiones']}")
        print(f"Chelsea lesiones: {regla5_data['away']['total_lesiones']}")
        print(f"Impacto Arsenal: {regla5_data['home']['impacto_estimado']:.1%}")
        print(f"Impacto Chelsea: {regla5_data['away']['impacto_estimado']:.1%}")
        """)
    else:
        # Probar con equipos reales
        arsenal_id = EQUIPOS_PREMIER_LEAGUE['Arsenal']
        chelsea_id = EQUIPOS_PREMIER_LEAGUE['Chelsea']
        
        print(f"\n🔍 PROBANDO CON ARSENAL vs CHELSEA...")
        regla5_data = integrar_lesiones_con_reglas(arsenal_id, chelsea_id, API_KEY)
        
        print(f"\n📊 RESULTADOS:")
        print(f"Arsenal - Lesiones: {regla5_data['home']['total_lesiones']}")
        print(f"Chelsea - Lesiones: {regla5_data['away']['total_lesiones']}")
        print(f"Arsenal - Impacto: {regla5_data['home']['impacto_estimado']:.1%}")
        print(f"Chelsea - Impacto: {regla5_data['away']['impacto_estimado']:.1%}")
        
        print(f"\n📈 STATS API:")
        stats = regla5_data['stats_api']
        print(f"Requests hoy: {stats['requests_hoy']}/{stats['limite_diario']}")
        print(f"Restantes: {stats['requests_restantes']}")
    
    print(f"\n✅ SISTEMA DE LESIONES LISTO")
