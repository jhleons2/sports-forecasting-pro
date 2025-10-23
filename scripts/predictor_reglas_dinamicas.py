"""
PREDICTOR CON REGLAS DINÁMICAS
===============================

Predictor que calcula las 5 reglas en TIEMPO REAL para cada partido.

Las reglas se calculan DINÁMICAMENTE desde HOY:
1. Últimos 8 partidos total (desde HOY hacia atrás)
2. Últimos 5 de local (desde HOY hacia atrás)
3. Últimos 5 de visitante (desde HOY hacia atrás)
4. 5 entre sí (desde HOY hacia atrás)
5. Bajas de jugadores (AL MOMENTO)

NO usa features pre-calculados, calcula TODO en tiempo real.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import pandas as pd
import numpy as np
from datetime import datetime, date
from typing import Optional, Dict
from src.models.poisson_dc import DixonColes
from src.models.xgboost_classifier import XGBoost1X2Classifier
from src.features.reglas_dinamicas import calcular_reglas_dinamicas, preparar_features_para_prediccion
from src.features.ratings import add_elo

PROC = Path("data/processed")

class PredictorReglasDinamicas:
    """
    Predictor que calcula reglas DINÁMICAMENTE para cada partido.
    """
    
    def __init__(self):
        self.dc_model = None
        self.xgb_model = None
        self.calibrator = None
        self.df_historico = None
        self.df_con_elo = None
        
    def load_and_train(self):
        """
        Carga datos históricos y entrena modelos.
        """
        print("\n" + "=" * 70)
        print("  PREDICTOR CON REGLAS DINÁMICAS - INICIALIZANDO")
        print("=" * 70)
        print("\n✅ Las reglas se calcularán DINÁMICAMENTE desde HOY")
        print("   para cada predicción.\n")
        
        # 1. Cargar datos históricos base (sin features pre-calculados)
        print("1. Cargando datos históricos base...")
        self.df_historico = pd.read_parquet(PROC / "matches.parquet")
        print(f"   {len(self.df_historico)} partidos cargados")
        
        # 2. Añadir ELO (necesario para el modelo)
        print("\n2. Calculando ELO ratings...")
        self.df_con_elo = add_elo(self.df_historico)
        print("   OK")
        
        # 3. Entrenar Dixon-Coles
        print("\n3. Entrenando Dixon-Coles...")
        self.dc_model = DixonColes().fit(self.df_con_elo)
        print("   OK")
        
        # 4. Entrenar XGBoost con dataset CON REGLAS (pre-calculado para entrenamiento)
        print("\n4. Entrenando XGBoost con reglas...")
        df_reglas = pd.read_parquet(PROC / "matches_con_reglas.parquet")
        
        feature_cols = [
            'EloHome', 'EloAway',
            'Home_Pts_ultimos8_liga', 'Home_GD_ultimos8_liga',
            'Away_Pts_ultimos8_liga', 'Away_GD_ultimos8_liga',
            'Home_GF_local5_liga', 'Home_GA_local5_liga', 'Home_GD_local5_liga',
            'Away_GF_visitante5_liga', 'Away_GA_visitante5_liga', 'Away_GD_visitante5_liga',
            'H2H5_home_wins', 'H2H5_away_wins', 'H2H5_total_goals_avg',
            'Home_jugadores_clave_bajas', 'Away_jugadores_clave_bajas'
        ]
        
        train_df = df_reglas[df_reglas[feature_cols].notna().all(axis=1)].copy()
        
        # Añadir target si no existe
        if 'y' not in train_df.columns:
            def lab(r):
                if r['FTHG'] > r['FTAG']: return 0
                if r['FTHG'] == r['FTAG']: return 1
                return 2
            train_df['y'] = train_df.apply(lab, axis=1)
        
        X_train = train_df[feature_cols].fillna(0)
        xgb_df = X_train.copy()
        xgb_df['y'] = train_df['y'].values
        
        self.xgb_model = XGBoost1X2Classifier(n_estimators=100, max_depth=5)
        self.xgb_model.fit(xgb_df)
        print("   OK")
        
        # 5. Calibrar
        print("\n5. Calibrando probabilidades...")
        probs_raw = self.xgb_model.predict_proba(xgb_df.drop('y', axis=1))
        y_true = train_df['y'].values
        
        from sklearn.isotonic import IsotonicRegression
        self.calibrator = {}
        for i, clase in enumerate(['H', 'D', 'A']):
            cal = IsotonicRegression(out_of_bounds='clip')
            y_bin = (y_true == i).astype(int)
            cal.fit(probs_raw.iloc[:, i].values, y_bin)
            self.calibrator[clase] = cal
        
        print("   OK")
        print("\n" + "=" * 70)
        print("  PREDICTOR LISTO - Reglas se calcularán dinámicamente")
        print("=" * 70)
        
    def predict_con_reglas_dinamicas(self, 
                                     equipo_home: str, 
                                     equipo_away: str, 
                                     liga: str,
                                     fecha_partido: Optional[date] = None) -> dict:
        """
        Hace predicción calculando reglas DINÁMICAMENTE.
        
        Parameters:
        -----------
        equipo_home : str
            Equipo local
        equipo_away : str
            Equipo visitante
        liga : str
            Código de la liga
        fecha_partido : date, optional
            Fecha del partido (default: HOY para futuros)
            
        Returns:
        --------
        dict : Predicciones + reglas usadas
        """
        print(f"\n{'='*70}")
        print(f"  PREDICCIÓN CON REGLAS DINÁMICAS")
        print(f"{'='*70}")
        
        # 1. Calcular reglas DINÁMICAMENTE desde HOY
        reglas = calcular_reglas_dinamicas(
            self.df_historico,
            equipo_home,
            equipo_away,
            liga,
            fecha_partido
        )
        
        # 2. Preparar features
        features = preparar_features_para_prediccion(reglas)
        
        # 3. Añadir ELO actual
        elo_home = self.df_con_elo[
            (self.df_con_elo['HomeTeam'] == equipo_home) | 
            (self.df_con_elo['AwayTeam'] == equipo_home)
        ].tail(1)
        
        elo_away = self.df_con_elo[
            (self.df_con_elo['HomeTeam'] == equipo_away) | 
            (self.df_con_elo['AwayTeam'] == equipo_away)
        ].tail(1)
        
        if len(elo_home) > 0:
            features['EloHome'] = elo_home.iloc[0].get('EloHome', elo_home.iloc[0].get('EloAway', 1500))
        else:
            features['EloHome'] = 1500
            
        if len(elo_away) > 0:
            features['EloAway'] = elo_away.iloc[0].get('EloAway', elo_away.iloc[0].get('EloHome', 1500))
        else:
            features['EloAway'] = 1500
        
        # 4. Predecir 1X2 con XGBoost
        pred_df = pd.DataFrame([features])
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
        
        # 5. Estimar goles con Dixon-Coles
        match_row = pd.Series(features)
        
        # Over/Under
        ou = self.dc_model.prob_over_under(match_row, line=2.5)
        
        # xG estimado
        params = self.dc_model.params_
        elo_diff = (features['EloHome'] - features['EloAway']) / 400.0
        xG_home = np.exp(params[0] + params[1] * elo_diff + params[4])
        xG_away = np.exp(params[2] - params[3] * elo_diff)
        
        return {
            'equipo_home': equipo_home,
            'equipo_away': equipo_away,
            'liga': liga,
            'fecha_calculo': datetime.now().date().isoformat(),
            
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
            'reglas': reglas  # Incluir TODAS las reglas calculadas
        }


def main():
    """
    Ejemplo de uso con cálculo dinámico.
    """
    print("""
