# Load environment variables from .env if present
-include .env
export

PY ?= python
LEAGUES ?= E0 SP1 D1 I1 F1

.PHONY: help venv install env fd fd_org understat fbref prepare dimayor_api backtest report export_probs export_compare alerts clv dashboard all_fd all_dimayor clean

help:
	@echo "Targets:"
	@echo "  venv            Create virtualenv (.venv)"
	@echo "  install         Install dependencies into .venv"
	@echo "  env             Create .env from .env.example if missing"
	@echo "  fd              Download Football-Data for LEAGUES ($(LEAGUES))"
	@echo "  fd_org          Download football-data.org API (live scores, fixtures)"
	@echo "  understat       (Optional) Scrape Understat xG for top leagues (current season)"
	@echo "  fbref           (Optional) Scrape FBref advanced stats (rate limited)"
	@echo "  prepare         Build processed dataset (merge + features)"
	@echo "  dimayor_api     Build Colombia Primera A dataset via API-FOOTBALL"
	@echo "  backtest        Run multi-market backtest (blend + isotonic enabled)"
	@echo "  report          Generate HTML report"
	@echo "  export_probs    Export 1X2 probabilities for test set"
	@echo "  export_compare  Export RAW vs BLEND vs CALIBRATED probabilities"
	@echo "  alerts          Generate value picks for next 7 days (DIMAYOR, Bet365)"
	@echo "  clv             Compute CLV (requires closing odds)"
	@echo "  dashboard       Launch Streamlit dashboard"
	@echo "  all_fd          (FD) fd -> prepare -> backtest -> report"
	@echo "  all_dimayor     (API) dimayor_api -> backtest -> report"
	@echo "  clean           Remove processed & reports"

venv:
	$(PY) -m venv .venv

install: venv
	. .venv/bin/activate && pip install -r requirements.txt

env:
	@test -f .env || cp .env.example .env

fd:
	$(PY) -m src.etl.football_data_multi --leagues $(LEAGUES)

fd_org:
	$(PY) -m src.etl.football_data_org --competitions PL PD BL1 SA FL1 --mode all

understat:
	$(PY) -m src.etl.understat_scraper --leagues EPL La_Liga Bundesliga Serie_A Ligue_1 --start_year auto

fbref:
	$(PY) -m src.etl.fbref_scraper --leagues EPL La_Liga Bundesliga Serie_A Ligue_1 --season current

prepare:
	$(PY) -m src.etl.prepare_dataset_pro

dimayor_api:
	$(PY) -m src.etl.api_football_colombia
	$(PY) scripts/prepare_dimayor_from_api.py

backtest:
	$(PY) scripts/backtest_all_markets.py

report:
	$(PY) scripts/generate_report.py

export_probs:
	$(PY) scripts/export_probs.py

export_compare:
	$(PY) scripts/export_probs_compare.py

alerts:
	$(PY) scripts/alerts_dimayor.py

clv:
	$(PY) scripts/compute_clv.py

dashboard:
	$(PY) -m streamlit run app.py

all_fd: fd prepare backtest report

all_dimayor: dimayor_api backtest report

clean:
	rm -rf data/processed/*.parquet reports/*
