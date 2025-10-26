"""
REGLAS DINÁMICAS - Cálculo en Tiempo Real
==========================================

Calcula las 5 reglas DINÁMICAMENTE desde HOY para partidos futuros:

1. Últimos 8 partidos total (misma liga) - HASTA HOY
2. Últimos 5 de local (misma liga) - HASTA HOY
3. Últimos 5 de visitante (misma liga) - HASTA HOY
4. 5 entre sí (H2H) - HASTA HOY
5. Bajas de jugadores - AL MOMENTO

Importante: Se calcula desde la fecha ACTUAL, no histórica.
"""

import pandas as pd
import numpy as np
from datetime import datetime, date
from typing import Dict, Optional


def calcular_ultimos_8_liga(df: pd.DataFrame, equipo: str, liga: str, hasta_fecha: Optional[date] = None) -> Dict:
    """
    Calcula estadísticas de los últimos 5 partidos con PESO EXPONENCIAL por recencia.
    
    MEJORA: Reducido de 8 a 5 partidos y con peso decreciente (más reciente = más peso)
    
    Parameters:
    -----------
    df : pd.DataFrame
        Dataset histórico completo
    equipo : str
        Nombre del equipo
    liga : str
        Código de la liga (E0, SP1, etc.)
    hasta_fecha : date, optional
        Fecha límite (default: fecha máxima del dataset)
        
    Returns:
    --------
    dict : Estadísticas de últimos 5 partidos con peso temporal
    """
    if hasta_fecha is None:
        hasta_fecha = pd.to_datetime(df['Date']).max().date()
    
    # Filtrar partidos de la liga hasta la fecha
    df_filtrado = df[
        (df['League'] == liga) &
        (pd.to_datetime(df['Date']).dt.date <= hasta_fecha)
    ].copy()
    
    # Buscar partidos del equipo (como local O visitante)
    partidos_home = df_filtrado[df_filtrado['HomeTeam'] == equipo]
    partidos_away = df_filtrado[df_filtrado['AwayTeam'] == equipo]
    
    # Combinar y ordenar por fecha DESCENDENTE (más reciente primero)
    todos_partidos = pd.concat([partidos_home, partidos_away]).sort_values('Date', ascending=False)
    
    # MEJORA: Solo últimos 5 partidos (antes eran 8)
    ultimos_5 = todos_partidos.head(5)
    
    if len(ultimos_5) == 0:
        return {'gf': 0, 'ga': 0, 'gd': 0, 'pts': 0, 'partidos': 0, 'efectividad': 0}
    
    # PESOS EXPONENCIALES por recencia (más reciente = más peso)
    # Partido más reciente: peso 1.0
    # Segundo más reciente: peso 0.8
    # Tercero: peso 0.6
    # Cuarto: peso 0.4
    # Quinto: peso 0.2
    pesos = [1.0, 0.8, 0.6, 0.4, 0.2]
    
    # Calcular estadísticas CON PESOS
    gf = 0
    ga = 0
    pts = 0
    peso_total = 0
    
    for idx, (_, partido) in enumerate(ultimos_5.iterrows()):
        peso = pesos[idx] if idx < len(pesos) else 0.2
        
        if partido['HomeTeam'] == equipo:
            # Como local
            gf += partido['FTHG'] * peso
            ga += partido['FTAG'] * peso
            if partido['FTHG'] > partido['FTAG']:
                pts += 3 * peso
            elif partido['FTHG'] == partido['FTAG']:
                pts += 1 * peso
        else:
            # Como visitante
            gf += partido['FTAG'] * peso
            ga += partido['FTHG'] * peso
            if partido['FTAG'] > partido['FTHG']:
                pts += 3 * peso
            elif partido['FTAG'] == partido['FTHG']:
                pts += 1 * peso
        
        peso_total += peso
    
    # Normalizar por peso total
    if peso_total > 0:
        gf = gf / peso_total
        ga = ga / peso_total
        pts = pts / peso_total
    
    return {
        'gf': gf,
        'ga': ga,
        'gd': gf - ga,
        'pts': pts,
        'partidos': len(ultimos_5),
        'efectividad': (pts / 3) * 100 if len(ultimos_5) > 0 else 0
    }


