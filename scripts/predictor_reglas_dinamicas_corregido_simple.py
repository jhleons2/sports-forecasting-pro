"""
PREDICTOR CON REGLAS DINÁMICAS - VERSIÓN SIMPLIFICADA CORREGIDA
==============================================================

Versión simplificada que solo agrega mapeo de nombres al predictor original.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from scripts.predictor_reglas_dinamicas import PredictorReglasDinamicas
import pandas as pd

class PredictorReglasDinamicasCorregido(PredictorReglasDinamicas):
    """
    Predictor que hereda del original pero agrega mapeo de nombres.
    """
    
    def __init__(self):
        super().__init__()
        self.mapeo_nombres = None
        
    def load_and_train(self):
        """Carga datos y entrena modelos, incluyendo mapeo de nombres"""
        # Llamar al método original
        super().load_and_train()
        
        # Cargar mapeo de nombres
        self._cargar_mapeo_nombres()
        
    def _cargar_mapeo_nombres(self):
        """Carga el mapeo de nombres desde el archivo creado"""
        try:
            # Cargar fixtures mapeados para obtener el mapeo
            df_fixtures_mapeado = pd.read_parquet("data/processed/upcoming_fixtures_mapeado.parquet")
            
            # Crear mapeo desde las columnas originales
            mapeo = {}
            for _, row in df_fixtures_mapeado.iterrows():
                if row['HomeTeam_Original'] != row['HomeTeam']:
                    mapeo[row['HomeTeam_Original']] = row['HomeTeam']
                if row['AwayTeam_Original'] != row['AwayTeam']:
                    mapeo[row['AwayTeam_Original']] = row['AwayTeam']
            
            self.mapeo_nombres = mapeo
            print(f"   ✅ {len(self.mapeo_nombres)} mapeos de nombres cargados")
            
        except FileNotFoundError:
            print("   ⚠️  Archivo de mapeo no encontrado, usando mapeo básico...")
            self.mapeo_nombres = self._crear_mapeo_basico()
    
    def _crear_mapeo_basico(self):
        """Crea un mapeo básico para casos comunes"""
        return {
            'Newcastle United FC': 'Newcastle',
            'Fulham FC': 'Fulham',
            'Chelsea FC': 'Chelsea',
            'Sunderland AFC': 'Sunderland',
            'Arsenal FC': 'Arsenal',
            'Liverpool FC': 'Liverpool',
            'Manchester United FC': 'Man United',
            'Manchester City FC': 'Man City',
            'Tottenham Hotspur FC': 'Tottenham',
            'West Ham United FC': 'West Ham',
            'Brighton & Hove Albion FC': 'Brighton',
            'Crystal Palace FC': 'Crystal Palace',
            'Everton FC': 'Everton',
            'Leeds United FC': 'Leeds',
            'Aston Villa FC': 'Aston Villa',
            'Wolverhampton Wanderers FC': 'Wolves',
            'Burnley FC': 'Burnley',
            'Watford FC': 'Watford',
            'Norwich City FC': 'Norwich',
            'Southampton FC': 'Southampton',
            'Leicester City FC': 'Leicester',
            'AFC Bournemouth': 'Bournemouth',
            'Brentford FC': 'Brentford',
            'Nottingham Forest FC': 'Nott\'m Forest'
        }
    
    def mapear_nombres(self, equipo_home: str, equipo_away: str) -> tuple:
        """
        Mapea nombres de fixtures a nombres de datos históricos.
        
        Returns:
        --------
        tuple: (equipo_home_mapeado, equipo_away_mapeado)
        """
        home_mapeado = self.mapeo_nombres.get(equipo_home, equipo_home)
        away_mapeado = self.mapeo_nombres.get(equipo_away, equipo_away)
        
        return home_mapeado, away_mapeado
    
    def predict_con_reglas_dinamicas(self, equipo_home: str, equipo_away: str, liga: str):
        """
        Predice usando reglas DINÁMICAS con mapeo de nombres.
        
        Parameters:
        -----------
        equipo_home : str
            Nombre del equipo local (del fixture)
        equipo_away : str
            Nombre del equipo visitante (del fixture)
        liga : str
            Código de la liga
            
        Returns:
        --------
        dict : Predicciones con reglas calculadas dinámicamente
        """
        print(f"\n" + "=" * 70)
        print("  PREDICCIÓN CON REGLAS DINÁMICAS")
        print("=" * 70)
        
        # MAPEAR NOMBRES
        home_mapeado, away_mapeado = self.mapear_nombres(equipo_home, equipo_away)
        
        print(f"📊 Mapeando nombres:")
        print(f"   {equipo_home} → {home_mapeado}")
        print(f"   {equipo_away} → {away_mapeado}")
        
        # Usar el método original con nombres mapeados
        resultado = super().predict_con_reglas_dinamicas(home_mapeado, away_mapeado, liga)
        
        # AGREGAR PREDICCIONES ADICIONALES
        resultado['events'] = self._predict_events(resultado)
        
        # Agregar información de mapeo
        resultado['nombres_originales'] = {
            'home': equipo_home,
            'away': equipo_away
        }
        resultado['nombres_mapeados'] = {
            'home': home_mapeado,
            'away': away_mapeado
        }
        
        return resultado
    
    def _predict_events(self, prediccion_base):
        """
        Predice eventos adicionales basados en xG y ELO.
        
        Parameters:
        -----------
        prediccion_base : dict
            Predicción base con xG y 1X2
            
        Returns:
        --------
        dict : Eventos predichos (corners, tarjetas, tiros)
        """
        xG_home = prediccion_base['goals']['xG_home']
        xG_away = prediccion_base['goals']['xG_away']
        
        # CORNERS
        # Aproximación: ~5-6 corners por gol esperado
        corners_home = xG_home * 5.5
        corners_away = xG_away * 5.5
        corners_total = corners_home + corners_away
        
        # TARJETAS
        # Base: 3.5-4.5 tarjetas amarillas por partido
        # Más equilibrado (empate probable) = más tarjetas
        prob_empate = prediccion_base['1x2']['pD']
        if prob_empate > 0.35:  # Partido muy equilibrado
            yellow_cards = 4.5
        elif prob_empate > 0.25:  # Partido moderadamente equilibrado
            yellow_cards = 4.0
        else:  # Partido con favorito claro
            yellow_cards = 3.5
        
        red_cards = 0.15  # ~15% de probabilidad de roja
        total_cards = yellow_cards + red_cards
        
        # TIROS
        # Aproximación: ~9 tiros por gol esperado
        shots_home = xG_home * 9.0
        shots_away = xG_away * 9.0
        shots_total = shots_home + shots_away
        
        # Tiros a puerta: ~35% del total
        shots_on_target_home = shots_home * 0.35
        shots_on_target_away = shots_away * 0.35
        
        return {
            'corners_home': float(corners_home),
            'corners_away': float(corners_away),
            'corners_total': float(corners_total),
            'corners_over_9_5': float(1.0 if corners_total > 9.5 else 0.0),
            'corners_over_10_5': float(1.0 if corners_total > 10.5 else 0.0),
            'corners_over_11_5': float(1.0 if corners_total > 11.5 else 0.0),
            'cards_yellow': float(yellow_cards),
            'cards_red': float(red_cards),
            'cards_total': float(total_cards),
            'cards_over_3_5': float(1.0 if total_cards > 3.5 else 0.0),
            'cards_over_4_5': float(1.0 if total_cards > 4.5 else 0.0),
            'shots_home': float(shots_home),
            'shots_away': float(shots_away),
            'shots_total': float(shots_total),
            'shots_on_target_home': float(shots_on_target_home),
            'shots_on_target_away': float(shots_on_target_away)
        }

# Función de conveniencia
def crear_predictor_corregido():
    """Crea y entrena el predictor corregido"""
    predictor = PredictorReglasDinamicasCorregido()
    predictor.load_and_train()
    return predictor

if __name__ == "__main__":
    # Probar el predictor corregido
    predictor = crear_predictor_corregido()
    
    # Probar con Newcastle vs Fulham
    resultado = predictor.predict_con_reglas_dinamicas(
        'Newcastle United FC',
        'Fulham FC',
        'E0'
    )
    
    print(f"\n🎯 RESULTADO:")
    print(f"   Newcastle: {resultado['1x2']['pH']*100:.1f}%")
    print(f"   Empate: {resultado['1x2']['pD']*100:.1f}%")
    print(f"   Fulham: {resultado['1x2']['pA']*100:.1f}%")
    
    print(f"\n✅ PREDICTOR CORREGIDO FUNCIONANDO")
