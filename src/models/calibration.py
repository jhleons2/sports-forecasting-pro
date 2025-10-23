"""
Módulo de calibración de probabilidades para modelos de predicción deportiva.

Implementa calibración isotónica para ajustar la confianza del modelo
y alinear las probabilidades predichas con las frecuencias observadas.
"""

import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression


class ProbabilityCalibrator:
    """
    Calibra probabilidades de modelos 1X2 usando regresión isotónica.
    
    La calibración corrige el "overconfidence" o "underconfidence" del modelo,
    ajustando las probabilidades predichas para que reflejen mejor las
    frecuencias reales observadas en los datos.
    
    Ejemplo:
        Si el modelo predice pH=0.75 pero históricamente solo gana el 55%,
        la calibración ajustará la probabilidad a ~0.55.
    """
    
    def __init__(self):
        """Inicializa los calibradores para cada outcome (H, D, A)."""
        self.calibrators = {
            'H': IsotonicRegression(out_of_bounds='clip', y_min=0.0, y_max=1.0),
            'D': IsotonicRegression(out_of_bounds='clip', y_min=0.0, y_max=1.0),
            'A': IsotonicRegression(out_of_bounds='clip', y_min=0.0, y_max=1.0)
        }
        self.is_fitted = False
    
    def fit(self, y_true, probs_df):
        """
        Entrena los calibradores con datos históricos.
        
        Parameters:
        -----------
        y_true : array-like
            Outcomes reales (0=Home, 1=Draw, 2=Away)
        probs_df : pd.DataFrame
            DataFrame con columnas ['pH', 'pD', 'pA'] de probabilidades predichas
        
        Returns:
        --------
        self : ProbabilityCalibrator
            Instancia entrenada
        """
        y_true = np.array(y_true)
        
        # Convertir a DataFrame si es necesario
        if not isinstance(probs_df, pd.DataFrame):
            probs_df = pd.DataFrame(probs_df, columns=['pH', 'pD', 'pA'])
        
        # Entrenar un calibrador para cada outcome
        for idx, outcome in enumerate(['H', 'D', 'A']):
            # Crear variable binaria: 1 si outcome ocurrió, 0 si no
            y_binary = (y_true == idx).astype(float)
            
            # Obtener probabilidades predichas para este outcome
            p_pred = probs_df[f'p{outcome}'].values
            
            # Validar que hay suficientes datos
            if len(p_pred) < 10:
                print(f"  ⚠️ Advertencia: Solo {len(p_pred)} muestras para calibrar {outcome}")
            
            # Entrenar calibrador isotónico
            self.calibrators[outcome].fit(p_pred, y_binary)
        
        self.is_fitted = True
        return self
    
    def transform(self, probs_df):
        """
        Aplica calibración a probabilidades nuevas.
        
        Parameters:
        -----------
        probs_df : pd.DataFrame
            DataFrame con columnas ['pH', 'pD', 'pA'] de probabilidades sin calibrar
        
        Returns:
        --------
        calibrated_df : pd.DataFrame
            DataFrame con probabilidades calibradas y normalizadas
        """
        if not self.is_fitted:
            raise ValueError("Calibrador no ha sido entrenado. Llama a fit() primero.")
        
        # Convertir a DataFrame si es necesario
        if not isinstance(probs_df, pd.DataFrame):
            probs_df = pd.DataFrame(probs_df, columns=['pH', 'pD', 'pA'])
        
        calibrated = {}
        
        # Aplicar calibración a cada outcome
        for outcome in ['H', 'D', 'A']:
            p_pred = probs_df[f'p{outcome}'].values
            calibrated[f'p{outcome}'] = self.calibrators[outcome].transform(p_pred)
        
        # Convertir a DataFrame
        calibrated_df = pd.DataFrame(calibrated)
        
        # Renormalizar para que sumen 1.0
        row_sums = calibrated_df.sum(axis=1)
        for col in calibrated_df.columns:
            calibrated_df[col] = calibrated_df[col] / row_sums
        
        return calibrated_df
    
    def fit_transform(self, y_true, probs_df):
        """
        Entrena y transforma en un solo paso (solo para datos de entrenamiento).
        
        Parameters:
        -----------
        y_true : array-like
            Outcomes reales (0=Home, 1=Draw, 2=Away)
        probs_df : pd.DataFrame
            DataFrame con columnas ['pH', 'pD', 'pA']
        
        Returns:
        --------
        calibrated_df : pd.DataFrame
            DataFrame con probabilidades calibradas
        """
        self.fit(y_true, probs_df)
        return self.transform(probs_df)