def calcular_ultimos_5_local(df: pd.DataFrame, equipo: str, liga: str, hasta_fecha: Optional[date] = None) -> Dict:
    """
    Calcula estadísticas de los últimos 5 partidos como LOCAL en una liga.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Dataset histórico completo
    equipo : str
        Nombre del equipo
    liga : str
        Código de la liga
    hasta_fecha : date, optional
        Fecha límite (default: HOY)
        
    Returns:
    --------
    dict : Estadísticas de últimos 5 como local
    """
    if hasta_fecha is None:
        hasta_fecha = datetime.now().date()
    
    # Filtrar SOLO partidos como local
    partidos_local = df[
        (df['League'] == liga) &
        (df['HomeTeam'] == equipo) &
        (pd.to_datetime(df['Date']).dt.date <= hasta_fecha)
    ].sort_values('Date', ascending=False).head(5)
    
    if len(partidos_local) == 0:
        return {'gf': 0, 'ga': 0, 'gd': 0, 'pts': 0, 'partidos': 0, 'win_rate': 0}
    
    gf = partidos_local['FTHG'].sum()
    ga = partidos_local['FTAG'].sum()
    
    pts = 0
    wins = 0
    for _, p in partidos_local.iterrows():
        if p['FTHG'] > p['FTAG']:
            pts += 3
            wins += 1
        elif p['FTHG'] == p['FTAG']:
            pts += 1
    
    return {
        'gf': gf,
        'ga': ga,
        'gd': gf - ga,
        'pts': pts,
        'partidos': len(partidos_local),
        'win_rate': (wins / len(partidos_local)) * 100 if len(partidos_local) > 0 else 0
    }


def calcular_ultimos_5_visitante(df: pd.DataFrame, equipo: str, liga: str, hasta_fecha: Optional[date] = None) -> Dict:
    """
    Calcula estadísticas de los últimos 5 partidos como VISITANTE en una liga.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Dataset histórico completo
    equipo : str
        Nombre del equipo
    liga : str
        Código de la liga
    hasta_fecha : date, optional
        Fecha límite (default: HOY)
        
    Returns:
    --------
    dict : Estadísticas de últimos 5 como visitante
    """
    if hasta_fecha is None:
        hasta_fecha = datetime.now().date()
    
    # Filtrar SOLO partidos como visitante
    partidos_visitante = df[
        (df['League'] == liga) &
        (df['AwayTeam'] == equipo) &
        (pd.to_datetime(df['Date']).dt.date <= hasta_fecha)
    ].sort_values('Date', ascending=False).head(5)
    
    if len(partidos_visitante) == 0:
        return {'gf': 0, 'ga': 0, 'gd': 0, 'pts': 0, 'partidos': 0, 'win_rate': 0}
    
    gf = partidos_visitante['FTAG'].sum()
    ga = partidos_visitante['FTHG'].sum()
    
    pts = 0
    wins = 0
    for _, p in partidos_visitante.iterrows():
        if p['FTAG'] > p['FTHG']:
            pts += 3
            wins += 1
        elif p['FTAG'] == p['FTHG']:
            pts += 1
    
    return {
        'gf': gf,
        'ga': ga,
        'gd': gf - ga,
        'pts': pts,
        'partidos': len(partidos_visitante),
        'win_rate': (wins / len(partidos_visitante)) * 100 if len(partidos_visitante) > 0 else 0
    }


def calcular_h2h_ultimos_5(df: pd.DataFrame, equipo_home: str, equipo_away: str, hasta_fecha: Optional[date] = None) -> Dict:
    """
    Calcula estadísticas de los últimos 5 enfrentamientos directos.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Dataset histórico completo
    equipo_home : str
        Equipo local
    equipo_away : str
        Equipo visitante
    hasta_fecha : date, optional
        Fecha límite (default: HOY)
        
    Returns:
    --------
    dict : Estadísticas de H2H
    """
    if hasta_fecha is None:
        hasta_fecha = datetime.now().date()
    
    # Buscar enfrentamientos directos (cualquier orden)
    h2h = df[
        (pd.to_datetime(df['Date']).dt.date <= hasta_fecha) &
        (
            ((df['HomeTeam'] == equipo_home) & (df['AwayTeam'] == equipo_away)) |
            ((df['HomeTeam'] == equipo_away) & (df['AwayTeam'] == equipo_home))
        )
    ].sort_values('Date', ascending=False).head(5)
    
    if len(h2h) == 0:
        return {
            'home_wins': 0,
            'draws': 0,
            'away_wins': 0,
            'home_goals_avg': 0.0,
            'away_goals_avg': 0.0,
            'total_goals_avg': 0.0,
            'partidos': 0
        }
    
    home_wins = 0
    draws = 0
    away_wins = 0
    home_goals = []
    away_goals = []
    
    for _, partido in h2h.iterrows():
        if partido['HomeTeam'] == equipo_home:
            # Mismo orden
            if partido['FTHG'] > partido['FTAG']:
                home_wins += 1
            elif partido['FTHG'] == partido['FTAG']:
                draws += 1
            else:
                away_wins += 1
            home_goals.append(partido['FTHG'])
            away_goals.append(partido['FTAG'])
        else:
            # Orden invertido
            if partido['FTAG'] > partido['FTHG']:
                home_wins += 1
            elif partido['FTHG'] == partido['FTAG']:
                draws += 1
            else:
                away_wins += 1
            home_goals.append(partido['FTAG'])
            away_goals.append(partido['FTHG'])
    
    return {
        'home_wins': home_wins,
        'draws': draws,
        'away_wins': away_wins,
        'home_goals_avg': np.mean(home_goals) if home_goals else 0.0,
        'away_goals_avg': np.mean(away_goals) if away_goals else 0.0,
        'total_goals_avg': (np.mean(home_goals) if home_goals else 0.0) + (np.mean(away_goals) if away_goals else 0.0),
        'partidos': len(h2h),
        'dominancia': (home_wins - away_wins) / len(h2h) if len(h2h) > 0 else 0.0
    }


