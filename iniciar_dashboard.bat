@echo off
cd /d "%~dp0"
echo.
echo ========================================================================
echo   INICIANDO DASHBOARD - SPORTS FORECASTING PRO
echo ========================================================================
echo.
echo Puerto 5000 libre ✓
echo Iniciando servidor...
echo.
echo El modelo Dixon-Coles necesita entrenarse (10-15 segundos)
echo.
python app_argon_con_reglas.py
echo.
echo Dashboard detenido.
pause