class BlendCalibrator:
    """
    Blending entre probabilidades del modelo y probabilidades del mercado.
    
    Combina las predicciones del modelo con las probabilidades implícitas
    del mercado (odds) usando un peso ajustable.
    
    Formula:
        p_final = alpha * p_modelo + (1 - alpha) * p_mercado
    
    donde alpha es el peso del modelo (0 = solo mercado, 1 = solo modelo)
    """
    
    def __init__(self, alpha=0.7):
        """
        Inicializa el blender.
        
        Parameters:
        -----------
        alpha : float, default=0.7
            Peso del modelo (0.0 a 1.0)
            - 1.0 = 100% modelo
            - 0.5 = 50% modelo, 50% mercado
            - 0.0 = 100% mercado
        """
        if not 0.0 <= alpha <= 1.0:
            raise ValueError(f"alpha debe estar entre 0 y 1, recibido: {alpha}")
        self.alpha = alpha
    
    def blend(self, probs_model, probs_market):
        """
        Combina probabilidades del modelo y mercado.
        
        Parameters:
        -----------
        probs_model : pd.DataFrame
            Probabilidades del modelo ['pH', 'pD', 'pA']
        probs_market : pd.DataFrame
            Probabilidades del mercado ['pH_mkt', 'pD_mkt', 'pA_mkt']
        
        Returns:
        --------
        blended : pd.DataFrame
            Probabilidades combinadas y normalizadas
        """
        blended = {}
        
        for outcome in ['H', 'D', 'A']:
            p_model = probs_model[f'p{outcome}'].values
            p_market = probs_market[f'p{outcome}_mkt'].values
            
            # Blend: alpha*modelo + (1-alpha)*mercado
            blended[f'p{outcome}'] = self.alpha * p_model + (1 - self.alpha) * p_market
        
        # Convertir a DataFrame
        blended_df = pd.DataFrame(blended)
        
        # Renormalizar
        row_sums = blended_df.sum(axis=1)
        for col in blended_df.columns:
            blended_df[col] = blended_df[col] / row_sums
        
        return blended_df


def evaluate_calibration(y_true, probs_df, n_bins=10):
    """
    Evalúa la calidad de la calibración de probabilidades.
    
    Retorna métricas como Brier Score y reliability curve.
    
    Parameters:
    -----------
    y_true : array-like
        Outcomes reales (0=Home, 1=Draw, 2=Away)
    probs_df : pd.DataFrame
        Probabilidades predichas ['pH', 'pD', 'pA']
    n_bins : int
        Número de bins para reliability curve
    
    Returns:
    --------
    metrics : dict
        Diccionario con métricas de calibración
    """
    from sklearn.metrics import brier_score_loss
    
    y_true = np.array(y_true)
    metrics = {}
    
    # Calcular Brier score para cada outcome
    for idx, outcome in enumerate(['H', 'D', 'A']):
        y_binary = (y_true == idx).astype(float)
        p_pred = probs_df[f'p{outcome}'].values
        
        brier = brier_score_loss(y_binary, p_pred)
        metrics[f'brier_{outcome}'] = brier
    
    # Brier score promedio
    metrics['brier_mean'] = np.mean([metrics[f'brier_{k}'] for k in ['H', 'D', 'A']])
    
    return metrics


if __name__ == "__main__":
    # Ejemplo de uso
    print("Módulo de calibración cargado correctamente.")
    print("\nEjemplo de uso:")
    print("""
    from src.models.calibration import ProbabilityCalibrator
    
    # Entrenar
    calibrator = ProbabilityCalibrator()
    calibrator.fit(y_train, probs_train)
    
    # Aplicar
    probs_calibrated = calibrator.transform(probs_test)
    """)