def calcular_reglas_dinamicas(df: pd.DataFrame, 
                               equipo_home: str, 
                               equipo_away: str, 
                               liga: str,
                               fecha_partido: Optional[date] = None) -> Dict:
    """
    Calcula TODAS las reglas dinámicamente para un partido futuro.
    
    Esta es la función PRINCIPAL que usa el dashboard.
    Calcula TODO desde la fecha actual (o fecha del partido).
    
    Parameters:
    -----------
    df : pd.DataFrame
        Dataset histórico completo
    equipo_home : str
        Equipo local
    equipo_away : str
        Equipo visitante
    liga : str
        Código de la liga
    fecha_partido : date, optional
        Fecha del partido (default: HOY para predicciones futuras)
        
    Returns:
    --------
    dict : Todas las reglas calculadas dinámicamente
    """
    # Para partidos futuros, calculamos HASTA HOY
    # Para partidos históricos, calculamos hasta el día del partido
    if fecha_partido is None or fecha_partido > datetime.now().date():
        hasta_fecha = datetime.now().date()
    else:
        hasta_fecha = fecha_partido
    
    print(f"\nCalculando reglas DINAMICAMENTE:")
    print(f"   Equipo home: {equipo_home}")
    print(f"   Equipo away: {equipo_away}")
    print(f"   Liga: {liga}")
    print(f"   Hasta fecha: {hasta_fecha}")
    
    # REGLA 1: Últimos 8 total
    home_8 = calcular_ultimos_8_liga(df, equipo_home, liga, hasta_fecha)
    away_8 = calcular_ultimos_8_liga(df, equipo_away, liga, hasta_fecha)
    
    # REGLA 2: Últimos 5 local
    home_5_local = calcular_ultimos_5_local(df, equipo_home, liga, hasta_fecha)
    
    # REGLA 3: Últimos 5 visitante
    away_5_visitante = calcular_ultimos_5_visitante(df, equipo_away, liga, hasta_fecha)
    
    # REGLA 4: H2H últimos 5
    h2h = calcular_h2h_ultimos_5(df, equipo_home, equipo_away, hasta_fecha)
    
    # REGLA 5: Bajas (Integrado con FPL API)
    try:
        from src.utils.sistema_lesiones_fpl import integrar_lesiones_fpl_con_reglas
        lesiones_data = integrar_lesiones_fpl_con_reglas(equipo_home, equipo_away)
        
        bajas = {
            'home_bajas': lesiones_data['home']['regla5']['total_lesiones'],
            'away_bajas': lesiones_data['away']['regla5']['total_lesiones'],
            'home_suspendidos': 0,  # FPL no distingue suspensiones
            'away_suspendidos': 0,
            'home_impacto': lesiones_data['home']['regla5']['impacto_estimado'],
            'away_impacto': lesiones_data['away']['regla5']['impacto_estimado'],
            'home_lesiones_detalle': lesiones_data['home']['lesiones_detalle'],
            'away_lesiones_detalle': lesiones_data['away']['lesiones_detalle']
        }
    except Exception as e:
        print(f"   ADVERTENCIA: Error cargando lesiones FPL: {e}")
        # Fallback a placeholder
        bajas = {
            'home_bajas': 0,
            'away_bajas': 0,
            'home_suspendidos': 0,
            'away_suspendidos': 0,
            'home_impacto': 0.0,
            'away_impacto': 0.0,
            'home_lesiones_detalle': [],
            'away_lesiones_detalle': []
        }
    
    reglas = {
        'ultimos_8_total': {
            'home': home_8,
            'away': away_8
        },
        'ultimos_5_local': home_5_local,
        'ultimos_5_visitante': away_5_visitante,
        'ultimos_5_h2h': h2h,
        'bajas_jugadores': bajas,
        'fecha_calculo': hasta_fecha.isoformat(),
        'partido': f"{equipo_home} vs {equipo_away}",
        'liga': liga
    }
    
    # Imprimir resumen
    print(f"\nReglas calculadas:")
    print(f"   REGLA 1: {home_8['partidos']} partidos home, {away_8['partidos']} away")
    print(f"   REGLA 2: {home_5_local['partidos']} partidos como local")
    print(f"   REGLA 3: {away_5_visitante['partidos']} partidos como visitante")
    print(f"   REGLA 4: {h2h['partidos']} enfrentamientos H2H")
    print(f"   REGLA 5: {bajas['home_bajas'] + bajas['away_bajas']} bajas totales")
    
    return reglas


