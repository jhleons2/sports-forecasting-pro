import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from pathlib import Path
import numpy as np

from scripts.predict_matches import MatchPredictor

REPORTS = Path("reports")
PROC = Path("data/processed")

st.set_page_config(page_title="Sports Forecasting PRO", layout="wide", page_icon="⚽")

st.sidebar.title("🎯 Sports Forecasting PRO")
page = st.sidebar.radio("Navegación", ["📊 Backtesting", "🔮 Predicciones por Partido"])

st.sidebar.header("📂 Dataset")
if (PROC/"matches.parquet").exists():
    dfp = pd.read_parquet(PROC/"matches.parquet")
    st.sidebar.write(f"Partidos: {len(dfp)}")
    st.sidebar.write(f"Desde: {dfp['Date'].min().date()}")
    st.sidebar.write(f"Hasta: {dfp['Date'].max().date()}")

# PÁGINA 1: BACKTESTING
if page == "📊 Backtesting":
    st.title("📊 Backtesting - Resultados Históricos")
    
    if not (REPORTS/"backtest_log.csv").exists():
        st.warning("⚠️ No encuentro backtest_log.csv. Ejecuta el pipeline primero.")
    else:
        log = pd.read_csv(REPORTS/"backtest_log.csv", parse_dates=['date'])
        st.subheader("📈 KPIs Generales")
        c1,c2,c3,c4,c5 = st.columns(5)
        kpi_turn = log['stake'].sum()
        kpi_pnl  = log['pnl'].sum()
        kpi_roi  = (kpi_pnl/kpi_turn) if kpi_turn>0 else 0.0
        kpi_bets = len(log)
        kpi_hr   = (log['result']=='WIN').mean() if len(log)>0 else 0.0
        c1.metric("Turnover", f"{kpi_turn:,.2f}")
        c2.metric("PNL", f"{kpi_pnl:,.2f}", delta=f"{kpi_roi*100:.1f}%")
        c3.metric("ROI", f"{100*kpi_roi:.2f}%")
        c4.metric("Apuestas", f"{kpi_bets}")
        c5.metric("Hit-rate", f"{100*kpi_hr:.2f}%")

        st.subheader("📉 Curva de Equity")
        fig = px.line(log.reset_index(), x=log.index, y="equity", 
                     labels={"x":"Apuesta #","equity":"Equity"})
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("📊 Desglose por Mercado")
        per_market = log.groupby("market", as_index=False).agg(
            turnover=("stake","sum"), pnl=("pnl","sum"), bets=("stake","count"))
        per_market["roi"] = (per_market["pnl"]/per_market["turnover"]*100).round(2)
        st.dataframe(per_market, use_container_width=True)

        st.subheader("🔍 Explorador de Apuestas")
        leagues = ["(todas)"] + sorted(log["league"].dropna().unique().tolist())
        sel_league = st.selectbox("Filtrar por Liga", leagues)
        df_view = log if sel_league=="(todas)" else log[log["league"]==sel_league]
        st.dataframe(df_view.sort_values("date", ascending=False), use_container_width=True)

