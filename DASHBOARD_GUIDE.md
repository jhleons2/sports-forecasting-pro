# 📊 Guía del Dashboard - Sports Forecasting PRO

## 🌐 Acceso

**URL**: http://localhost:8501

**Comando para lanzar**:
```bash
python -m streamlit run app.py
# O usando Makefile:
make dashboard
```

---

## 🎨 Vista del Dashboard

### **Sección 1: KPIs Principales** (Parte Superior)

```
┌──────────────────────────────────────────────────────────────────┐
│   Sports Forecasting PRO — Dashboard                              │
├──────────────────────────────────────────────────────────────────┤
│                                                                    │
│   📊 KPIs                                                         │
│   ┌────────────┬────────────┬────────────┬────────────┬────────┐│
│   │ Turnover   │    PNL     │    ROI     │  Apuestas  │Hit-rate││
│   │            │            │            │            │        ││
│   │ 2,649.7M   │  +945.5M   │  +35.68%   │    600     │ 58.67% ││
│   │            │            │            │            │        ││
│   └────────────┴────────────┴────────────┴────────────┴────────┘│
│                                                                    │
└──────────────────────────────────────────────────────────────────┘
```

**Métricas:**
- **Turnover**: Total apostado (suma de stakes)
- **PNL**: Profit & Loss neto
- **ROI**: Retorno sobre inversión (PNL/Turnover)
- **Apuestas**: Total de apuestas realizadas
- **Hit-rate**: Porcentaje de apuestas ganadoras

---

### **Sección 2: Curva de Equity** (Gráfico Interactivo)

```
┌──────────────────────────────────────────────────────────────────┐
│   📈 Curva de equity                                              │
│                                                                    │
│   Equity                                                          │
│   │                                                               │
│   │                                              ╱╲               │
│   │                                            ╱    ╲             │
│   │                                          ╱        ╲           │
│   │                                        ╱            ╲         │
│   │                    ╱╲                ╱                        │
│   │                  ╱    ╲            ╱                          │
│   │                ╱        ╲        ╱                            │
│   │              ╱            ╲    ╱                              │
│   │            ╱                ╲╱                                │
│   │          ╱                                                    │
│   │        ╱                                                      │
│   │      ╱                                                        │
│   │    ╱                                                          │
│   │  ╱                                                            │
│   └───────────────────────────────────────────────────────────────│
│      0        100       200       300       400       500    600  │
│                         Apuesta #                                 │
│                                                                    │
│   🖱️ INTERACTIVO: Hover para ver valores exactos                 │
│   🔍 Zoom: Click y arrastra                                       │
│   📥 Descargar: Botón en esquina superior derecha                │
└──────────────────────────────────────────────────────────────────┘
```

**Características:**
- ✅ Gráfico de línea interactivo (Plotly)
- ✅ Hover muestra apuesta # y equity exacto
- ✅ Zoom in/out con rueda del mouse
- ✅ Pan arrastrando con click
- ✅ Reset view con doble click

---

### **Sección 3: Desglose por Mercado**

```
┌──────────────────────────────────────────────────────────────────┐
│   📊 Desglose por mercado                                         │
│                                                                    │
│   ┌─────────┬──────────┬────────────────┬──────────┬─────────┐  │
│   │ market  │ turnover │      pnl       │  bets    │   roi   │  │
│   ├─────────┼──────────┼────────────────┼──────────┼─────────┤  │
│   │   1X2   │  814.0M  │  -210,029,020  │   156    │ -25.80% │  │
│   │   AH    │ 1,657.3M │ +1,158,269,958 │   365    │ +69.89% │  │
│   │  OU2.5  │  178.4M  │   -2,750,813   │    79    │  -1.54% │  │
│   └─────────┴──────────┴────────────────┴──────────┴─────────┘  │
│                                                                    │
│   🏆 Mejor mercado: AH (Asian Handicap) con +69.89% ROI          │
│   ⚠️  Mercado 1X2 requiere optimización                          │
└──────────────────────────────────────────────────────────────────┘
```

---

### **Sección 4: Explorador de Apuestas**