def preparar_features_para_prediccion(reglas: Dict) -> Dict:
    """
    Convierte reglas dinámicas en features para el modelo.
    
    Parameters:
    -----------
    reglas : dict
        Reglas calculadas dinámicamente
        
    Returns:
    --------
    dict : Features listos para predicción
    """
    features = {
        # REGLA 1: Últimos 8 total
        'Home_Pts_ultimos8_liga': reglas['ultimos_8_total']['home']['pts'],
        'Home_GD_ultimos8_liga': reglas['ultimos_8_total']['home']['gd'],
        'Home_GF_ultimos8_liga': reglas['ultimos_8_total']['home']['gf'],
        'Home_GA_ultimos8_liga': reglas['ultimos_8_total']['home']['ga'],
        
        'Away_Pts_ultimos8_liga': reglas['ultimos_8_total']['away']['pts'],
        'Away_GD_ultimos8_liga': reglas['ultimos_8_total']['away']['gd'],
        'Away_GF_ultimos8_liga': reglas['ultimos_8_total']['away']['gf'],
        'Away_GA_ultimos8_liga': reglas['ultimos_8_total']['away']['ga'],
        
        # REGLA 2: Últimos 5 local
        'Home_GF_local5_liga': reglas['ultimos_5_local']['gf'],
        'Home_GA_local5_liga': reglas['ultimos_5_local']['ga'],
        'Home_GD_local5_liga': reglas['ultimos_5_local']['gd'],
        
        # REGLA 3: Últimos 5 visitante
        'Away_GF_visitante5_liga': reglas['ultimos_5_visitante']['gf'],
        'Away_GA_visitante5_liga': reglas['ultimos_5_visitante']['ga'],
        'Away_GD_visitante5_liga': reglas['ultimos_5_visitante']['gd'],
        
        # REGLA 4: H2H
        'H2H5_home_wins': reglas['ultimos_5_h2h']['home_wins'],
        'H2H5_away_wins': reglas['ultimos_5_h2h']['away_wins'],
        'H2H5_total_goals_avg': reglas['ultimos_5_h2h']['total_goals_avg'],
        
        # REGLA 5: Bajas
        'Home_jugadores_clave_bajas': reglas['bajas_jugadores']['home_bajas'],
        'Away_jugadores_clave_bajas': reglas['bajas_jugadores']['away_bajas']
    }
    
    return features


