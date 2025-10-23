@echo off
cd /d "%~dp0"
echo.
echo ========================================================================
echo   INICIANDO DASHBOARD - SPORTS FORECASTING PRO
echo ========================================================================
echo.
echo Cargando predictor... (esto toma unos 10 segundos)
echo.
python app_argon_con_reglas.py
pause


