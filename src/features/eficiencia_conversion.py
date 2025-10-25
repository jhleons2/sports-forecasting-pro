"""
Análisis de Eficiencia de Conversión
=====================================

Calcula la eficiencia de los equipos para convertir xG en goles reales.
Esto ayuda a predecir mejor los resultados al considerar la calidad
de finalización, no solo las oportunidades creadas.
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional


class AnalizadorEficiencia:
    """Analiza la eficiencia de conversión xG -> Goles"""
    
    def __init__(self):
        self.historial_eficiencia = {}
    
    def calcular_eficiencia_equipo(
        self,
        df_historico: pd.DataFrame,
        equipo: str,
        ventana_partidos: int = 10
    ) -> Dict:
        """
        Calcula la eficiencia de un equipo en los últimos partidos
        
        Args:
            df_historico: DataFrame con partidos históricos
            equipo: Nombre del equipo
            ventana_partidos: Número de partidos a considerar
            
        Returns:
            Diccionario con métricas de eficiencia
        """
        # Filtrar partidos del equipo
        partidos_equipo = df_historico[
            (df_historico['HomeTeam'] == equipo) | 
            (df_historico['AwayTeam'] == equipo)
        ].sort_values('Date', ascending=False).head(ventana_partidos)
        
        if len(partidos_equipo) == 0:
            return self._eficiencia_default()
        
        goles_totales = 0
        xg_total = 0.0
        
        for _, row in partidos_equipo.iterrows():
            if row['HomeTeam'] == equipo:
                goles_totales += row.get('FTHG', 0)
                # Si no hay xG real, estimar desde datos disponibles
                if 'xG_home' in row and pd.notna(row['xG_home']):
                    xg_total += row['xG_home']
                else:
                    # Estimar xG aproximado
                    xg_total += self._estimar_xg_desde_goles(row.get('FTHG', 0))
            else:
                goles_totales += row.get('FTAG', 0)
                if 'xG_away' in row and pd.notna(row['xG_away']):
                    xg_total += row['xG_away']
                else:
                    xg_total += self._estimar_xg_desde_goles(row.get('FTAG', 0))
        
        # Calcular ratio de eficiencia
        if xg_total > 0:
            ratio_eficiencia = goles_totales / xg_total
        else:
            ratio_eficiencia = 1.0
        
        return {
            'goles_totales': goles_totales,
            'xg_total': xg_total,
            'ratio_eficiencia': ratio_eficiencia,
            'partidos_analizados': len(partidos_equipo),
            'goles_por_partido': goles_totales / len(partidos_equipo) if len(partidos_equipo) > 0 else 0
        }
    
    def calcular_eficiencia_head_to_head(
        self,
        df_historico: pd.DataFrame,
        equipo_home: str,
        equipo_away: str,
        ventana_partidos: int = 5
    ) -> Dict:
        """
        Calcula la eficiencia en enfrentamientos directos
        
        Args:
            df_historico: DataFrame con partidos históricos
            equipo_home: Equipo local
            equipo_away: Equipo visitante
            ventana_partidos: Número de partidos a considerar
            
        Returns:
            Diccionario con métricas H2H
        """
        # Filtrar partidos entre estos dos equipos
        h2h_matches = df_historico[
            ((df_historico['HomeTeam'] == equipo_home) & 
             (df_historico['AwayTeam'] == equipo_away)) |
            ((df_historico['HomeTeam'] == equipo_away) & 
             (df_historico['AwayTeam'] == equipo_home))
        ].sort_values('Date', ascending=False).head(ventana_partidos)
        
        if len(h2h_matches) == 0:
            return self._h2h_default()
        
        goles_home = 0
        goles_away = 0
        
        for _, row in h2h_matches.iterrows():
            if row['HomeTeam'] == equipo_home:
                goles_home += row.get('FTHG', 0)
                goles_away += row.get('FTAG', 0)
            else:
                goles_away += row.get('FTHG', 0)
                goles_home += row.get('FTAG', 0)
        
        return {
            'goles_home': goles_home,
            'goles_away': goles_away,
            'diferencia_goles': goles_home - goles_away,
            'partidos': len(h2h_matches),
            'ventaja_home': goles_home > goles_away
        }
    
    def aplicar_ajuste_eficiencia(
        self,
        xg_home: float,
        xg_away: float,
        eficiencia_home: Dict,
        eficiencia_away: Dict
    ) -> tuple:
        """
        Ajusta los xG según la eficiencia histórica de los equipos
        
        Args:
            xg_home: xG predicho para equipo local
            xg_away: xG predicho para equipo visitante
            eficiencia_home: Dict con eficiencia equipo local
            eficiencia_away: Dict con eficiencia equipo visitante
            
        Returns:
            Tupla con (xg_home_ajustado, xg_away_ajustado)
        """
        # Obtener ratio de eficiencia
        ratio_home = eficiencia_home.get('ratio_eficiencia', 1.0)
        ratio_away = eficiencia_away.get('ratio_eficiencia', 1.0)
        
        # Aplicar ajuste moderado (no queremos sobreajustar)
        # Reducir el impacto del ratio para evitar cambios extremos
        ajuste_home = 1.0 + (ratio_home - 1.0) * 0.3
        ajuste_away = 1.0 + (ratio_away - 1.0) * 0.3
        
        # Aplicar límites razonables (entre 0.8 y 1.3)
        ajuste_home = max(0.8, min(1.3, ajuste_home))
        ajuste_away = max(0.8, min(1.3, ajuste_away))
        
        # Calcular xG ajustado
        xg_home_ajustado = xg_home * ajuste_home
        xg_away_ajustado = xg_away * ajuste_away
        
        return xg_home_ajustado, xg_away_ajustado
    
    def _estimar_xg_desde_goles(self, goles: int) -> float:
        """
        Estima xG aproximado desde goles reales
        (usar solo cuando no hay datos de xG real)
        """
        # Simplificación: suponer que xG ≈ goles en promedio
        # En realidad se debería usar datos históricos más sofisticados
        return float(goles)
    
    def _eficiencia_default(self) -> Dict:
        """Retorna valores por defecto cuando no hay datos"""
        return {
            'goles_totales': 0,
            'xg_total': 0,
            'ratio_eficiencia': 1.0,
            'partidos_analizados': 0,
            'goles_por_partido': 0
        }
    
    def _h2h_default(self) -> Dict:
        """Retorna valores por defecto para H2H cuando no hay datos"""
        return {
            'goles_home': 0,
            'goles_away': 0,
            'diferencia_goles': 0,
            'partidos': 0,
            'ventaja_home': False
        }


# Instancia global
analizador_eficiencia = AnalizadorEficiencia()
