# Sports Forecasting PRO (Real Data) — 1X2, OU, AH + Dashboard

Proyecto completo para **pronóstico probabilístico y backtesting** con **datos reales**:

- **ETL por HTTP/scraping** para resultados y cuotas (Football-Data) y **xG** (Understat *opcional*).
- **Modelos**: Dixon–Coles (marcadores) + Boosting, **calibración** y **blending** con mercado.
- **Backtesting multi-mercado**: **1X2**, **Over/Under 2.5**, **Asian Handicap** (línea `AHh`).
- **Reporte HTML** con ROI/Drawdown y **Dashboard Streamlit** interactivo.
- **Datos del último año**: scripts descargan **temporada pasada y actual** automáticamente.

> Fuentes: Football-Data.co.uk (CSV/HTTP), Understat (scraping responsable). Ver sección **Fuentes & Legal**.

## Instalación

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

## Uso rápido (Top-5 ligas, última temporada + actual)
```bash
# 1) Descargar resultados/cuotas reales (Football-Data)
python -m src.etl.football_data_multi --leagues E0 SP1 D1 I1 F1

# 2) (Opcional) Scraping xG de Understat para esas ligas (temporada actual)
python -m src.etl.understat_scraper --leagues EPL La_Liga Bundesliga Serie_A Ligue_1 --start_year auto

# 2b) (Opcional) Scraping de estadísticas avanzadas de FBref (rate limited)
python -m src.etl.fbref_scraper --leagues EPL La_Liga Bundesliga Serie_A Ligue_1 --season current

# 3) Preparar dataset (merge + features + mapeos de nombres)
python -m src.etl.prepare_dataset_pro

# 4) Backtest + Log detallado
python scripts/backtest_all_markets.py

# 5) Reporte HTML + gráficos
python scripts/generate_report.py

# 6) Dashboard Streamlit
streamlit run app.py
```

## Estructura
```
sports-forecasting-pro/
├─ README.md
├─ requirements.txt
├─ .env.example
├─ data/
│  ├─ raw/                 # CSVs y JSON crudos
│  ├─ interim/             # Limpiezas parciales
│  └─ processed/           # Dataset final (parquet/csv)
├─ config/
│  └─ team_mapping.yaml    # Mapeos de nombres (Understat ↔ Football-Data)
├─ reports/
│  └─ (se crea en runtime) backtest_log.csv, equity.png, backtest_report.html
├─ src/
│  ├─ etl/
│  │  ├─ football_data_multi.py
│  │  ├─ understat_scraper.py
│  │  └─ prepare_dataset_pro.py
│  ├─ features/
│  │  ├─ ratings.py
│  │  └─ rolling.py
│  ├─ models/
│  │  ├─ poisson_dc.py
│  │  ├─ boosting.py
│  │  ├─ ensemble.py
│  │  └─ calibration.py
│  ├─ backtest/
│  │  ├─ bankroll.py
│  │  ├─ walk_forward.py
│  │  └─ settle.py
│  ├─ reporting/
│  │  └─ metrics.py
│  ├─ serve/
│  │  └─ api.py
│  └─ utils/
│     ├─ odds.py
│     └─ names.py
├─ scripts/
│  ├─ backtest_all_markets.py
│  ├─ generate_report.py
│  └─ export_probs.py
└─ app.py                  # Streamlit dashboard
```

## Fuentes & Legal
- **Football-Data.co.uk**: resultados + cuotas (apertura/cierre). Revisa su documentación y atribución.
- **Understat**: xG por partido; *scraping responsable* y respetar `robots.txt` y Términos. Sólo para análisis personal/educativo.
- **FBref**: estadísticas avanzadas; scraping permitido con rate limiting (<20 req/min). Ver: https://www.sports-reference.com/bot-traffic.html
- **API-FOOTBALL**: requiere clave RapidAPI; respeta límites del plan.
- Revisa las leyes y TOS locales antes de automatizar scraping o redistribuir datos. **No garantizamos disponibilidad/estabilidad de endpoints.**

📖 **Guía completa de scraping**: Ver [`docs/SCRAPING_GUIDE.md`](docs/SCRAPING_GUIDE.md)

*PRO scaffold generado: 2025-10-20T16:37:57.789228 UTC.*


### Colombia (BetPlay DIMAYOR) por **API-FOOTBALL**
Requiere clave **RapidAPI** para `api-football-v1.p.rapidapi.com`.

```bash
# 0) Variables de entorno en .env (ejemplo)
# API_FOOTBALL_KEY=tu_clave_rapidapi
# API_FOOTBALL_HOST=api-football-v1.p.rapidapi.com

# 1) Descargar fixtures + odds Bet365 (últimos 2 años)
python -m src.etl.api_football_colombia

# 2) Preparar dataset procesado
python scripts/prepare_dimayor_from_api.py

# 3) Backtest + Reporte
python scripts/backtest_all_markets.py
python scripts/generate_report.py
```

> La búsqueda del **league_id** se hace automáticamente via `/leagues?country=Colombia` y selecciona *Primera A*. Si tu cuenta no expone esa liga, verifica tu plan en API-FOOTBALL.


### CLV y closing odds
- Para **Top-5 ligas** desde Football-Data ya vienen columnas de **cierre** (Pinnacle/Avg/Bet365), por lo que `scripts/compute_clv.py` añade `clv` a cada apuesta 1X2 del log automáticamente.
- Para **DIMAYOR** u otras ligas sin cierre público, puedes usar un proveedor externo:
  - **The Odds API** (histórico con *snapshots* y soporte para Pinnacle/Bet365) — requiere API key y plan con histórico.
  - **Sportmonks / SportsDataIO / OddsJam** — opciones con histórico y cierre.
  - Configura `THE_ODDS_API_KEY` en `.env` y usa `src/etl/the_odds_api.py` para traer precios (actuales o snapshots).
> Nota: Desde **23-Jul-2025** el acceso público a la **Pinnacle API** se cerró; se requiere aprobación o usar agregadores/históricos de terceros.

### Alertas de picks (DIMAYOR)
```bash
# Variables opcionales en .env para Telegram
# TELEGRAM_BOT_TOKEN=...
# TELEGRAM_CHAT_ID=...

# Genera picks de valor (próximos 7 días, Bet365) y opcionalmente envía a Telegram
python scripts/alerts_dimayor.py
# CSV de salida:
# reports/alerts_picks.csv
```


## Uso con Makefile (atajos)
```bash
# 0) instalar deps y crear .env
make install env

# 1) Top-5 ligas (Football-Data): descarga -> prepara -> backtest -> reporte
make all_fd

# 2) Colombia (DIMAYOR) por API-FOOTBALL: descarga -> prepara -> backtest -> reporte
make all_dimayor

# 3) CLV (si hay cierres en el dataset)
make clv

# 4) Alertas de picks (próximos 7 días, Bet365)
make alerts

# 5) Dashboard
make dashboard
```
