"""
CONFIGURACIÓN PARA RAILWAY
=========================

Este archivo contiene la configuración específica para el despliegue en Railway.
"""

import os
from pathlib import Path

# Configuración base
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
PROCESSED_DIR = DATA_DIR / "processed"

# Configuración de Railway
PORT = int(os.environ.get("PORT", 5000))
HOST = "0.0.0.0"  # Railway requiere 0.0.0.0
DEBUG = os.environ.get("FLASK_DEBUG", "False").lower() == "true"

# Configuración de la aplicación
SECRET_KEY = os.environ.get("SECRET_KEY", "sports-forecasting-pro-2025-railway")

# Configuración de archivos
UPLOAD_FOLDER = PROCESSED_DIR
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

# Configuración de logging
LOG_LEVEL = "INFO" if not DEBUG else "DEBUG"

# Configuración de datos
DATA_FILES = {
    "matches": PROCESSED_DIR / "matches.parquet",
    "fixtures": PROCESSED_DIR / "upcoming_fixtures.parquet",
    "fixtures_mapeado": PROCESSED_DIR / "upcoming_fixtures_mapeado.parquet"
}

# Verificar que los archivos de datos existen
def verificar_archivos_datos():
    """Verificar que los archivos de datos necesarios existen"""
    archivos_faltantes = []
    
    for nombre, archivo in DATA_FILES.items():
        if not archivo.exists():
            archivos_faltantes.append(f"{nombre}: {archivo}")
    
    if archivos_faltantes:
        print("⚠️ ADVERTENCIA: Archivos de datos faltantes:")
        for archivo in archivos_faltantes:
            print(f"   - {archivo}")
        print("   La aplicación puede no funcionar correctamente.")
    else:
        print("✅ Todos los archivos de datos están presentes.")

# Configuración de Railway específica
RAILWAY_CONFIG = {
    "port": PORT,
    "host": HOST,
    "debug": DEBUG,
    "secret_key": SECRET_KEY,
    "log_level": LOG_LEVEL
}

if __name__ == "__main__":
    print("🔧 CONFIGURACIÓN RAILWAY:")
    print(f"   Puerto: {PORT}")
    print(f"   Host: {HOST}")
    print(f"   Debug: {DEBUG}")
    print(f"   Directorio base: {BASE_DIR}")
    print()
    verificar_archivos_datos()
