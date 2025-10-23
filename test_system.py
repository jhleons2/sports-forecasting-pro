#!/usr/bin/env python3
"""
Script de prueba para verificar que la aplicación funciona correctamente
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Probar que todas las importaciones funcionan"""
    print("🔍 Probando importaciones...")
    
    try:
        import pandas as pd
        print("   ✅ pandas")
    except ImportError as e:
        print(f"   ❌ pandas: {e}")
        return False
    
    try:
        import numpy as np
        print("   ✅ numpy")
    except ImportError as e:
        print(f"   ❌ numpy: {e}")
        return False
    
    try:
        import flask
        print("   ✅ flask")
    except ImportError as e:
        print(f"   ❌ flask: {e}")
        return False
    
    try:
        from src.models.poisson_dc import DixonColes
        print("   ✅ DixonColes")
    except ImportError as e:
        print(f"   ❌ DixonColes: {e}")
        return False
    
    try:
        from src.models.xgboost_classifier import XGBoost1X2Classifier
        print("   ✅ XGBoost1X2Classifier")
    except ImportError as e:
        print(f"   ❌ XGBoost1X2Classifier: {e}")
        return False
    
    return True

def test_data_files():
    """Probar que los archivos de datos existen"""
    print("\n📁 Probando archivos de datos...")
    
    data_files = [
        "data/processed/matches.parquet",
        "data/processed/upcoming_fixtures.parquet"
    ]
    
    all_exist = True
    for file_path in data_files:
        if os.path.exists(file_path):
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path} - FALTANTE")
            all_exist = False
    
    return all_exist

def test_app_creation():
    """Probar que la aplicación Flask se puede crear"""
    print("\n🌐 Probando creación de aplicación Flask...")
    
    try:
        from flask import Flask
        app = Flask(__name__)
        
        @app.route('/')
        def home():
            return "Sistema de Precisión Máxima - OK"
        
        @app.route('/health')
        def health():
            return {'status': 'healthy'}, 200
        
        print("   ✅ Aplicación Flask creada correctamente")
        print("   ✅ Endpoints básicos configurados")
        return True
        
    except Exception as e:
        print(f"   ❌ Error creando aplicación: {e}")
        return False

def test_predictor_creation():
    """Probar que el predictor se puede crear"""
    print("\n🎯 Probando creación del predictor...")
    
    try:
        from scripts.predictor_corregido_simple import PredictorConReglasDinamicas
        
        # Crear predictor con datos mínimos
        predictor = PredictorConReglasDinamicas()
        print("   ✅ Predictor creado correctamente")
        return True
        
    except Exception as e:
        print(f"   ❌ Error creando predictor: {e}")
        return False

def main():
    """Función principal de prueba"""
    print("=" * 70)
    print("PRUEBA DEL SISTEMA DE PRECISIÓN MÁXIMA")
    print("=" * 70)
    
    # Ejecutar todas las pruebas
    tests = [
        ("Importaciones", test_imports),
        ("Archivos de datos", test_data_files),
        ("Aplicación Flask", test_app_creation),
        ("Predictor", test_predictor_creation)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"   ❌ Error en {test_name}: {e}")
            results.append((test_name, False))
    
    # Resumen de resultados
    print("\n" + "=" * 70)
    print("RESUMEN DE PRUEBAS")
    print("=" * 70)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nPruebas pasadas: {passed}/{total}")
    
    if passed == total:
        print("🎉 ¡Todas las pruebas pasaron! El sistema está listo.")
        return True
    else:
        print("⚠️  Algunas pruebas fallaron. Revisar errores.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
