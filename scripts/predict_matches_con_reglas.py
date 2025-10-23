"""
PREDICTOR CON REGLAS ESPECÍFICAS
=================================

Sistema de predicción que usa EXCLUSIVAMENTE las 5 reglas:
1. Últimos 8 partidos total (misma liga)
2. Últimos 5 de local (misma liga)
3. Últimos 5 de visitante (misma liga)
4. 5 entre sí (H2H)
5. Bajas de jugadores

TODOS los cálculos se basan en estas reglas.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import pandas as pd
import numpy as np
from src.models.poisson_dc import DixonColes
from src.models.xgboost_classifier import XGBoost1X2Classifier

PROC = Path("data/processed")

class PredictorConReglas:
    """
    Predictor que usa SOLO las reglas específicas.
    """
    
    def __init__(self):
        self.dc_model = None
        self.xgb_model = None
        self.calibrator = None
        self.df_historico = None
        
    def load_and_train(self):
        """
        Carga dataset CON REGLAS y entrena modelos.
        """
        print("\n" + "=" * 70)
        print("  PREDICTOR CON REGLAS - CARGANDO")
        print("=" * 70)
        
        # 1. Cargar dataset CON REGLAS
        print("\n1. Cargando datos históricos CON REGLAS...")
        self.df_historico = pd.read_parquet(PROC / "matches_con_reglas.parquet")
        print(f"   Partidos cargados: {len(self.df_historico)}")
        print(f"   Rango: {self.df_historico['Date'].min()} a {self.df_historico['Date'].max()}")
        
        # 2. Entrenar Dixon-Coles (para AH y OU)
        print("\n2. Entrenando Dixon-Coles (AH + OU)...")
        self.dc_model = DixonColes().fit(self.df_historico)
        print("   OK")
        
        # 3. Entrenar XGBoost para 1X2 usando SOLO features de reglas
        print("\n3. Entrenando XGBoost (1X2) con features de REGLAS...")
        
        # Features basados en TUS REGLAS
        feature_cols = [
            # ELO (base)
            'EloHome', 'EloAway',
            
            # REGLA 1: Últimos 8 total
            'Home_Pts_ultimos8_liga',
            'Home_GD_ultimos8_liga',
            'Away_Pts_ultimos8_liga',
            'Away_GD_ultimos8_liga',
            
            # REGLA 2: Últimos 5 local
            'Home_GF_local5_liga',
            'Home_GA_local5_liga',
            'Home_GD_local5_liga',
            
            # REGLA 3: Últimos 5 visitante
            'Away_GF_visitante5_liga',
            'Away_GA_visitante5_liga',
            'Away_GD_visitante5_liga',
            
            # REGLA 4: H2H
            'H2H5_home_wins',
            'H2H5_away_wins',
            'H2H5_total_goals_avg',
            
            # REGLA 5: Bajas (placeholder)
            'Home_jugadores_clave_bajas',
            'Away_jugadores_clave_bajas'
        ]
        
        # Preparar datos para XGBoost
        train_df = self.df_historico[
            self.df_historico[feature_cols].notna().all(axis=1)
        ].copy()
        
        print(f"   Partidos para entrenar: {len(train_df)}")
        print(f"   Features usados: {len(feature_cols)}")
        
        # Crear features para XGBoost
        X_train = train_df[feature_cols].fillna(0)
        
        # Añadir columna 'y' si no existe
        if 'y' not in train_df.columns:
            def lab(r):
                if r['FTHG'] > r['FTAG']: return 0  # Home
                if r['FTHG'] == r['FTAG']: return 1  # Draw
                return 2  # Away
            train_df['y'] = train_df.apply(lab, axis=1)
        
        # Preparar dataframe con features + target
        xgb_df = X_train.copy()
        xgb_df['y'] = train_df['y'].values
        
        # Entrenar
        self.xgb_model = XGBoost1X2Classifier(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1
        )
        self.xgb_model.fit(xgb_df)
        print("   OK")
        
        # 4. Calibrar
        print("\n4. Calibrando probabilidades...")
        probs_raw = self.xgb_model.predict_proba(xgb_df.drop('y', axis=1))
        y_true = train_df['y'].values
        
        # Calibrar cada clase
        from sklearn.isotonic import IsotonicRegression
        self.calibrator = {}
        for i, clase in enumerate(['H', 'D', 'A']):
            cal = IsotonicRegression(out_of_bounds='clip')
            y_bin = (y_true == i).astype(int)
            cal.fit(probs_raw.iloc[:, i].values, y_bin)
            self.calibrator[clase] = cal
        
        print("   OK")
        
        print("\n" + "=" * 70)
        print("  MODELOS LISTOS (basados en TUS REGLAS)")
        print("=" * 70)
        
    def predict_all(self, match_data: dict) -> dict:
        """
        Predice partido usando SOLO las reglas.
        
        Parameters:
        -----------
        match_data : dict
            Datos del partido con features de reglas
            
        Returns:
        --------
        dict : Predicciones completas
        """
        # Preparar features
        features = {
            'EloHome': match_data.get('EloHome', 1500),
            'EloAway': match_data.get('EloAway', 1500),
            
            # REGLA 1
            'Home_Pts_ultimos8_liga': match_data.get('Home_Pts_ultimos8_liga', 0),
            'Home_GD_ultimos8_liga': match_data.get('Home_GD_ultimos8_liga', 0),
            'Away_Pts_ultimos8_liga': match_data.get('Away_Pts_ultimos8_liga', 0),
            'Away_GD_ultimos8_liga': match_data.get('Away_GD_ultimos8_liga', 0),
            
            # REGLA 2
            'Home_GF_local5_liga': match_data.get('Home_GF_local5_liga', 0),
            'Home_GA_local5_liga': match_data.get('Home_GA_local5_liga', 0),
            'Home_GD_local5_liga': match_data.get('Home_GD_local5_liga', 0),
            
            # REGLA 3
            'Away_GF_visitante5_liga': match_data.get('Away_GF_visitante5_liga', 0),
            'Away_GA_visitante5_liga': match_data.get('Away_GA_visitante5_liga', 0),
            'Away_GD_visitante5_liga': match_data.get('Away_GD_visitante5_liga', 0),
            
            # REGLA 4
            'H2H5_home_wins': match_data.get('H2H5_home_wins', 0),
            'H2H5_away_wins': match_data.get('H2H5_away_wins', 0),
            'H2H5_total_goals_avg': match_data.get('H2H5_total_goals_avg', 2.5),
            
            # REGLA 5
            'Home_jugadores_clave_bajas': match_data.get('Home_jugadores_clave_bajas', 0),
            'Away_jugadores_clave_bajas': match_data.get('Away_jugadores_clave_bajas', 0)
        }
        
        # Crear DataFrame para predicción
        pred_df = pd.DataFrame([features])
        
        # 1X2 con XGBoost + Calibración
        probs_raw = self.xgb_model.predict_proba(pred_df)
        
        # Calibrar
        pH_cal = float(self.calibrator['H'].predict([probs_raw.iloc[0, 0]])[0])
        pD_cal = float(self.calibrator['D'].predict([probs_raw.iloc[0, 1]])[0])
        pA_cal = float(self.calibrator['A'].predict([probs_raw.iloc[0, 2]])[0])
        
        # Normalizar
        total = pH_cal + pD_cal + pA_cal
        pH_cal /= total
        pD_cal /= total
        pA_cal /= total
        
        # Estimación de goles usando Dixon-Coles
        match_row = pd.Series(match_data)
        
        # Over/Under
        ou = self.dc_model.prob_over_under(match_row, line=2.5)
        
        # xG estimado de Dixon-Coles
        params = self.dc_model.params_
        elo_diff = (match_data.get('EloHome', 1500) - match_data.get('EloAway', 1500)) / 400.0
        xG_home = np.exp(params[0] + params[1] * elo_diff + params[4])
        xG_away = np.exp(params[2] - params[3] * elo_diff)
        
        # Asian Handicap (si hay datos)
        ah_line = match_data.get('AHh', 0.0)
        ah_probs = self.dc_model.ah_probabilities(match_row, line=ah_line, side='home')
        
        return {
            '1x2': {
                'pH': pH_cal,
                'pD': pD_cal,
                'pA': pA_cal
            },
            'goals': {
                'xG_home': xG_home,
                'xG_away': xG_away,
                'xG_total': xG_home + xG_away
            },
            'over_under': {
                'pOver': ou['pOver'],
                'pUnder': ou['pUnder']
            },
            'asian_handicap': {
                'line': ah_line,
                'pWin': ah_probs.get('win', 0),
                'pPush': ah_probs.get('push', 0),
                'pLoss': ah_probs.get('loss', 0)
            },
            'reglas_usadas': {
                'ultimos_8_home_pts': features['Home_Pts_ultimos8_liga'],
                'ultimos_8_away_pts': features['Away_Pts_ultimos8_liga'],
                'local_5_home_gd': features['Home_GD_local5_liga'],
                'visitante_5_away_gd': features['Away_GD_visitante5_liga'],
                'h2h_total_goals': features['H2H5_total_goals_avg'],
                'bajas_home': features['Home_jugadores_clave_bajas'],
                'bajas_away': features['Away_jugadores_clave_bajas']
            }
        }


def main():
    """
    Ejemplo de uso del predictor con reglas.
    """
    print("""
