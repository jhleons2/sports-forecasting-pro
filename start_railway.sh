#!/bin/bash
# Script de inicio robusto para Railway

echo "=========================================="
echo "SISTEMA DE PRECISION MAXIMA (75.2%)"
echo "=========================================="

# Verificar Python
echo "Verificando Python..."
python --version

# Verificar archivos necesarios
echo "Verificando archivos..."
if [ ! -f "start_app.py" ]; then
    echo "ERROR: start_app.py no encontrado"
    exit 1
fi

if [ ! -f "requirements-railway.txt" ]; then
    echo "ERROR: requirements-railway.txt no encontrado"
    exit 1
fi

# Instalar dependencias
echo "Instalando dependencias..."
pip install -r requirements-railway.txt

# Crear directorios necesarios
echo "Creando directorios..."
mkdir -p templates
mkdir -p static
mkdir -p data/processed

# Establecer variables de entorno
export PYTHONPATH=/app
export FLASK_ENV=production
export FLASK_DEBUG=False

# Iniciar aplicación
echo "Iniciando Sistema de Precisión Máxima..."
python start_app.py
