# 📍 DÓNDE VER LA JUSTIFICACIÓN - GUÍA VISUAL

## 🌐 **URL DEL DASHBOARD:**
**http://localhost:5000**

---

## 📺 **UBICACIÓN EXACTA EN LA PÁGINA:**

```
┌─────────────────────────────────────────────────────────────┐
│                    NAVEGADOR WEB                            │
│  URL: http://localhost:5000/predict/E0/2                   │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                                                             │
│           Newcastle United FC vs Fulham FC                  │
│                   2025-10-25                                │
│                                                             │
└─────────────────────────────────────────────────────────────┘

┌──────────────┬──────────────┬──────────────┐
│  GANA LOCAL  │   EMPATE     │  GANA VISIT. │
│              │              │              │
│    25.0%     │    29.8%     │    45.2%     │
│              │              │              │
│  Newcastle   │   Empate     │   Fulham     │
└──────────────┴──────────────┴──────────────┘

        ⬇️  HAZ SCROLL HACIA ABAJO  ⬇️
        ═══════════════════════════════

┌─────────────────────────────────────────────────────────────┐
│ ℹ️  ¿Por qué estos porcentajes?                    ← AQUÍ │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  📊 Forma reciente:          🏠 Rendimiento local:        │
│  Newcastle: 9/24 pts          Newcastle en casa:          │
│  (37.5%)                      6 GF - 6 GA                  │
│  Fulham: 8/24 pts             Win rate: 40.0%             │
│  (33.3%)                                                   │
│                                                             │
│  ✈️ Rendimiento visitante:    🔄 H2H:                     │
│  Fulham fuera:                 0W - 0D - 2L               │
│  6 GF - 11 GA                  (2 partidos)               │
│  Win rate: 20.0%               Fulham domina              │
│                                                             │
│  🕒 Calculado dinámicamente desde 2025-10-21              │
└─────────────────────────────────────────────────────────────┘

        ⬇️  MÁS ABAJO  ⬇️

┌─────────────────────────────────────────────────────────────┐
│  TUS 5 REGLAS DINÁMICAS - JUSTIFICACIÓN DETALLADA         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  📊 REGLA 1: Últimos 8 partidos total                     │
│  🏠 REGLA 2: Últimos 5 de local                           │
│  ✈️  REGLA 3: Últimos 5 de visitante                      │
│  🔄 REGLA 4: 5 entre sí (H2H)                             │
│  🚑 REGLA 5: Bajas de jugadores                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 **PASOS ESPECÍFICOS:**

### **1. Abrir Dashboard**
```
http://localhost:5000
```

### **2. En la Página Principal**
- Verás una lista de partidos por liga
- Ejemplo: "Newcastle United FC vs Fulham FC"
- Busca el botón **"Ver Predicción"**

### **3. Clic en "Ver Predicción"**
- Te lleva a una página con los 3 porcentajes grandes
- IMPORTANTE: No te quedes solo ahí

### **4. HAZ SCROLL HACIA ABAJO** ⬇️
- Después de ver los 3 porcentajes (Local/Empate/Visitante)
- Baja con la rueda del mouse
- O con la barra de scroll lateral

### **5. Buscar la Caja Azul**
- Color: **AZUL CLARO** (alert-info)
- Título: **"ℹ️ ¿Por qué estos porcentajes?"**
- Tiene 4 columnas con íconos

---

## ❓ **SI NO LA VES:**

### **Opción 1: Limpiar Caché del Navegador**
```
Windows: Ctrl + F5
Mac: Cmd + Shift + R
```

### **Opción 2: Modo Incógnito**
```
Chrome: Ctrl + Shift + N
Firefox: Ctrl + Shift + P
Edge: Ctrl + Shift + N
```

### **Opción 3: Verificar la URL**
Asegúrate de estar en:
```
http://localhost:5000/predict/E0/[número]
```

**NO** en:
```
http://localhost:5000/analysis/E0/[número]  ← Esta es otra página
```

---

## 🔍 **CARACTERÍSTICAS DE LA JUSTIFICACIÓN:**

### **Aspecto Visual:**
- ✅ Caja con fondo **AZUL CLARO**
- ✅ Ícono de **información** (ℹ️)
- ✅ Título: **"¿Por qué estos porcentajes?"**
- ✅ **4 columnas** con datos

### **Contenido:**
1. **📊 Forma reciente** - Últimos 8 partidos
2. **🏠 Rendimiento local** - Win rate en casa
3. **✈️ Rendimiento visitante** - Win rate fuera
4. **🔄 H2H** - Enfrentamientos directos

---

## 💡 **TIPS:**

### **1. Posición en la Página:**
- ❌ NO está al principio
- ❌ NO está junto a los porcentajes grandes
- ✅ Está **DEBAJO** de los porcentajes
- ✅ Está **ANTES** de la sección "TUS 5 REGLAS DINÁMICAS"

### **2. Si Usas Móvil/Tablet:**
- La justificación se adapta al tamaño
- Puede aparecer en 2 o 4 columnas dependiendo del ancho
- Haz scroll más hacia abajo

### **3. Resolución de Pantalla:**
- En pantallas pequeñas, los datos se apilan verticalmente
- En pantallas grandes, aparecen las 4 columnas horizontales

---

## 🚀 **VERIFICACIÓN RÁPIDA:**

### **Comando para Probar:**
Abre en tu navegador exactamente esta URL:
```
http://localhost:5000/predict/E0/2
```

### **Qué Esperar Ver:**
1. Header con "Newcastle United FC vs Fulham FC"
2. 3 tarjetas grandes con porcentajes
3. **HAZ SCROLL** ⬇️
4. Caja azul "¿Por qué estos porcentajes?"
5. Más abajo: "TUS 5 REGLAS DINÁMICAS"

---

## 📞 **SI AÚN NO LA VES:**

### **Verifica que el Dashboard esté Actualizado:**
```bash
# Detén el dashboard (Ctrl+C en la terminal)
# Vuelve a iniciarlo:
python app_argon_con_reglas.py
```

### **Luego en el Navegador:**
1. Cierra todas las pestañas de localhost:5000
2. Abre una nueva pestaña
3. Ve a http://localhost:5000
4. Presiona Ctrl+F5 (Windows) o Cmd+Shift+R (Mac)
5. Selecciona un partido
6. HAZ SCROLL hacia abajo

---

## ✅ **CONFIRMACIÓN:**

Si ves esto, **¡LO ENCONTRASTE!**:

```
ℹ️  ¿Por qué estos porcentajes?
─────────────────────────────────
📊 Forma reciente: ...
🏠 Rendimiento local: ...
✈️ Rendimiento visitante: ...
🔄 H2H: ...
```

---

**Dashboard:** http://localhost:5000  
**Última actualización:** 21 de Octubre, 2025  
**Estado:** ✅ Funcionando con justificación integrada