╔════════════════════════════════════════════════════════════════╗
║  PREDICTOR CON REGLAS DINÁMICAS                                ║
║  Las reglas se calculan DESDE HOY para cada predicción         ║
╚════════════════════════════════════════════════════════════════╝
    """)
    
    # Inicializar
    predictor = PredictorReglasDinamicas()
    predictor.load_and_train()
    
    # Ejemplo: Arsenal vs Chelsea (Premier League)
    print("\n" + "=" * 70)
    print("  EJEMPLO: Partido Futuro")
    print("=" * 70)
    
    resultado = predictor.predict_con_reglas_dinamicas(
        equipo_home="Arsenal",
        equipo_away="Chelsea",
        liga="E0"
        # fecha_partido no especificada = se calcula desde HOY
    )
    
    # Mostrar resultados
    print(f"\n\n{'='*70}")
    print(f"  PREDICCIÓN: {resultado['equipo_home']} vs {resultado['equipo_away']}")
    print(f"  Liga: {resultado['liga']}")
    print(f"  Calculado: {resultado['fecha_calculo']}")
    print(f"{'='*70}")
    
    print("\n1X2:")
    print(f"  {resultado['equipo_home']}: {resultado['1x2']['pH']*100:.1f}%")
    print(f"  Empate: {resultado['1x2']['pD']*100:.1f}%")
    print(f"  {resultado['equipo_away']}: {resultado['1x2']['pA']*100:.1f}%")
    
    print("\nGoles Esperados:")
    print(f"  {resultado['equipo_home']}: {resultado['goals']['xG_home']:.2f}")
    print(f"  {resultado['equipo_away']}: {resultado['goals']['xG_away']:.2f}")
    print(f"  Total: {resultado['goals']['xG_total']:.2f}")
    
    print("\nOver/Under 2.5:")
    print(f"  Over:  {resultado['over_under']['pOver']*100:.1f}%")
    print(f"  Under: {resultado['over_under']['pUnder']*100:.1f}%")
    
    # Mostrar reglas usadas
    from src.features.reglas_dinamicas import formato_reglas_texto
    print("\n" + formato_reglas_texto(resultado['reglas']))
    
    print("\n✅ PREDICCIÓN COMPLETADA")
    print(f"   Todas las reglas calculadas desde HOY ({resultado['fecha_calculo']})")
    print(f"   NO usa datos pre-calculados, TODO es dinámico")


if __name__ == "__main__":
    main()