# PÁGINA 2: PREDICCIONES
elif page == "🔮 Predicciones por Partido":
    st.title("🔮 Predicciones Detalladas por Partido")
    
    @st.cache_resource
    def load_predictor():
        predictor = MatchPredictor()
        with st.spinner("Cargando modelos... (30 segundos)"):
            predictor.load_and_train()
        return predictor
    
    try:
        predictor = load_predictor()
        df_matches = predictor.df_historical
        
        st.subheader("⚽ Selecciona un Partido")
        col1, col2 = st.columns(2)
        
        with col1:
            leagues = sorted(df_matches['League'].dropna().unique())
            selected_league = st.selectbox("Liga", leagues, index=0)
        
        with col2:
            matches_in_league = df_matches[df_matches['League'] == selected_league].tail(50)
            match_options = [f"{row['HomeTeam']} vs {row['AwayTeam']} ({row['Date'].date()})" 
                           for idx, row in matches_in_league.iterrows()]
            selected_match_str = st.selectbox("Partido", match_options)
        
        selected_idx = match_options.index(selected_match_str)
        match_row = matches_in_league.iloc[selected_idx]
        match_data = match_row.to_dict()
        
        with st.spinner("Generando predicción..."):
            predictions = predictor.predict_all(match_data)
        
        st.markdown("---")
        st.header(f"📊 {predictions['match_info']['home_team']} vs {predictions['match_info']['away_team']}")
        
        tab1, tab2, tab3, tab4 = st.tabs(["📈 Resultado", "⚽ Goles", "🎯 Eventos", "📊 Estadísticas"])
        
        with tab1:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(f"🏠 {predictions['match_info']['home_team']}", 
                         f"{predictions['1x2']['pH']*100:.1f}%")
            with col2:
                st.metric("🤝 Empate", f"{predictions['1x2']['pD']*100:.1f}%")
            with col3:
                st.metric(f"✈️ {predictions['match_info']['away_team']}", 
                         f"{predictions['1x2']['pA']*100:.1f}%")
            
            fig_1x2 = go.Figure(data=[
                go.Bar(x=['Home', 'Draw', 'Away'], 
                      y=[predictions['1x2']['pH']*100, predictions['1x2']['pD']*100, predictions['1x2']['pA']*100],
                      marker_color=['lightblue', 'gray', 'lightcoral'])
            ])
            fig_1x2.update_layout(title="Probabilidades 1X2", yaxis_title="Probabilidad %")
            st.plotly_chart(fig_1x2, use_container_width=True)
            
            st.subheader("🎲 Asian Handicap 0.0")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Home Win", f"{predictions['asian_handicap_0']['home']['win']*100:.1f}%")
            with col2:
                st.metric("Away Win", f"{predictions['asian_handicap_0']['away']['win']*100:.1f}%")
        
        with tab2:
            st.subheader("⚽ Goles Esperados (xG)")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(predictions['match_info']['home_team'], f"{predictions['goals']['xG_home']:.2f}")
            with col2:
                st.metric("Total", f"{predictions['goals']['xG_total']:.2f}")
            with col3:
                st.metric(predictions['match_info']['away_team'], f"{predictions['goals']['xG_away']:.2f}")
            
            st.subheader("📊 Over/Under")
            ou_data = pd.DataFrame({
                'Línea': ['1.5', '2.5', '3.5'],
                'Over %': [predictions['over_under_1.5']['pOver']*100,
                          predictions['over_under_2.5']['pOver']*100,
                          predictions['over_under_3.5']['pOver']*100],
                'Under %': [predictions['over_under_1.5']['pUnder']*100,
                           predictions['over_under_2.5']['pUnder']*100,
                           predictions['over_under_3.5']['pUnder']*100]
            })
            
            fig_ou = go.Figure()
            fig_ou.add_trace(go.Bar(name='Over', x=ou_data['Línea'], y=ou_data['Over %'], marker_color='lightgreen'))
            fig_ou.add_trace(go.Bar(name='Under', x=ou_data['Línea'], y=ou_data['Under %'], marker_color='lightcoral'))
            fig_ou.update_layout(title="Probabilidades Over/Under", xaxis_title="Línea", yaxis_title="%", barmode='group')
            st.plotly_chart(fig_ou, use_container_width=True)
            st.dataframe(ou_data, use_container_width=True)
        
        with tab3:
            st.subheader("🎯 Eventos Específicos del Partido")
            
            st.markdown("### 🎯 Corners (Tiros de Esquina)")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(predictions['match_info']['home_team'], f"{predictions['corners']['corners_home']:.1f}")
            with col2:
                st.metric("TOTAL", f"{predictions['corners']['corners_total']:.1f}",
                         delta="Alto" if predictions['corners']['corners_total'] > 10 else "Bajo")
            with col3:
                st.metric(predictions['match_info']['away_team'], f"{predictions['corners']['corners_away']:.1f}")
            
            if predictions['corners']['corners_total'] > 11.5:
                st.success(f"✅ RECOMENDACIÓN: Over 10.5 corners (Esperados: {predictions['corners']['corners_total']:.1f})")
            elif predictions['corners']['corners_total'] < 9:
                st.info(f"💡 RECOMENDACIÓN: Under 10.5 corners (Esperados: {predictions['corners']['corners_total']:.1f})")
            else:
                st.warning("⚠️ Corners cerca de la línea, evaluar odds")
            
            st.markdown("---")
            st.markdown("### 🟨 Tarjetas")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Amarillas", f"{predictions['cards']['yellow_cards']:.1f}")
            with col2:
                st.metric("Rojas", f"{predictions['cards']['red_cards']:.2f}")
            with col3:
                st.metric("TOTAL", f"{predictions['cards']['total_cards']:.1f}")
            
            if predictions['cards']['total_cards'] > 4.5:
                st.success(f"✅ RECOMENDACIÓN: Over 4.5 tarjetas (Esperadas: {predictions['cards']['total_cards']:.1f})")
            elif predictions['cards']['total_cards'] > 3.5:
                st.info(f"💡 CONSIDERAR: Over 3.5 tarjetas (Esperadas: {predictions['cards']['total_cards']:.1f})")
            
            st.markdown("---")
            st.markdown("### ⚽ Tiros")
            col1, col2 = st.columns(2)
            with col1:
                st.metric(f"Tiros {predictions['match_info']['home_team']}", f"{predictions['shots']['shots_home']:.1f}")
                st.metric("A puerta", f"{predictions['shots']['shots_on_target_home']:.1f}")
            with col2:
                st.metric(f"Tiros {predictions['match_info']['away_team']}", f"{predictions['shots']['shots_away']:.1f}")
                st.metric("A puerta", f"{predictions['shots']['shots_on_target_away']:.1f}")
        
        with tab4:
            st.subheader("📊 Estadísticas del Partido")
            col1, col2 = st.columns(2)
            with col1:
                st.metric(f"ELO {predictions['match_info']['home_team']}", f"{match_data.get('EloHome', 'N/A')}")
            with col2:
                st.metric(f"ELO {predictions['match_info']['away_team']}", f"{match_data.get('EloAway', 'N/A')}")
            
            st.markdown("### 📈 Forma Reciente (últimos 5)")
            col1, col2 = st.columns(2)
            with col1:
                st.metric(f"GD {predictions['match_info']['home_team']}", f"{match_data.get('Home_GD_roll5', 'N/A')}")
            with col2:
                st.metric(f"GD {predictions['match_info']['away_team']}", f"{match_data.get('Away_GD_roll5', 'N/A')}")
            
            st.markdown("### 📋 Resumen Completo")
            resumen = pd.DataFrame({
                'Estadística': ['Prob. Home', 'Prob. Draw', 'Prob. Away', 'xG Home', 'xG Away', 'xG Total',
                               'Over 2.5', 'Under 2.5', 'Corners Home', 'Corners Away', 'Corners Total',
                               'Tarjetas', 'Tiros Home', 'Tiros Away'],
                'Valor': [f"{predictions['1x2']['pH']*100:.1f}%", f"{predictions['1x2']['pD']*100:.1f}%",
                         f"{predictions['1x2']['pA']*100:.1f}%", f"{predictions['goals']['xG_home']:.2f}",
                         f"{predictions['goals']['xG_away']:.2f}", f"{predictions['goals']['xG_total']:.2f}",
                         f"{predictions['over_under_2.5']['pOver']*100:.1f}%", f"{predictions['over_under_2.5']['pUnder']*100:.1f}%",
                         f"{predictions['corners']['corners_home']:.1f}", f"{predictions['corners']['corners_away']:.1f}",
                         f"{predictions['corners']['corners_total']:.1f}", f"{predictions['cards']['total_cards']:.1f}",
                         f"{predictions['shots']['shots_home']:.1f}", f"{predictions['shots']['shots_away']:.1f}"]
            })
            st.dataframe(resumen, use_container_width=True)
    
    except Exception as e:
        st.error(f"Error: {e}")
        st.info("Verifica que exista data/processed/matches.parquet")