def formato_reglas_texto(reglas: Dict) -> str:
    """
    Formatea las reglas en texto legible.
    
    Parameters:
    -----------
    reglas : dict
        Reglas calculadas
        
    Returns:
    --------
    str : Texto formateado
    """
    home_team = reglas['partido'].split(' vs ')[0]
    away_team = reglas['partido'].split(' vs ')[1]
    
    texto = f"""
╔════════════════════════════════════════════════════════════════╗
║  ANÁLISIS DINÁMICO: {reglas['partido']:^42s}  ║
║  Liga: {reglas['liga']:^10s} | Calculado: {reglas['fecha_calculo']:^30s}  ║
╚════════════════════════════════════════════════════════════════╝

📊 REGLA 1: ÚLTIMOS 8 PARTIDOS TOTAL (HASTA HOY - {reglas['liga']})
────────────────────────────────────────────────────────────────
  {home_team}:
    Partidos jugados:  {reglas['ultimos_8_total']['home']['partidos']}
    Goles a favor:     {reglas['ultimos_8_total']['home']['gf']}
    Goles en contra:   {reglas['ultimos_8_total']['home']['ga']}
    Diferencia:        {reglas['ultimos_8_total']['home']['gd']:+d}
    Puntos:            {reglas['ultimos_8_total']['home']['pts']}/{reglas['ultimos_8_total']['home']['partidos']*3}
    Efectividad:       {reglas['ultimos_8_total']['home']['efectividad']:.1f}%

  {away_team}:
    Partidos jugados:  {reglas['ultimos_8_total']['away']['partidos']}
    Goles a favor:     {reglas['ultimos_8_total']['away']['gf']}
    Goles en contra:   {reglas['ultimos_8_total']['away']['ga']}
    Diferencia:        {reglas['ultimos_8_total']['away']['gd']:+d}
    Puntos:            {reglas['ultimos_8_total']['away']['pts']}/{reglas['ultimos_8_total']['away']['partidos']*3}
    Efectividad:       {reglas['ultimos_8_total']['away']['efectividad']:.1f}%

🏠 REGLA 2: ÚLTIMOS 5 COMO LOCAL (HASTA HOY - {reglas['liga']})
────────────────────────────────────────────────────────────────
  {home_team}:
    Partidos en casa:  {reglas['ultimos_5_local']['partidos']}
    Goles a favor:     {reglas['ultimos_5_local']['gf']}
    Goles en contra:   {reglas['ultimos_5_local']['ga']}
    Diferencia:        {reglas['ultimos_5_local']['gd']:+d}
    Puntos:            {reglas['ultimos_5_local']['pts']}/{reglas['ultimos_5_local']['partidos']*3}
    Win rate:          {reglas['ultimos_5_local']['win_rate']:.1f}%

✈️  REGLA 3: ÚLTIMOS 5 COMO VISITANTE (HASTA HOY - {reglas['liga']})
────────────────────────────────────────────────────────────────
  {away_team}:
    Partidos fuera:    {reglas['ultimos_5_visitante']['partidos']}
    Goles a favor:     {reglas['ultimos_5_visitante']['gf']}
    Goles en contra:   {reglas['ultimos_5_visitante']['ga']}
    Diferencia:        {reglas['ultimos_5_visitante']['gd']:+d}
    Puntos:            {reglas['ultimos_5_visitante']['pts']}/{reglas['ultimos_5_visitante']['partidos']*3}
    Win rate:          {reglas['ultimos_5_visitante']['win_rate']:.1f}%

🔄 REGLA 4: ÚLTIMOS 5 H2H (HASTA HOY)
────────────────────────────────────────────────────────────────
  Partidos H2H:      {reglas['ultimos_5_h2h']['partidos']}
  Victorias {home_team}: {reglas['ultimos_5_h2h']['home_wins']}
  Empates:           {reglas['ultimos_5_h2h']['draws']}
  Victorias {away_team}: {reglas['ultimos_5_h2h']['away_wins']}
  
  Goles promedio:
    {home_team}:     {reglas['ultimos_5_h2h']['home_goals_avg']:.2f}
    {away_team}:     {reglas['ultimos_5_h2h']['away_goals_avg']:.2f}
    Total:             {reglas['ultimos_5_h2h']['total_goals_avg']:.2f}
  
  Dominancia:        {reglas['ultimos_5_h2h']['dominancia']:+.2f} (-1=away, +1=home)

⚠️  REGLA 5: BAJAS DE JUGADORES (AL MOMENTO)
────────────────────────────────────────────────────────────────
  {home_team}:
    Jugadores clave bajas:  {reglas['bajas_jugadores']['home_bajas']}
    Suspendidos:            {reglas['bajas_jugadores']['home_suspendidos']}

  {away_team}:
    Jugadores clave bajas:  {reglas['bajas_jugadores']['away_bajas']}
    Suspendidos:            {reglas['bajas_jugadores']['away_suspendidos']}

╚════════════════════════════════════════════════════════════════╝

Calculo realizado hasta: {reglas['fecha_calculo']}
Todas las reglas calculadas DINAMICAMENTE desde datos actualizados
"""
    
    return texto


if __name__ == "__main__":
    print("""
    MÓDULO DE REGLAS DINÁMICAS
    ===========================
    
    Calcula las 5 reglas en TIEMPO REAL para partidos futuros.
    
    Uso:
    
    from src.features.reglas_dinamicas import calcular_reglas_dinamicas
    
    # Cargar datos históricos
    df = pd.read_parquet("data/processed/matches.parquet")
    
    # Calcular reglas para partido de mañana
    reglas = calcular_reglas_dinamicas(
        df,
        equipo_home="Arsenal",
        equipo_away="Chelsea",
        liga="E0"
    )
    
    # Las reglas se calculan HASTA HOY (no histórico)
    print(reglas)
    """)

