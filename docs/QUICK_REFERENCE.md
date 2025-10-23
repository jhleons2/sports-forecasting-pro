# 🚀 Referencia Rápida: Scraping Deportivo

## 🏆 Top 3 Recomendaciones

### 1️⃣ **FBref** (MEJOR para comenzar)
```bash
# ✅ GRATIS | ✅ LEGAL | ⭐⭐⭐⭐⭐ Calidad
make fbref

# Obtienes:
# - Estadísticas avanzadas (xG, presión, pases)
# - 100+ ligas desde 2017
# - Rate limit: 15-20 req/min
```

**Por qué elegirlo:**
- Legalmente permitido (ver ToS)
- Datos estructurados (pandas.read_html directo)
- Complementa perfectamente Football-Data
- Ideal para features de ML

---

### 2️⃣ **Football-Data.co.uk** (Ya lo usas)
```bash
# ✅ GRATIS | ✅ LEGAL | Sin límites
make fd

# Obtienes:
# - Resultados históricos Top-20 ligas
# - Odds de cierre (Pinnacle, Bet365)
# - Perfecto para backtesting
```

**Por qué es perfecto:**
- Descarga directa HTTP (no scraping)
- Incluye closing odds para CLV
- Datos desde 1993

---

### 3️⃣ **API-FOOTBALL** (Para LATAM)
```bash
# 💰 $30/mes | ✅ LEGAL | 1000+ ligas
# Configurar API_FOOTBALL_KEY en .env
make dimayor_api

# Obtienes:
# - Ligas de América Latina
# - Datos en tiempo real
# - Odds de múltiples casas
```

**Cuándo usarlo:**
- Necesitas ligas fuera de Europa
- Quieres datos en tiempo real
- Plan gratuito: 100 req/día (para testing)

---

## 📊 Comparativa Rápida

| Fuente | Costo | Legalidad | Mejor Para |
|--------|-------|-----------|------------|
| **FBref** | 🆓 | ✅ | Estadísticas avanzadas |
| **Football-Data** | 🆓 | ✅ | Backtesting + Odds |
| **Understat** | 🆓 | ⚠️ | xG metrics |
| **API-FOOTBALL** | $30 | ✅ | LATAM + Real-time |
| **The Odds API** | $50 | ✅ | Closing odds |

---

## 🎯 Casos de Uso

### Proyecto Personal (GRATIS)
```bash
make all_fd      # Europa
make understat   # xG
make fbref       # Stats avanzadas
make dashboard
```

### Producción Colombia ($30/mes)
```bash
# .env: API_FOOTBALL_KEY=...
make all_dimayor
make alerts  # Telegram picks
```

### Profesional ($80/mes)
```bash
# .env: API_FOOTBALL_KEY + THE_ODDS_API_KEY
make all_dimayor
make clv     # Closing Line Value
make alerts
```

---

## ⚠️ Evitar

❌ **Transfermarkt** - Cloudflare agresivo, contra ToS  
❌ **Scraping agresivo** - Respeta rate limits  
❌ **Redistribución comercial** - Solo uso personal

---

## 📖 Ver Guía Completa

Para detalles técnicos completos: [`docs/SCRAPING_GUIDE.md`](./SCRAPING_GUIDE.md)

