# 🏆 Guía Completa: Scraping de Datos Deportivos

## 📋 Índice
1. [Fuentes Recomendadas](#fuentes-recomendadas)
2. [Aspectos Legales](#aspectos-legales)
3. [Implementación Técnica](#implementación-técnica)
4. [Comparativa de Fuentes](#comparativa-de-fuentes)
5. [Mejores Prácticas](#mejores-prácticas)

---

## 🎯 Fuentes Recomendadas

### ✅ TIER 1: APIs Oficiales (Recomendado)

#### 1. **Football-Data.co.uk** (Ya implementado)
- **URL**: https://www.football-data.co.uk/
- **Método**: Descarga directa HTTP (CSV)
- **Costo**: 🆓 100% Gratuito
- **Legalidad**: ✅ Completamente legal
- **Datos**:
  - Top-20 ligas europeas
  - Resultados históricos desde 1993
  - Odds de apertura y cierre (Bet365, Pinnacle)
  - Actualización: Semanal

**Implementación actual:**
```bash
make fd  # Descarga automática
```

---

#### 2. **API-FOOTBALL (RapidAPI)** (Ya implementado)
- **URL**: https://rapidapi.com/api-sports/api/api-football
- **Método**: API REST
- **Costo**: 
  - 🆓 Gratis: 100 req/día
  - 💰 Pro: $30/mes (3,000 req/día)
- **Legalidad**: ✅ Completamente legal
- **Datos**:
  - 1000+ ligas (incluye LATAM)
  - Fixtures en tiempo real
  - Odds de múltiples casas
  - Estadísticas de equipos/jugadores

**Implementación actual:**
```bash
# Configurar en .env:
# API_FOOTBALL_KEY=tu_clave

make dimayor_api  # Colombia
```

---

#### 3. **The Odds API** (Módulo creado)
- **URL**: https://the-odds-api.com/
- **Método**: API REST
- **Costo**:
  - 🆓 Gratis: 500 req/mes (solo odds actuales)
  - 💰 Starter: $50/mes (históricos limitados)
  - 💰 Pro: $200+/mes (históricos completos)
- **Legalidad**: ✅ Completamente legal
- **Datos**:
  - Odds actuales de 50+ casas
  - Snapshots históricos (plan pago)
  - Pinnacle, Bet365, Betfair, etc.
  - Closing odds para CLV

**Uso:**
```python
from src.etl.the_odds_api import get_odds

# Configurar THE_ODDS_API_KEY en .env
odds = get_odds("soccer_england_epl", markets="h2h")
```

---

### ⚠️ TIER 2: Scraping Tolerado (Educativo/Personal)

#### 4. **FBref** (NUEVO - Implementado)
- **URL**: https://fbref.com/
- **Método**: Web Scraping (pandas.read_html)
- **Costo**: 🆓 Gratis
- **Legalidad**: ✅ Permitido con rate limiting
- **Rate Limit**: 15-20 requests/minuto
- **Datos**:
  - Estadísticas avanzadas (xG, xA, presión)
  - 100+ ligas desde 2017
  - Datos de jugadores y equipos
  - Métricas de pases, defensivas, tiros

**Uso:**
```bash
# Temporada actual (Top-5)
make fbref

# Temporada específica
python -m src.etl.fbref_scraper --leagues EPL --season 2023-2024

# Todas las ligas disponibles
python -m src.etl.fbref_scraper --leagues EPL La_Liga Bundesliga Serie_A Ligue_1
```

**Datos descargados:**
- `data/raw/fbref/EPL_latest_table.csv` - Tabla de posiciones
- `data/raw/fbref/EPL_latest_shooting.csv` - Estadísticas de tiros
- `data/raw/fbref/EPL_latest_passing.csv` - Estadísticas de pases
- `data/raw/fbref/EPL_latest_defense.csv` - Estadísticas defensivas
- `data/raw/fbref/EPL_latest_full.csv` - Todo merged

**Términos de uso:**
- Sports Reference (dueño de FBref) permite scraping educativo
- Ver: https://www.sports-reference.com/bot-traffic.html
- Requisitos:
  - Rate limiting obligatorio (<20 req/min)
  - User-Agent identificable
  - No comercial sin permiso

---

#### 5. **Understat** (Ya implementado)
- **URL**: https://understat.com/
- **Método**: Web Scraping (JSON embebido)
- **Costo**: 🆓 Gratis
- **Legalidad**: ⚠️ Zona gris (tolerado para uso personal)
- **Datos**:
  - xG (Expected Goals) por partido
  - Top-5 ligas europeas
  - Datos de jugadores
  - Shots + xG map

**Uso:**
```bash
make understat
```

**Consideraciones:**
- Scraping NO oficialmente permitido
- Usa rate limiting (0.4s delay)
- Solo uso personal/educativo
- Puede cambiar estructura HTML

---

#### 6. **Transfermarkt**
- **URL**: https://www.transfermarkt.com/
- **Método**: Web Scraping (Selenium requerido)
- **Costo**: 🆓 Gratis
- **Legalidad**: ❌ Contra Terms of Service
- **Datos**:
  - Valuaciones de jugadores
  - Transferencias históricas
  - 600+ ligas
  - Plantillas completas

**Desafíos técnicos:**
- Cloudflare agresivo
- Requiere Selenium/Playwright
- Bloqueos de IP frecuentes
- Requiere proxy rotation

**NO IMPLEMENTADO** - Alto riesgo de bloqueo

---

### 💎 TIER 3: APIs Profesionales (Enterprise)

#### 7. **Stats Perform (Opta)**
- **URL**: https://www.statsperform.com/
- **Costo**: 💎 $500-5,000/mes (empresa)
- **Datos**: Oficiales de 60+ ligas (usado por ESPN, BBC)

#### 8. **Sportradar**
- **URL**: https://sportradar.com/
- **Costo**: 💎 Enterprise (contactar ventas)
- **Datos**: Partner oficial FIFA/UEFA

#### 9. **SportsDataIO**
- **URL**: https://sportsdata.io/
- **Costo**: 💰 $50-500/mes
- **Datos**: NFL, NBA, MLB, NHL, Soccer

---

## ⚖️ Aspectos Legales

### ✅ **Permitido Legalmente**
1. **APIs oficiales con clave** (API-FOOTBALL, The Odds API)
2. **Descargas directas HTTP** (Football-Data)
3. **Scraping con permiso explícito** (FBref educativo)
4. **Datos públicos sin ToS restrictivos**

### ⚠️ **Zona Gris**
1. **Scraping de sitios que no prohíben explícitamente** (Understat)
2. **Uso personal/educativo de datos públicos**
3. **Scraping con rate limiting respetuoso**

**Recomendación:** OK para proyectos personales/educativos. NO redistribuir.

### ❌ **Prohibido / Alto Riesgo**
1. **Scraping contra Terms of Service** (Transfermarkt)
2. **Burlar medidas anti-bot** (Cloudflare bypass)
3. **Uso comercial de datos scraped sin permiso**
4. **Rate limiting agresivo (DoS)**

---

## 🛠️ Implementación Técnica

### Rate Limiting (CRÍTICO)

#### Opción 1: Sleep manual
```python
import time

time.sleep(3)  # 3 segundos entre requests
response = requests.get(url)
```

#### Opción 2: Decorator de rate limiting
```python
from ratelimit import limits, sleep_and_retry

@sleep_and_retry
@limits(calls=15, period=60)  # 15 calls por minuto
def fetch_data(url):
    return requests.get(url)
```

#### Opción 3: Backoff exponencial
```python
import backoff

@backoff.on_exception(backoff.expo, requests.exceptions.RequestException, max_tries=3)
def fetch_with_retry(url):
    return requests.get(url)
```

---

### User-Agent (IMPORTANTE)

```python
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml',
    'Accept-Language': 'en-US,en;q=0.9',
}

response = requests.get(url, headers=headers)
```

---

### Manejo de Errores

```python
def safe_scrape(url, max_retries=3):
    for i in range(max_retries):
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return response
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:  # Too Many Requests
                wait_time = 2 ** i * 60  # Exponential backoff
                print(f"Rate limited. Esperando {wait_time}s...")
                time.sleep(wait_time)
            elif e.response.status_code == 403:  # Forbidden
                print("❌ Bloqueado. Considera usar proxy.")
                break
            else:
                raise
        except requests.exceptions.Timeout:
            print(f"⏱️ Timeout. Reintento {i+1}/{max_retries}")
            time.sleep(5)
    return None
```

---

### Proxy Rotation (Para sitios restrictivos)

```python
import random

PROXIES = [
    'http://proxy1.com:8080',
    'http://proxy2.com:8080',
    'http://proxy3.com:8080',
]

def get_with_proxy(url):
    proxy = random.choice(PROXIES)
    proxies = {'http': proxy, 'https': proxy}
    return requests.get(url, proxies=proxies)
```

---

## 📊 Comparativa de Fuentes

| Fuente | Método | Costo | Legalidad | Dificultad | Calidad | Rate Limit |
|--------|--------|-------|-----------|------------|---------|------------|
| **Football-Data** | HTTP | 🆓 | ✅ Legal | ⭐ | ⭐⭐⭐⭐⭐ | Sin límite |
| **FBref** | Scraping | 🆓 | ✅ Permitido | ⭐⭐ | ⭐⭐⭐⭐⭐ | 20/min |
| **Understat** | Scraping | 🆓 | ⚠️ Gris | ⭐⭐ | ⭐⭐⭐⭐⭐ | Manual |
| **API-FOOTBALL** | API | $30/mes | ✅ Legal | ⭐ | ⭐⭐⭐⭐ | 100/día gratis |
| **The Odds API** | API | $50/mes | ✅ Legal | ⭐ | ⭐⭐⭐⭐⭐ | 500/mes gratis |
| **Transfermarkt** | Scraping | 🆓 | ❌ Prohibido | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Cloudflare |
| **Sportradar** | API | $1K+/mes | ✅ Legal | ⭐ | ⭐⭐⭐⭐⭐ | Alto |

---

## 🎓 Mejores Prácticas

### 1. **Jerarquía de Decisión**
```
¿Hay API oficial? → Úsala (siempre preferible)
  ↓ NO
¿Los Terms permiten scraping? → Scrape con rate limiting
  ↓ NO
¿Es zona gris? → Solo uso personal + rate limiting conservador
  ↓ NO
❌ NO scrapear (riesgo legal/técnico alto)
```

### 2. **Rate Limiting Recomendado**

| Tipo de Sitio | Delay Recomendado |
|--------------|-------------------|
| APIs oficiales | Según documentación |
| Sitios que permiten scraping | 3-5 segundos |
| Zona gris | 5-10 segundos |
| Sitios restrictivos | 10-30 segundos + proxy |

### 3. **Almacenamiento en Caché**
```python
import pickle
from pathlib import Path

def get_cached_or_fetch(url, cache_file, max_age_hours=24):
    cache = Path(cache_file)
    if cache.exists():
        age = time.time() - cache.stat().st_mtime
        if age < max_age_hours * 3600:
            return pickle.load(cache.open('rb'))
    
    data = fetch_data(url)
    pickle.dump(data, cache.open('wb'))
    return data
```

### 4. **Respeta robots.txt**
```python
from urllib.robotparser import RobotFileParser

def can_scrape(url):
    rp = RobotFileParser()
    rp.set_url(f"{url}/robots.txt")
    rp.read()
    return rp.can_fetch("*", url)
```

### 5. **Logging y Monitoreo**
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraping.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

logger.info(f"Scraping {url}")
logger.warning(f"Rate limited en {url}")
logger.error(f"Error scraping {url}: {e}")
```

---

## 🚀 Recomendación para tu Proyecto

### **Setup Actual (Óptimo para empezar):**
```bash
# 1. Top-5 Ligas Europeas (GRATIS, LEGAL)
make all_fd

# 2. xG metrics (GRATIS, uso educativo)
make understat

# 3. Estadísticas avanzadas (GRATIS, LEGAL) [NUEVO]
make fbref

# 4. Dashboard
make dashboard
```

### **Upgrade Recomendado ($30-50/mes):**
```bash
# En .env:
API_FOOTBALL_KEY=...  # $30/mes para LATAM
THE_ODDS_API_KEY=...  # $50/mes para closing odds

# Ejecutar:
make all_dimayor  # Colombia
make clv          # Closing Line Value
make alerts       # Picks de valor
```

---

## 📚 Recursos Adicionales

### Librerías Útiles
```bash
pip install requests beautifulsoup4 lxml
pip install ratelimit backoff
pip install selenium playwright  # Para sitios JS-heavy
pip install pandas  # Para read_html directo
```

### Documentación
- FBref ToS: https://www.sports-reference.com/bot-traffic.html
- robots.txt spec: https://developers.google.com/search/docs/advanced/robots/intro
- HTTP status codes: https://httpstatuses.com/

### Comunidades
- r/webscraping (Reddit)
- Stack Overflow [web-scraping tag]
- GitHub Topics: #sports-data #web-scraping

---

## ⚠️ Disclaimer Legal

Este proyecto es para **uso educativo/personal únicamente**. 

- **NO redistribuir datos scraped comercialmente**
- **Respetar Terms of Service de cada sitio**
- **Usar rate limiting apropiado**
- **Atribuir fuentes en análisis públicos**

El autor no se hace responsable del uso indebido de estas herramientas.

---

**Última actualización**: Octubre 2025  
**Mantenedor**: Sports Forecasting PRO

