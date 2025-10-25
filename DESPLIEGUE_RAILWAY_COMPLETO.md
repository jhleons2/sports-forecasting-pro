# 🚀 GUÍA COMPLETA DE DESPLIEGUE EN RAILWAY

## ✅ **ARCHIVOS LISTOS PARA PRODUCCIÓN**

### **Archivos de Configuración:**
- ✅ `railway.toml` - Configurado con `app_argon_con_reglas.py`
- ✅ `requirements-railway.txt` - Todas las dependencias
- ✅ `railway.env` - Variables de entorno
- ✅ `app_argon_con_reglas.py` - Dashboard con 5 reglas dinámicas

## 📋 **PASOS PARA DESPLEGAR**

### **1. Preparar el Repositorio**

```bash
# Verificar que estás en el directorio correcto
cd sports-forecasting-pro

# Verificar que los archivos existen
ls railway.toml
ls app_argon_con_reglas.py
ls requirements-railway.txt
ls data/processed/matches.parquet
```

### **2. Subir a GitHub (si aún no está)**

```bash
# Inicializar git si no está inicializado
git init

# Agregar todos los archivos
git add .

# Commit inicial
git commit -m "Deploy to Railway - Dashboard con reglas dinámicas"

# Agregar tu repositorio remoto (reemplaza con tu URL)
git remote add origin https://github.com/TU_USUARIO/sports-forecasting-pro.git

# Push al repositorio
git branch -M main
git push -u origin main
```

### **3. Configurar Railway**

#### **Opción A: Desde el Dashboard Web (Recomendado)**

1. **Ir a Railway:**
   - Abre: https://railway.app
   - Inicia sesión con GitHub

2. **Crear Nuevo Proyecto:**
   - Click en "New Project"
   - Selecciona "Deploy from GitHub repo"
   - Busca tu repositorio: `sports-forecasting-pro`
   - Click en "Deploy Now"

3. **Configurar Variables de Entorno:**
   - Ve a "Variables"
   - Agrega las siguientes variables:
   
   ```
   PORT = 8080
   FLASK_ENV = production
   FLASK_DEBUG = False
   SECRET_KEY = sistema_precision_maxima_2025
   FOOTBALL_API_KEY = 2b1693b0c9ba4a99bf8346cd0a9d27d0
   PYTHONPATH = /app
   ```

4. **Verificar la Configuración:**
   - Railway detectará automáticamente el `railway.toml`
   - Usará `requirements-railway.txt` para instalar dependencias
   - Ejecutará `app_argon_con_reglas.py` como aplicación principal

#### **Opción B: Desde la CLI**

```bash
# Instalar Railway CLI
npm install -g @railway/cli

# Login
railway login

# Inicializar proyecto
railway init

# Conectar a un proyecto existente (si tienes uno)
railway link

# Desplegar
railway up
```

## 🔍 **VERIFICACIÓN DEL DESPLIEGUE**

### **1. Verificar Logs:**
En Railway Dashboard:
- Ve a tu proyecto
- Click en "Deployments"
- Ve a "Logs"
- Debes ver:
  ```
  DASHBOARD CON TUS 5 REGLAS - SPORTS FORECASTING PRO
  PREDICTOR LISTO
  Running on http://0.0.0.0:8080
  ```

### **2. Probar el Dashboard:**
- Abre la URL proporcionada por Railway
- URL típica: `https://TU_PROYECTO.up.railway.app`
- Debe mostrar el dashboard con ligas y partidos

### **3. Endpoints de Verificación:**
Prueba estos endpoints:

```
# Health check
https://TU_PROYECTO.up.railway.app/health

# Dashboard principal
https://TU_PROYECTO.up.railway.app/

# Status
https://TU_PROYECTO.up.railway.app/status
```

## ⚠️ **POSIBLES PROBLEMAS Y SOLUCIONES**

### **Problema 1: "No module named 'xxx'"**
**Solución:**
```bash
# Verificar que requirements-railway.txt tiene todas las dependencias
# Asegúrate de incluir todas las librerías que usa app_argon_con_reglas.py
```

### **Problema 2: "File not found: matches.parquet"**
**Solución:**
```bash
# Los archivos de datos deben estar en el repositorio
# Verificar que data/processed/ está incluido en git
git add data/
git commit -m "Add processed data"
git push
```

### **Problema 3: "Port already in use"**
**Solución:**
```bash
# Railway asigna el puerto automáticamente
# Asegúrate de usar os.environ.get('PORT', 8080)
# Ya está configurado en app_argon_con_reglas.py
```

### **Problema 4: Health check falla**
**Solución:**
```bash
# Verificar que el endpoint /health existe
# Ya está implementado en app_argon_con_reglas.py
# Debe retornar status 200
```

## 🔧 **CONFIGURACIÓN ADICIONAL**

### **Agregar Dominio Personalizado:**
1. En Railway Dashboard
2. Ve a "Settings" > "Domains"
3. Agrega tu dominio personalizado

### **Monitoreo:**
1. Railway Dashboard > "Metrics"
2. Ver CPU, RAM, Request/Response

### **Logs en Tiempo Real:**
1. Railway Dashboard > "Deployments" > "Logs"
2. Ver logs en tiempo real

## 📊 **ESTADO DEL DASHBOARD EN RAILWAY**

### **Características Activadas:**
- ✅ Dashboard con 5 reglas dinámicas
- ✅ Mapeo automático de nombres
- ✅ Predicciones con Dixon-Coles
- ✅ Análisis con reglas calculadas desde HOY
- ✅ Sistema de alertas
- ✅ Fixtures próximos (48 horas)

### **Endpoints Disponibles:**
- `/` - Dashboard principal
- `/predict/<league>/<match>` - Predicción detallada
- `/analysis/<league>/<match>` - Análisis con reglas
- `/health` - Health check
- `/status` - Estado del sistema
- `/sync` - Sincronizar fixtures

## 🎯 **SIGUIENTE URL**

Una vez desplegado, tu dashboard estará en:
**`https://web-production-3cdd2.up.railway.app`**

## 📞 **SUPPORT**

Si tienes problemas:
1. Revisa los logs en Railway Dashboard
2. Verifica que todas las variables de entorno estén configuradas
3. Asegúrate de que los archivos de datos estén en el repositorio

---

**¡Listo! Tu proyecto estará desplegado en Railway con todas las funcionalidades activas.**
