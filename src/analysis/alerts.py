#!/usr/bin/env python3
"""
Sistema de Alertas Automáticas de Valor
======================================

Genera alertas cuando se detectan oportunidades de valor en las predicciones.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
import os
from pathlib import Path


@dataclass
class ValueAlert:
    """Alerta de valor detectada"""
    match_id: str
    home_team: str
    away_team: str
    market: str
    selection: str
    odds: float
    model_prob: float
    edge: float
    confidence: str
    urgency: str
    timestamp: datetime
    expires_at: datetime
    recommendation: str
    stake_suggestion: float


class AlertManager:
    """
    Gestor de alertas de valor automáticas
    """
    
    def __init__(self, alerts_file: str = "data/alerts/value_alerts.json"):
        self.alerts_file = Path(alerts_file)
        self.alerts_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Umbrales para diferentes tipos de alertas (reducidos para generar más alertas)
        self.alert_thresholds = {
            'CRITICAL': 0.08,    # Edge > 8% - Alerta crítica
            'HIGH': 0.05,        # Edge > 5% - Alerta alta
            'MEDIUM': 0.03,      # Edge > 3% - Alerta media
            'LOW': 0.01          # Edge > 1% - Alerta baja
        }
        
        # Tiempo de expiración por tipo de alerta
        self.expiration_times = {
            'CRITICAL': timedelta(hours=2),
            'HIGH': timedelta(hours=6),
            'MEDIUM': timedelta(hours=12),
            'LOW': timedelta(hours=24)
        }
    
    def generate_alerts(self, matches_with_analysis: List[Dict]) -> List[ValueAlert]:
        """
        Genera alertas para todos los partidos con oportunidades de valor
        
        Args:
            matches_with_analysis: Lista de partidos con análisis completos
            
        Returns:
            List[ValueAlert]: Lista de alertas generadas
        """
        
        alerts = []
        
        for match_data in matches_with_analysis:
            match_alerts = self._analyze_match_for_alerts(match_data)
            alerts.extend(match_alerts)
        
        # Ordenar por urgencia y edge
        alerts.sort(key=lambda x: (x.edge, x.urgency), reverse=True)
        
        return alerts
    
    def _analyze_match_for_alerts(self, match_data: Dict) -> List[ValueAlert]:
        """Analiza un partido específico para generar alertas"""
        
        alerts = []
        analysis = match_data.get('analysis', {})
        
        if not analysis or not hasattr(analysis, 'edge_analysis'):
            return alerts
        
        # Extraer datos del partido (puede venir en match_data directamente o en match_data['match_data'])
        partido_data = match_data.get('match_data', match_data)
        match_id = f"{partido_data['HomeTeam']}_vs_{partido_data['AwayTeam']}_{partido_data.get('Date', '')}"
        
        for edge in analysis.edge_analysis:
            # Solo generar alertas para edges positivos significativos
            if edge.edge >= self.alert_thresholds['LOW']:
                urgency = self._determine_urgency(edge.edge)
                
                # Calcular tiempo de expiración
                expires_at = datetime.now() + self.expiration_times[urgency]
                
                # Generar recomendación
                recommendation = self._generate_recommendation(edge, partido_data)
                
                # Sugerir stake
                stake_suggestion = self._calculate_suggested_stake(edge)
                
                alert = ValueAlert(
                    match_id=match_id,
                    home_team=partido_data['HomeTeam'],
                    away_team=partido_data['AwayTeam'],
                    market=edge.market,
                    selection=edge.selection,
                    odds=edge.odds,
                    model_prob=edge.model_prob,
                    edge=edge.edge,
                    confidence=edge.confidence,
                    urgency=urgency,
                    timestamp=datetime.now(),
                    expires_at=expires_at,
                    recommendation=recommendation,
                    stake_suggestion=stake_suggestion
                )
                
                alerts.append(alert)
        
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
    
    def _generate_recommendation(self, edge, match_data: Dict) -> str:
        """Genera una recomendación específica para la alerta"""
        
        edge_pct = edge.edge * 100
        
        if edge.edge >= 0.10:
            return f"OPORTUNIDAD EXCELENTE: {edge.market} - {edge.selection} con {edge_pct:.1f}% de edge. Apuesta recomendada."
        elif edge.edge >= 0.05:
            return f"BUENA OPORTUNIDAD: {edge.market} - {edge.selection} con {edge_pct:.1f}% de edge. Considerar apuesta."
        else:
            return f"OPORTUNIDAD MODERADA: {edge.market} - {edge.selection} con {edge_pct:.1f}% de edge. Apuesta pequeña."
    
    def _calculate_suggested_stake(self, edge) -> float:
        """Calcula el stake sugerido basado en Kelly"""
        
        # Usar fracción de Kelly conservadora (25% del Kelly completo)
        conservative_kelly = edge.kelly_fraction * 0.25
        
        # Limitar a máximo 5% del bankroll
        max_stake = min(conservative_kelly, 0.05)
        
        return max_stake
    
    def save_alerts(self, alerts: List[ValueAlert]) -> None:
        """Guarda las alertas en un archivo JSON"""
        
        alerts_data = []
        
        for alert in alerts:
            alert_dict = {
                'match_id': alert.match_id,
                'home_team': alert.home_team,
                'away_team': alert.away_team,
                'market': alert.market,
                'selection': alert.selection,
                'odds': alert.odds,
                'model_prob': alert.model_prob,
                'edge': alert.edge,
                'confidence': alert.confidence,
                'urgency': alert.urgency,
                'timestamp': alert.timestamp.isoformat(),
                'expires_at': alert.expires_at.isoformat(),
                'recommendation': alert.recommendation,
                'stake_suggestion': alert.stake_suggestion
            }
            alerts_data.append(alert_dict)
        
        with open(self.alerts_file, 'w', encoding='utf-8') as f:
            json.dump(alerts_data, f, indent=2, ensure_ascii=False)
    
    def load_alerts(self) -> List[ValueAlert]:
        """Carga las alertas desde el archivo JSON"""
        
        if not self.alerts_file.exists():
            return []
        
        try:
            with open(self.alerts_file, 'r', encoding='utf-8') as f:
                alerts_data = json.load(f)
            
            alerts = []
            for alert_dict in alerts_data:
                alert = ValueAlert(
                    match_id=alert_dict['match_id'],
                    home_team=alert_dict['home_team'],
                    away_team=alert_dict['away_team'],
                    market=alert_dict['market'],
                    selection=alert_dict['selection'],
                    odds=alert_dict['odds'],
                    model_prob=alert_dict['model_prob'],
                    edge=alert_dict['edge'],
                    confidence=alert_dict['confidence'],
                    urgency=alert_dict['urgency'],
                    timestamp=datetime.fromisoformat(alert_dict['timestamp']),
                    expires_at=datetime.fromisoformat(alert_dict['expires_at']),
                    recommendation=alert_dict['recommendation'],
                    stake_suggestion=alert_dict['stake_suggestion']
                )
                alerts.append(alert)
            
            return alerts
        
        except Exception as e:
            print(f"Error cargando alertas: {e}")
            return []
    
    def clean_expired_alerts(self) -> int:
        """Elimina alertas expiradas y retorna el número eliminado"""
        
        alerts = self.load_alerts()
        active_alerts = []
        expired_count = 0
        
        for alert in alerts:
            if alert.expires_at > datetime.now():
                active_alerts.append(alert)
            else:
                expired_count += 1
        
        if expired_count > 0:
            self.save_alerts(active_alerts)
        
        return expired_count
    
    def get_active_alerts(self) -> List[ValueAlert]:
        """Obtiene solo las alertas activas (no expiradas)"""
        
        alerts = self.load_alerts()
        return [alert for alert in alerts if alert.expires_at > datetime.now()]
    
    def get_alerts_by_urgency(self, urgency: str = None) -> List[ValueAlert]:
        """Obtiene alertas filtradas por urgencia"""
        
        alerts = self.get_active_alerts()
        
        if urgency:
            return [alert for alert in alerts if alert.urgency == urgency]
        
        return alerts
    
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
                'avg_edge': 0,
                'total_exposure': 0
            }
        
        urgency_counts = {
            'CRITICAL': len([a for a in alerts if a.urgency == 'CRITICAL']),
            'HIGH': len([a for a in alerts if a.urgency == 'HIGH']),
            'MEDIUM': len([a for a in alerts if a.urgency == 'MEDIUM']),
            'LOW': len([a for a in alerts if a.urgency == 'LOW'])
        }
        
        edges = [alert.edge for alert in alerts]
        stakes = [alert.stake_suggestion for alert in alerts]
        
        return {
            'total_alerts': len(alerts),
            'critical_alerts': urgency_counts['CRITICAL'],
            'high_alerts': urgency_counts['HIGH'],
            'medium_alerts': urgency_counts['MEDIUM'],
            'low_alerts': urgency_counts['LOW'],
            'best_edge': max(edges) if edges else 0,
            'avg_edge': np.mean(edges) if edges else 0,
            'total_exposure': sum(stakes) * 100  # Asumiendo bankroll de 100
        }


def generate_daily_alerts() -> Dict:
    """
    Función helper para generar alertas diarias
    """
    
    # Cargar fixtures próximos (esto debería conectarse con el sistema principal)
    try:
        fixtures_df = pd.read_parquet('data/processed/upcoming_fixtures.parquet')
        
        # Aquí se procesarían las predicciones y análisis
        # Por ahora, retornamos un ejemplo
        alert_manager = AlertManager()
        
        # Limpiar alertas expiradas
        expired_count = alert_manager.clean_expired_alerts()
        
        # Generar resumen
        summary = alert_manager.generate_alert_summary()
        
        return {
            'status': 'success',
            'expired_cleaned': expired_count,
            'summary': summary,
            'message': f'Alertas procesadas. {expired_count} alertas expiradas eliminadas.'
        }
        
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Error generando alertas: {e}'
        }


if __name__ == "__main__":
    # Ejemplo de uso
    alert_manager = AlertManager()
    
    # Limpiar alertas expiradas
    expired = alert_manager.clean_expired_alerts()
    print(f"Alertas expiradas eliminadas: {expired}")
    
    # Generar resumen
    summary = alert_manager.generate_alert_summary()
    print(f"Resumen de alertas activas: {summary}")