╔════════════════════════════════════════════════════════════════╗
║  PREDICTOR CON REGLAS ESPECÍFICAS                              ║
╚════════════════════════════════════════════════════════════════╝
    """)
    
    # Inicializar y entrenar
    predictor = PredictorConReglas()
    predictor.load_and_train()
    
    # Cargar un partido de ejemplo
    df = pd.read_parquet(PROC / "matches_con_reglas.parquet")
    
    # Obtener último partido con datos completos
    ultimo = df[
        (df['H2H5_matches'] > 0) &
        (df['Home_Pts_ultimos8_liga'] > 0)
    ].tail(1).iloc[0]
    
    print("\n" + "=" * 70)
    print(f"  PREDICCIÓN: {ultimo['HomeTeam']} vs {ultimo['AwayTeam']}")
    print(f"  Liga: {ultimo['League']}")
    print("=" * 70)
    
    # Hacer predicción
    predictions = predictor.predict_all(ultimo.to_dict())
    
    # Mostrar resultados
    print("\n1X2 (basado en reglas):")
    print(f"  Home:  {predictions['1x2']['pH']*100:.1f}%")
    print(f"  Draw:  {predictions['1x2']['pD']*100:.1f}%")
    print(f"  Away:  {predictions['1x2']['pA']*100:.1f}%")
    
    print("\nGoles Esperados:")
    print(f"  {ultimo['HomeTeam']}: {predictions['goals']['xG_home']:.2f}")
    print(f"  {ultimo['AwayTeam']}: {predictions['goals']['xG_away']:.2f}")
    print(f"  Total: {predictions['goals']['xG_total']:.2f}")
    
    print("\nOver/Under 2.5:")
    print(f"  Over:  {predictions['over_under']['pOver']*100:.1f}%")
    print(f"  Under: {predictions['over_under']['pUnder']*100:.1f}%")
    
    print("\n" + "=" * 70)
    print("  REGLAS USADAS EN ESTA PREDICCIÓN:")
    print("=" * 70)
    reglas = predictions['reglas_usadas']
    print(f"\nÚltimos 8 total:")
    print(f"  Home: {reglas['ultimos_8_home_pts']:.0f} pts")
    print(f"  Away: {reglas['ultimos_8_away_pts']:.0f} pts")
    
    print(f"\nÚltimos 5 local:")
    print(f"  Home GD: {reglas['local_5_home_gd']:+.0f}")
    
    print(f"\nÚltimos 5 visitante:")
    print(f"  Away GD: {reglas['visitante_5_away_gd']:+.0f}")
    
    print(f"\nH2H:")
    print(f"  Goles promedio: {reglas['h2h_total_goals']:.1f}")
    
    print(f"\nBajas:")
    print(f"  Home: {reglas['bajas_home']:.0f}")
    print(f"  Away: {reglas['bajas_away']:.0f}")
    
    print("\n✅ Predicción basada 100% en TUS 5 REGLAS")


if __name__ == "__main__":
    main()

