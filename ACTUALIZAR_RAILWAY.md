# 🔧 INSTRUCCIONES PARA ACTUALIZAR RAILWAY

## Problema Actual
El servidor Railway muestra predicciones INCORRECTAS porque usa código antiguo:
- ❌ Crystal Palace 53.5% (INCORRECTO - Arsenal ganó 1-0)
- ❌ Arsenal 0% efectividad (datos no encontrados)

## Causa
El código en Railway NO tiene las correcciones recientes:
1. Mapeo manual de "Arsenal FC" → "Arsenal"
2. Ajustes mejorados de forma reciente (+20% vs +8%)

## Solución

### Opción 1: Deploy Automático (Recomendado)
Si Railway está conectado a Git:

```bash
# 1. Verificar cambios
git status

# 2. Hacer commit de las correcciones
git add .
git commit -m "Fix: Corrección de mapeo Arsenal y ajustes de predicción"

# 3. Push a Railway
git push origin main
```

Railway detectará el push y desplegará automáticamente.

---

### Opción 2: Deploy Manual
Si Railway NO está conectado a Git:

1. **Acceder a Railway Dashboard:**
   - Ir a https://railway.app
   - Seleccionar tu proyecto
   - Ir a "Settings" → "Deploy"

2. **Forzar redeploy:**
   - Click en "Redeploy"
   - O usar el comando CLI:
   ```bash
   railway redeploy
   ```

---

### Opción 3: Verificación Local
Antes de deployar, verificar que funciona localmente:

```bash
python test_prediccion_arsenal.py
```

**Resultado esperado:**
```
Arsenal: 74.3% ✅
Empate: 16.4%
Crystal Palace: 9.3%
```

Si muestra esto, está listo para deployar.

---

## Archivos Modificados
1. `src/utils/mapeador_dinamico.py` - Mapeo manual agregado
2. `scripts/predictor_corregido_simple.py` - Ajustes mejorados

---

## Verificación Post-Deploy
1. Esperar 2-3 minutos después del deploy
2. Ir a: https://web-production-3cdd2.up.railway.app/predict/E0/2
3. Verificar que muestra:
   - ✅ Arsenal como favorito (>50%)
   - ✅ Arsenal con datos históricos (no 0% efectividad)
