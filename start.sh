#!/bin/bash
# Script de inicio para Railway

echo "🚀 Iniciando Sistema de Precisión Máxima..."

# Verificar que Python esté disponible
python --version

# Verificar que los archivos necesarios estén presentes
if [ ! -f "app_argon_con_reglas.py" ]; then
    echo "❌ Error: app_argon_con_reglas.py no encontrado"
    exit 1
fi

if [ ! -f "requirements-railway.txt" ]; then
    echo "❌ Error: requirements-railway.txt no encontrado"
    exit 1
fi

# Instalar dependencias si es necesario
echo "📦 Instalando dependencias..."
pip install -r requirements-railway.txt

# Crear directorios necesarios
mkdir -p data/processed
mkdir -p static
mkdir -p templates

# Establecer variables de entorno
export PYTHONPATH=/app
export FLASK_ENV=production
export FLASK_DEBUG=False

# Iniciar la aplicación
echo "🎯 Iniciando aplicación Flask..."
python app_argon_con_reglas.py
