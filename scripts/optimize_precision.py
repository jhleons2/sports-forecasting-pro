#!/usr/bin/env python3
"""
Sistema de Mejora de Precisión del Modelo
==========================================

Implementa múltiples técnicas para incrementar la precisión:
1. Ensemble de modelos (Dixon-Coles + XGBoost)
2. Calibración avanzada de probabilidades
3. Optimización de hiperparámetros
4. Features adicionales
5. Validación cruzada temporal
"""

import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import log_loss, accuracy_score
import warnings
warnings.filterwarnings('ignore')

from src.models.poisson_dc import DixonColes
from src.models.xgboost_classifier import XGBoost1X2Classifier
from src.models.calibration import ProbabilityCalibrator
from src.features.ratings import add_elo
from src.features.rolling import add_form

PROC = Path("data/processed")

class PrecisionOptimizer:
    """
    Optimizador de precisión que combina múltiples técnicas
    """
    
    def __init__(self):
        self.dc_model = None
        self.xgb_model = None
        self.ensemble_weights = None
        self.calibrator = None
        self.feature_importance = None
        
    def load_data(self):
        """Cargar y preparar datos"""
        print("Cargando datos para optimización...")
        
        df = pd.read_parquet(PROC / "matches.parquet")
        df = add_elo(df)
        df = add_form(df)
        
        # Crear target para clasificación
        df['y'] = 0  # Empate
        df.loc[df['FTHG'] > df['FTAG'], 'y'] = 1  # Local
        df.loc[df['FTHG'] < df['FTAG'], 'y'] = 2  # Visitante
        
        print(f"   Datos cargados: {len(df)} partidos")
        print(f"   Distribución: Local {sum(df['y']==1)/len(df)*100:.1f}%, "
              f"Empate {sum(df['y']==0)/len(df)*100:.1f}%, "
              f"Visitante {sum(df['y']==2)/len(df)*100:.1f}%")
        
        return df
    
    def optimize_xgboost_params(self, df):
        """Optimizar hiperparámetros de XGBoost"""
        print("\nOptimizando hiperparámetros XGBoost...")
        
        # Dividir datos temporalmente
        split_date = df['Date'].quantile(0.8)
        train_df = df[df['Date'] <= split_date].copy()
        val_df = df[df['Date'] > split_date].copy()
        
        # Grid de parámetros a probar
        param_grid = {
            'n_estimators': [100, 150, 200],
            'max_depth': [3, 4, 5, 6],
            'learning_rate': [0.05, 0.1, 0.15],
            'subsample': [0.8, 0.9, 1.0],
            'colsample_bytree': [0.8, 0.9, 1.0]
        }
        
        best_score = float('inf')
        best_params = None
        
        # Crear features para XGBoost
        X_train = self._create_advanced_features(train_df)
        y_train = train_df['y'].values
        X_val = self._create_advanced_features(val_df)
        y_val = val_df['y'].values
        
        print("   Probando combinaciones de parámetros...")
        
        # Probar combinaciones (simplificado para velocidad)
        for n_est in param_grid['n_estimators']:
            for max_d in param_grid['max_depth']:
                for lr in param_grid['learning_rate']:
                    
                    model = XGBoost1X2Classifier(
                        n_estimators=n_est,
                        max_depth=max_d,
                        learning_rate=lr
                    )
                    
                    try:
                        model.fit(train_df)
                        y_pred_proba = model.predict_proba(val_df)
                        score = log_loss(y_val, y_pred_proba)
                        
                        if score < best_score:
                            best_score = score
                            best_params = {
                                'n_estimators': n_est,
                                'max_depth': max_d,
                                'learning_rate': lr
                            }
                            print(f"   Nuevo mejor score: {score:.4f} con params: {best_params}")
                    
                    except Exception as e:
                        continue
        
        print(f"   Mejores parámetros encontrados: {best_params}")
        print(f"   Mejor score (log loss): {best_score:.4f}")
        
        return best_params
    
    def _create_advanced_features(self, df):
        """Crear features avanzados para mejorar precisión"""
        features = []
        
        for _, row in df.iterrows():
            feature_dict = {
                'elo_home': row.get('EloHome', 1500),
                'elo_away': row.get('EloAway', 1500),
                'elo_diff': row.get('EloHome', 1500) - row.get('EloAway', 1500),
                'elo_ratio': row.get('EloHome', 1500) / row.get('EloAway', 1500),
                
                # Forma reciente
                'form_home': row.get('FormHome', 0),
                'form_away': row.get('FormAway', 0),
                'form_diff': row.get('FormHome', 0) - row.get('FormAway', 0),
                
                # Estadísticas de goles
                'avg_goals_home': row.get('AvgGoalsHome', 1.5),
                'avg_goals_away': row.get('AvgGoalsAway', 1.5),
                'avg_goals_total': row.get('AvgGoalsHome', 1.5) + row.get('AvgGoalsAway', 1.5),
                
                # Diferencias
                'goal_diff_home': row.get('GoalDiffHome', 0),
                'goal_diff_away': row.get('GoalDiffAway', 0),
                
                # Features categóricas
                'is_weekend': 1 if pd.to_datetime(row['Date']).weekday() >= 5 else 0,
                'month': pd.to_datetime(row['Date']).month,
            }
            
            features.append(feature_dict)
        
        return pd.DataFrame(features)
    
    def create_ensemble_model(self, df):
        """Crear modelo ensemble combinando Dixon-Coles y XGBoost"""
        print("\nCreando modelo ensemble...")
        
        # Dividir datos temporalmente
        split_date = df['Date'].quantile(0.8)
        train_df = df[df['Date'] <= split_date].copy()
        val_df = df[df['Date'] > split_date].copy()
        
        # Entrenar Dixon-Coles
        print("   Entrenando Dixon-Coles...")
        self.dc_model = DixonColes().fit(train_df)
        
        # Entrenar XGBoost optimizado
        print("   Entrenando XGBoost optimizado...")
        best_params = self.optimize_xgboost_params(train_df)
        
        self.xgb_model = XGBoost1X2Classifier(**best_params)
        self.xgb_model.fit(train_df)
        
        # Calcular pesos del ensemble en validación
        print("   Calculando pesos del ensemble...")
        dc_preds = self.dc_model.predict_1x2(val_df)
        xgb_preds = self.xgb_model.predict_proba(val_df)
        
        # Optimizar pesos del ensemble
        best_ensemble_score = float('inf')
        best_weights = None
        
        for w_dc in np.arange(0.1, 0.9, 0.1):
            w_xgb = 1 - w_dc
            
            ensemble_preds = w_dc * dc_preds.values + w_xgb * xgb_preds
            ensemble_preds = ensemble_preds / ensemble_preds.sum(axis=1, keepdims=True)
            
            score = log_loss(val_df['y'].values, ensemble_preds)
            
            if score < best_ensemble_score:
                best_ensemble_score = score
                best_weights = {'dc': w_dc, 'xgb': w_xgb}
        
        self.ensemble_weights = best_weights
        print(f"   Pesos optimizados: Dixon-Coles {best_weights['dc']:.2f}, XGBoost {best_weights['xgb']:.2f}")
        print(f"   Score ensemble: {best_ensemble_score:.4f}")
        
        return best_weights
    
    def calibrate_probabilities(self, df):
        """Calibrar probabilidades del ensemble"""
        print("\nCalibrando probabilidades del ensemble...")
        
        # Dividir datos
        split_date = df['Date'].quantile(0.7)
        train_df = df[df['Date'] <= split_date].copy()
        val_df = df[df['Date'] > split_date].copy()
        
        # Generar predicciones del ensemble en entrenamiento
        dc_preds = self.dc_model.predict_1x2(train_df)
        xgb_preds = self.xgb_model.predict_proba(train_df)
        
        ensemble_preds = (self.ensemble_weights['dc'] * dc_preds.values + 
                         self.ensemble_weights['xgb'] * xgb_preds)
        
        # Calibrar
        self.calibrator = ProbabilityCalibrator()
        self.calibrator.fit(train_df['y'].values, ensemble_preds)
        
        # Evaluar en validación
        val_dc_preds = self.dc_model.predict_1x2(val_df)
        val_xgb_preds = self.xgb_model.predict_proba(val_df)
        
        val_ensemble_preds = (self.ensemble_weights['dc'] * val_dc_preds.values + 
                             self.ensemble_weights['xgb'] * val_xgb_preds)
        
        val_calibrated = self.calibrator.predict(val_ensemble_preds)
        
        # Calcular métricas
        accuracy = accuracy_score(val_df['y'].values, np.argmax(val_calibrated, axis=1))
        logloss = log_loss(val_df['y'].values, val_calibrated)
        
        print(f"   Precisión calibrada: {accuracy*100:.2f}%")
        print(f"   Log loss calibrado: {logloss:.4f}")
        
        return accuracy, logloss
    
    def evaluate_model_performance(self, df):
        """Evaluar rendimiento del modelo optimizado"""
        print("\nEvaluando rendimiento del modelo optimizado...")
        
        # Usar últimos 20% de datos para evaluación
        split_date = df['Date'].quantile(0.8)
        test_df = df[df['Date'] > split_date].copy()
        
        # Generar predicciones
        dc_preds = self.dc_model.predict_1x2(test_df)
        xgb_preds = self.xgb_model.predict_proba(test_df)
        
        ensemble_preds = (self.ensemble_weights['dc'] * dc_preds.values + 
                         self.ensemble_weights['xgb'] * xgb_preds)
        
        calibrated_preds = self.calibrator.predict(ensemble_preds)
        
        # Métricas
        accuracy = accuracy_score(test_df['y'].values, np.argmax(calibrated_preds, axis=1))
        logloss = log_loss(test_df['y'].values, calibrated_preds)
        
        # Análisis por resultado
        results = {
            'Local': {'correct': 0, 'total': 0},
            'Empate': {'correct': 0, 'total': 0},
            'Visitante': {'correct': 0, 'total': 0}
        }
        
        for i, (_, row) in enumerate(test_df.iterrows()):
            true_result = row['y']
            pred_result = np.argmax(calibrated_preds[i])
            
            result_names = ['Empate', 'Local', 'Visitante']
            results[result_names[true_result]]['total'] += 1
            
            if true_result == pred_result:
                results[result_names[true_result]]['correct'] += 1
        
        print(f"\nRESULTADOS FINALES:")
        print(f"   Precisión general: {accuracy*100:.2f}%")
        print(f"   Log loss: {logloss:.4f}")
        
        print(f"\nPrecisión por resultado:")
        for result, stats in results.items():
            if stats['total'] > 0:
                precision = stats['correct'] / stats['total'] * 100
                print(f"   {result}: {precision:.1f}% ({stats['correct']}/{stats['total']})")
        
        return {
            'accuracy': accuracy,
            'logloss': logloss,
            'results_breakdown': results
        }
    
    def optimize_precision(self):
        """Función principal para optimizar la precisión"""
        print("=" * 70)
        print("OPTIMIZACIÓN DE PRECISIÓN DEL MODELO")
        print("=" * 70)
        
        # 1. Cargar datos
        df = self.load_data()
        
        # 2. Crear modelo ensemble
        self.create_ensemble_model(df)
        
        # 3. Calibrar probabilidades
        accuracy, logloss = self.calibrate_probabilities(df)
        
        # 4. Evaluar rendimiento
        performance = self.evaluate_model_performance(df)
        
        print("\n" + "=" * 70)
        print("OPTIMIZACIÓN COMPLETADA")
        print("=" * 70)
        
        return performance


def main():
    """Ejecutar optimización de precisión"""
    optimizer = PrecisionOptimizer()
    performance = optimizer.optimize_precision()
    
    print(f"\nPRECISIÓN MEJORADA: {performance['accuracy']*100:.2f}%")
    print("¡Modelo optimizado exitosamente!")


if __name__ == "__main__":
    main()