```
┌──────────────────────────────────────────────────────────────────┐
│   🔍 Explorador de apuestas                                       │
│                                                                    │
│   Liga: [Dropdown]  ▼                                            │
│         ┌─────────────────────────────┐                          │
│         │ (todas)                     │                          │
│         │ E0  (Premier League)        │                          │
│         │ SP1 (La Liga)               │                          │
│         │ D1  (Bundesliga)            │                          │
│         │ I1  (Serie A)               │                          │
│         │ F1  (Ligue 1)               │                          │
│         └─────────────────────────────┘                          │
│                                                                    │
│   📋 Tabla de apuestas (scrollable, ordenable)                   │
│   ┌─────────┬─────────┬────────┬──────┬──────┬──────┬─────┬────┐│
│   │  date   │ league  │ market │ sel. │ odds │stake │ pnl │res ││
│   ├─────────┼─────────┼────────┼──────┼──────┼──────┼─────┼────┤│
│   │2025-10-05│  E0   │  AH    │  H   │ 1.95 │ 1000 │+950 │WIN ││
│   │2025-10-04│  SP1  │  1X2   │  A   │ 2.50 │  500 │-500 │LOSS││
│   │2025-10-04│  D1   │  OU2.5 │ Over │ 1.85 │  750 │+637 │WIN ││
│   │   ...   │  ...  │  ...   │ ...  │ ...  │ ...  │ ... │... ││
│   └─────────┴─────────┴────────┴──────┴──────┴──────┴─────┴────┘│
│                                                                    │
│   ⬆️⬇️ Click en columnas para ordenar                             │
│   📄 Scroll para ver todas las apuestas                          │
└──────────────────────────────────────────────────────────────────┘
```

**Filtros disponibles:**
- Por liga (E0, SP1, D1, I1, F1)
- Ordenamiento por cualquier columna

---

### **Sección 5: Información del Dataset** (Sidebar Izquierda)

```
┌─────────────────────────────┐
│   📁 Dataset                │
├─────────────────────────────┤
│                             │
│   Partidos cargados:        │
│   2,079                     │
│                             │
│   Rango de fechas:          │
│   2024-08-15 → 2025-10-05  │
│                             │
│                             │
│   📖 Fuentes:               │
│   • Football-Data.co.uk     │
│   • football-data.org       │
│                             │
└─────────────────────────────┘
```

---

## 🎯 Casos de Uso del Dashboard

### **1. Análisis de Rendimiento Global**
```
✅ Ver KPIs principales de un vistazo
✅ ROI general del sistema
✅ Número total de apuestas y hit-rate
```

### **2. Seguimiento de Equity**
```
✅ Visualizar crecimiento del bankroll
✅ Identificar periodos de drawdown
✅ Verificar consistencia del sistema
```

### **3. Análisis por Mercado**
```
✅ Comparar rendimiento 1X2 vs AH vs OU
✅ Identificar mercados más rentables
✅ Detectar mercados que necesitan mejora
```

### **4. Exploración Detallada**
```
✅ Buscar apuestas específicas
✅ Filtrar por liga
✅ Analizar patrones de wins/losses
✅ Verificar odds y stakes
```

---

## 🔧 Personalización

El dashboard se puede personalizar editando `app.py`:

### **Agregar Nuevas Métricas:**
```python
# En app.py, después de las métricas actuales:
c6 = st.columns(1)
max_drawdown = calcular_drawdown(log)
c6.metric("Drawdown Máximo", f"{max_drawdown:.2%}")
```

### **Agregar Filtros Adicionales:**
```python
# Agregar filtro por mercado:
markets = ["(todos)"] + sorted(log["market"].unique().tolist())
sel_market = st.selectbox("Mercado", markets)
df_view = log if sel_market=="(todos)" else log[log["market"]==sel_market]
```

### **Agregar Gráficos:**
```python
# Gráfico de distribución de odds:
fig = px.histogram(log, x="odds", nbins=50, title="Distribución de Odds")
st.plotly_chart(fig, use_container_width=True)
```

---

## 🚨 Solución de Problemas

### **Error: "streamlit no se reconoce"**
```bash
# Solución: Usar python -m
python -m streamlit run app.py
```

