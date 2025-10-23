"""
Modelo XGBoost para predicción de resultados 1X2

Dixon-Coles no funciona para 1X2, pero XGBoost sí puede hacerlo
al capturar patrones no-lineales y usar features adicionales.
"""

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.preprocessing import StandardScaler


class XGBoost1X2Classifier:
    """
    Clasificador XGBoost para predicción 1X2.
    
    Usa features avanzados que Dixon-Coles no puede capturar:
    - ELO ratings
    - Forma reciente (últimos 5 partidos)
    - Home/Away strength
    - Head-to-head histórico
    - Gol difference
    """
    
    def __init__(self, n_estimators=100, max_depth=5, learning_rate=0.1):
        """
        Inicializa el modelo XGBoost.
        
        Parameters:
        -----------
        n_estimators : int
            Número de árboles
        max_depth : int
            Profundidad máxima de árboles
        learning_rate : float
            Tasa de aprendizaje
        """
        self.model = xgb.XGBClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            learning_rate=learning_rate,
            objective='multi:softprob',
            num_class=3,
            random_state=42,
            use_label_encoder=False,
            eval_metric='mlogloss'
        )
        self.scaler = StandardScaler()
        self.is_fitted = False
    
    def _create_features(self, df):
        """
        Crea features para el modelo.
        
        Parameters:
        -----------
        df : pd.DataFrame
            DataFrame con datos de partidos
        
        Returns:
        --------
        X : np.ndarray
            Matriz de features
        """
        features = []
        
        # 1. ELO features
        if 'EloHome' in df.columns and 'EloAway' in df.columns:
            features.append(df['EloHome'].values)
            features.append(df['EloAway'].values)
            features.append((df['EloHome'] - df['EloAway']).values)
        
        # 2. Form features (rolling últimos 5)
        form_cols = [c for c in df.columns if 'roll5' in c.lower()]
        for col in form_cols:
            features.append(df[col].fillna(0).values)
        
        # 3. Home advantage implícito
        if 'EloHome' in df.columns:
            # Asumimos que hay ventaja de local en el ELO
            pass
        
        # 4. Goal difference reciente
        if 'Home_GD_roll5' in df.columns and 'Away_GD_roll5' in df.columns:
            features.append((df['Home_GD_roll5'] - df['Away_GD_roll5']).fillna(0).values)
        
        # 5. Odds como feature (refleja opinión del mercado)
        if 'B365H' in df.columns:
            # Convertir odds a probabilidades implícitas
            prob_h = 1.0 / df['B365H'].values
            prob_d = 1.0 / df['B365D'].values
            prob_a = 1.0 / df['B365A'].values
            
            # Normalizar (quitar overround)
            total = prob_h + prob_d + prob_a
            features.append(prob_h / total)
            features.append(prob_d / total)
            features.append(prob_a / total)
        
        # Combinar todos los features
        X = np.column_stack(features) if features else np.zeros((len(df), 1))
        
        return X
    
    def fit(self, df):
        """
        Entrena el modelo XGBoost.
        
        Parameters:
        -----------
        df : pd.DataFrame
            DataFrame con datos de entrenamiento
            Debe contener columna 'y' con outcomes (0=H, 1=D, 2=A)
        
        Returns:
        --------
        self : XGBoost1X2Classifier
        """
        X = self._create_features(df)
        y = df['y'].values
        
        # Escalar features
        X_scaled = self.scaler.fit_transform(X)
        
        # Entrenar modelo
        self.model.fit(X_scaled, y, verbose=False)
        
        self.is_fitted = True
        return self
    
    def predict_proba(self, df):
        """
        Predice probabilidades 1X2.
        
        Parameters:
        -----------
        df : pd.DataFrame
            DataFrame con datos de partidos
        
        Returns:
        --------
        probs : pd.DataFrame
            DataFrame con columnas ['pH', 'pD', 'pA']
        """
        if not self.is_fitted:
            raise ValueError("Modelo no entrenado. Llamar a fit() primero.")
        
        X = self._create_features(df)
        X_scaled = self.scaler.transform(X)
        
        # Predecir probabilidades
        probs = self.model.predict_proba(X_scaled)
        
        # Convertir a DataFrame
        probs_df = pd.DataFrame(probs, columns=['pH', 'pD', 'pA'])
        
        return probs_df
    
    def feature_importance(self):
        """
        Retorna la importancia de features.
        
        Returns:
        --------
        importance : dict
            Diccionario con importancias
        """
        if not self.is_fitted:
            raise ValueError("Modelo no entrenado.")
        
        importance = self.model.feature_importances_
        return importance


class EnsemblePredictor:
    """
    Ensemble de Dixon-Coles y XGBoost.
    
    Combina las fortalezas de ambos modelos:
    - Dixon-Coles: Bueno para distribución de goles
    - XGBoost: Bueno para patrones complejos
    """
    
    def __init__(self, dixon_coles, xgb_model, alpha=0.5):
        """
        Inicializa el ensemble.
        
        Parameters:
        -----------
        dixon_coles : DixonColes
            Modelo Dixon-Coles entrenado
        xgb_model : XGBoost1X2Classifier
            Modelo XGBoost entrenado
        alpha : float
            Peso de Dixon-Coles (0.0 = solo XGBoost, 1.0 = solo DC)
        """
        self.dc = dixon_coles
        self.xgb = xgb_model
        self.alpha = alpha
    
    def predict_proba(self, df):
        """
        Predice probabilidades combinando ambos modelos.
        
        Parameters:
        -----------
        df : pd.DataFrame
            DataFrame con datos de partidos
        
        Returns:
        --------
        probs : pd.DataFrame
            Probabilidades combinadas ['pH', 'pD', 'pA']
        """
        # Predicciones de cada modelo
        probs_dc = self.dc.predict_1x2(df)
        probs_xgb = self.xgb.predict_proba(df)
        
        # Ensemble ponderado
        probs_combined = self.alpha * probs_dc + (1 - self.alpha) * probs_xgb
        
        # Renormalizar
        row_sums = probs_combined.sum(axis=1)
        for col in probs_combined.columns:
            probs_combined[col] = probs_combined[col] / row_sums
        
        return probs_combined


if __name__ == "__main__":
    print("Módulo XGBoost para 1X2 cargado correctamente.")
    print("\nEjemplo de uso:")
    print("""
    from src.models.xgboost_classifier import XGBoost1X2Classifier
    
    # Entrenar
    xgb_model = XGBoost1X2Classifier()
    xgb_model.fit(train_data)
    
    # Predecir
    probs = xgb_model.predict_proba(test_data)
    """)

