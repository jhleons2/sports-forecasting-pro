#!/usr/bin/env python3
"""
Sistema de Alertas Simplificado para Sports Forecasting PRO
Genera alertas basadas en las predicciones del modelo Dixon-Coles
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
from pathlib import Path

@dataclass
class SimpleAlert:
    """Alerta simplificada de valor"""
    match_id: str
    home_team: str
    away_team: str
    market: str
    selection: str
    model_prob: float
    edge: float
    urgency: str
    recommendation: str
    expires_at: datetime

class SimpleAlertManager:
    """Gestor de alertas simplificado"""
    
    def __init__(self, alerts_file: str = "data/alerts/simple_alerts.json"):
        self.alerts_file = Path(alerts_file)
        self.alerts_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Umbrales más bajos para generar más alertas
        self.alert_thresholds = {
            'CRITICAL': 0.15,    # Probabilidad > 15% por encima de mercado
            'HIGH': 0.10,        # Probabilidad > 10% por encima de mercado
            'MEDIUM': 0.05,      # Probabilidad > 5% por encima de mercado
            'LOW': 0.02          # Probabilidad > 2% por encima de mercado
        }
        
        # Tiempo de expiración
        self.expiration_times = {
            'CRITICAL': timedelta(hours=2),
            'HIGH': timedelta(hours=6),
            'MEDIUM': timedelta(hours=12),
            'LOW': timedelta(hours=24)
        }
    
    def generate_alerts_from_predictions(self, matches_with_predictions: List[Dict]) -> List[SimpleAlert]:
        """Genera alertas basadas en predicciones del modelo"""
        alerts = []
        
        for match_data in matches_with_predictions:
            match_alerts = self._analyze_match_predictions(match_data)
            alerts.extend(match_alerts)
        
        # Ordenar por edge
        alerts.sort(key=lambda x: x.edge, reverse=True)
        return alerts
    
    def _analyze_match_predictions(self, match_data: Dict) -> List[SimpleAlert]:
        """Analiza las predicciones de un partido para generar alertas"""
        alerts = []
        
        try:
            predictions = match_data.get('analysis', {})
            partido_data = match_data.get('match_data', match_data)
            
            if not predictions or not partido_data:
                return alerts
            
            match_id = f"{partido_data['HomeTeam']}_vs_{partido_data['AwayTeam']}_{partido_data.get('Date', '')}"
            
            # Analizar mercado 1X2
            if 'probabilities' in predictions:
                probs = predictions['probabilities']
                
                # Home Win
                if probs.get('home_win', 0) > 0.45:  # Probabilidad moderada-alta de victoria local
                    edge = probs['home_win'] - 0.33  # Edge sobre mercado equilibrado (1/3)
                    if edge >= self.alert_thresholds['LOW']:
                        urgency = self._determine_urgency(edge)
                        alert = SimpleAlert(
                            match_id=match_id,
                            home_team=partido_data['HomeTeam'],
                            away_team=partido_data['AwayTeam'],
                            market='1X2',
                            selection='1',
                            model_prob=probs['home_win'],
                            edge=edge,
                            urgency=urgency,
                            recommendation=f"Fuerte favorito local: {partido_data['HomeTeam']} ({probs['home_win']:.1%})",
                            expires_at=datetime.now() + self.expiration_times[urgency]
                        )
                        alerts.append(alert)
                
                # Away Win
                if probs.get('away_win', 0) > 0.45:  # Probabilidad moderada-alta de victoria visitante
                    edge = probs['away_win'] - 0.33
                    if edge >= self.alert_thresholds['LOW']:
                        urgency = self._determine_urgency(edge)
                        alert = SimpleAlert(
                            match_id=match_id,
                            home_team=partido_data['HomeTeam'],
                            away_team=partido_data['AwayTeam'],
                            market='1X2',
                            selection='2',
                            model_prob=probs['away_win'],
                            edge=edge,
                            urgency=urgency,
                            recommendation=f"Fuerte favorito visitante: {partido_data['AwayTeam']} ({probs['away_win']:.1%})",
                            expires_at=datetime.now() + self.expiration_times[urgency]
                        )
                        alerts.append(alert)
                
                # Draw
                if probs.get('draw', 0) > 0.25:  # Probabilidad moderada de empate
                    edge = probs['draw'] - 0.25  # Empate menos común
                    if edge >= self.alert_thresholds['LOW']:
                        urgency = self._determine_urgency(edge)
                        alert = SimpleAlert(
                            match_id=match_id,
                            home_team=partido_data['HomeTeam'],
                            away_team=partido_data['AwayTeam'],
                            market='1X2',
                            selection='X',
                            model_prob=probs['draw'],
                            edge=edge,
                            urgency=urgency,
                            recommendation=f"Alta probabilidad de empate ({probs['draw']:.1%})",
                            expires_at=datetime.now() + self.expiration_times[urgency]
                        )
                        alerts.append(alert)
            
            # Analizar Over/Under 2.5
            if 'over_under' in predictions:
                ou = predictions['over_under']
                
                if ou.get('over_2_5', 0) > 0.55:  # Probabilidad moderada Over 2.5
                    edge = ou['over_2_5'] - 0.45
                    if edge >= self.alert_thresholds['LOW']:
                        urgency = self._determine_urgency(edge)
                        alert = SimpleAlert(
                            match_id=match_id,
                            home_team=partido_data['HomeTeam'],
                            away_team=partido_data['AwayTeam'],
                            market='Over/Under',
                            selection='Over 2.5',
                            model_prob=ou['over_2_5'],
                            edge=edge,
                            urgency=urgency,
                            recommendation=f"Alta probabilidad Over 2.5 ({ou['over_2_5']:.1%})",
                            expires_at=datetime.now() + self.expiration_times[urgency]
                        )
                        alerts.append(alert)
                
                if ou.get('under_2_5', 0) > 0.7:  # Alta probabilidad Under 2.5
                    edge = ou['under_2_5'] - 0.5
                    if edge >= self.alert_thresholds['LOW']:
                        urgency = self._determine_urgency(edge)
                        alert = SimpleAlert(
                            match_id=match_id,
                            home_team=partido_data['HomeTeam'],
                            away_team=partido_data['AwayTeam'],
                            market='Over/Under',
                            selection='Under 2.5',
                            model_prob=ou['under_2_5'],
                            edge=edge,
                            urgency=urgency,
                            recommendation=f"Alta probabilidad Under 2.5 ({ou['under_2_5']:.1%})",
                            expires_at=datetime.now() + self.expiration_times[urgency]
                        )
                        alerts.append(alert)
        
        except Exception as e:
            print(f"Error analizando partido para alertas: {e}")
        
        return alerts
    
    def _determine_urgency(self, edge: float) -> str:
        """Determina la urgencia basada en el edge"""
        if edge >= self.alert_thresholds['CRITICAL']:
            return 'CRITICAL'
        elif edge >= self.alert_thresholds['HIGH']:
            return 'HIGH'
        elif edge >= self.alert_thresholds['MEDIUM']:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def save_alerts(self, alerts: List[SimpleAlert]) -> None:
        """Guarda las alertas en un archivo JSON"""
        alerts_data = []
        
        for alert in alerts:
            alert_dict = {
                'match_id': alert.match_id,
                'home_team': alert.home_team,
                'away_team': alert.away_team,
                'market': alert.market,
                'selection': alert.selection,
                'model_prob': alert.model_prob,
                'edge': alert.edge,
                'urgency': alert.urgency,
                'recommendation': alert.recommendation,
                'expires_at': alert.expires_at.isoformat(),
                'created_at': datetime.now().isoformat()
            }
            alerts_data.append(alert_dict)
        
        with open(self.alerts_file, 'w', encoding='utf-8') as f:
            json.dump(alerts_data, f, indent=2, ensure_ascii=False)
    
    def get_active_alerts(self) -> List[SimpleAlert]:
        """Obtiene alertas activas (no expiradas)"""
        if not self.alerts_file.exists():
            return []
        
        try:
            with open(self.alerts_file, 'r', encoding='utf-8') as f:
                alerts_data = json.load(f)
            
            active_alerts = []
            now = datetime.now()
            
            for alert_data in alerts_data:
                expires_at = datetime.fromisoformat(alert_data['expires_at'])
                if expires_at > now:
                    alert = SimpleAlert(
                        match_id=alert_data['match_id'],
                        home_team=alert_data['home_team'],
                        away_team=alert_data['away_team'],
                        market=alert_data['market'],
                        selection=alert_data['selection'],
                        model_prob=alert_data['model_prob'],
                        edge=alert_data['edge'],
                        urgency=alert_data['urgency'],
                        recommendation=alert_data['recommendation'],
                        expires_at=expires_at
                    )
                    active_alerts.append(alert)
            
            return active_alerts
        
        except Exception as e:
            print(f"Error cargando alertas: {e}")
            return []
    
    def clean_expired_alerts(self) -> int:
        """Limpia alertas expiradas y retorna el número eliminado"""
        alerts = self.get_active_alerts()
        self.save_alerts(alerts)
        
        if self.alerts_file.exists():
            with open(self.alerts_file, 'r', encoding='utf-8') as f:
                all_alerts = json.load(f)
            return len(all_alerts) - len(alerts)
        return 0
    
    def generate_alert_summary(self) -> Dict:
        """Genera un resumen de las alertas activas"""
        alerts = self.get_active_alerts()
        
        if not alerts:
            return {
                'total_alerts': 0,
                'critical_alerts': 0,
                'high_alerts': 0,
                'medium_alerts': 0,
                'low_alerts': 0,
                'best_edge': 0,
                'avg_edge': 0
            }
        
        urgency_counts = {
            'CRITICAL': len([a for a in alerts if a.urgency == 'CRITICAL']),
            'HIGH': len([a for a in alerts if a.urgency == 'HIGH']),
            'MEDIUM': len([a for a in alerts if a.urgency == 'MEDIUM']),
            'LOW': len([a for a in alerts if a.urgency == 'LOW'])
        }
        
        edges = [alert.edge for alert in alerts]
        
        return {
            'total_alerts': len(alerts),
            'critical_alerts': urgency_counts['CRITICAL'],
            'high_alerts': urgency_counts['HIGH'],
            'medium_alerts': urgency_counts['MEDIUM'],
            'low_alerts': urgency_counts['LOW'],
            'best_edge': max(edges) if edges else 0,
            'avg_edge': sum(edges) / len(edges) if edges else 0
        }
    
    def get_alerts_by_urgency(self, urgency: str) -> List[SimpleAlert]:
        """Obtiene alertas por nivel de urgencia"""
        alerts = self.get_active_alerts()
        return [alert for alert in alerts if alert.urgency == urgency]


if __name__ == "__main__":
    # Ejemplo de uso
    alert_manager = SimpleAlertManager()
    print("Sistema de alertas simplificado inicializado correctamente")