### **Error: "No encuentro reports/backtest_log.csv"**
```bash
# Solución: Ejecutar backtesting primero
python scripts/backtest_all_markets.py
```

### **Error: "No encuentro data/processed/matches.parquet"**
```bash
# Solución: Preparar dataset
python -m src.etl.football_data_multi --leagues E0 SP1 D1 I1 F1
python -m src.etl.prepare_dataset_pro
```

### **Dashboard muy lento**
```bash
# Solución 1: Reducir tamaño del dataset
# Filtrar solo últimos 6 meses en backtest

# Solución 2: Usar caching
# En app.py, agregar @st.cache_data a funciones de carga
```

---

## 📱 Acceso Remoto

### **Compartir en Red Local:**
```bash
# Lanzar con IP específica:
python -m streamlit run app.py --server.address 0.0.0.0

# Acceder desde otro dispositivo en la misma red:
http://TU_IP_LOCAL:8501
```

### **Desplegar en Nube (Streamlit Cloud):**
```bash
# 1. Subir a GitHub
git init
git add .
git commit -m "Initial commit"
git push

# 2. Ir a https://share.streamlit.io/
# 3. Conectar repositorio
# 4. Seleccionar app.py
# 5. Deploy! 🚀
```

---

## 🎨 Temas y Estilo

### **Cambiar Tema:**

Crear archivo `.streamlit/config.toml`:

```toml
[theme]
primaryColor = "#1f77b4"
backgroundColor = "#0e1117"
secondaryBackgroundColor = "#262730"
textColor = "#fafafa"
font = "sans serif"
```

---

## 📊 Métricas Disponibles en el Log

El archivo `reports/backtest_log.csv` contiene:

```csv
date,league,market,selection,line,odds,stake,
p_model,p_mkt,result,pnl,equity,edge
```

**Columnas:**
- `date`: Fecha del partido
- `league`: Liga (E0, SP1, etc.)
- `market`: Mercado (1X2, AH, OU2.5)
- `selection`: Selección (H/D/A, Over/Under)
- `line`: Línea (para AH)
- `odds`: Cuota apostada
- `stake`: Cantidad apostada (Kelly sizing)
- `p_model`: Probabilidad del modelo
- `p_mkt`: Probabilidad del mercado
- `result`: WIN/LOSS
- `pnl`: Ganancia/pérdida
- `equity`: Bankroll acumulado
- `edge`: Ventaja percibida (p_model - p_mkt)

---

## 🔄 Actualización en Tiempo Real

Para actualizar el dashboard con nuevos datos:

```bash
# 1. Descargar nuevos datos
python -m src.etl.football_data_multi --leagues E0 SP1 D1 I1 F1

# 2. Re-procesar
python -m src.etl.prepare_dataset_pro

# 3. Re-ejecutar backtest
python scripts/backtest_all_markets.py

# 4. El dashboard se actualizará automáticamente al refrescar
# O presiona 'R' en el dashboard
```

---

## 💡 Tips Avanzados

### **1. Múltiples Páginas:**
```python
# Crear carpeta pages/
pages/
  ├── 1_📊_Overview.py
  ├── 2_🔍_Analysis.py
  └── 3_⚙️_Settings.py

# Streamlit las detectará automáticamente
```

### **2. Widgets Interactivos:**
```python
# Slider para filtrar por edge mínimo:
min_edge = st.slider("Edge mínimo", 0.0, 0.10, 0.02)
df_filtered = log[log['edge'] >= min_edge]
```

### **3. Descarga de Datos:**
```python
# Botón para descargar CSV:
csv = log.to_csv(index=False).encode('utf-8')
st.download_button(
    label="📥 Descargar log completo",
    data=csv,
    file_name='backtest_log.csv',
    mime='text/csv'
)
```

---

## 🎓 Recursos Adicionales

- **Documentación Streamlit**: https://docs.streamlit.io/
- **Galería de Apps**: https://streamlit.io/gallery
- **Componentes**: https://streamlit.io/components
- **Argon Dashboard** (tu framework UI): [[memory:2415242]]

---

**Dashboard listo en**: http://localhost:8501  
**Para detener**: Ctrl+C en la terminal donde se ejecuta

