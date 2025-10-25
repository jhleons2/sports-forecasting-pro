# MEJORAS DE EFICIENCIA DE CONVERSIÓN - IMPLEMENTADAS

## Problema Identificado

El modelo estaba prediciendo basándose principalmente en xG (expected goals), pero no consideraba la **eficiencia de conversión** de cada equipo (cuán bien convierten las oportunidades en goles reales).

### Ejemplos del Problema:

**Chelsea vs Brighton:**
- Predicho: Chelsea 1.52 xG (prob: 37.7%) vs Brighton 1.22 xG (prob: 30.0%)
- Resultado Real: Chelsea 1-3 Brighton
- **Problema**: Chelsea tenía más xG pero perdió por ineficiencia

**Man United vs Brighton:**
- Predicho: Man United 1.08 xG (prob: 19.3%) vs Brighton 1.70 xG (prob: 56.5%)
- Resultado Real: Man United 2-0 Brighton
- **Problema**: Brighton tenía mucho más xG pero Man United fue más eficiente

## Solución Implementada

### 1. Nuevo Módulo: `src/features/eficiencia_conversion.py`

**Funcionalidad:**
- Calcula el ratio de eficiencia (goles reales / xG) para cada equipo
- Analiza los últimos 10 partidos para obtener tendencias recientes
- Aplica ajustes moderados a las predicciones xG

**Características:**
- Ratio de eficiencia: Indica si un equipo convierte mejor o peor que su xG
- Ventana temporal: Últimos 10 partidos para capturar forma reciente
- Ajuste moderado: Solo 30% del impacto total para evitar sobreajuste
- Límites de seguridad: Ratio entre 0.8 y 1.3

### 2. Integración en el Predictor

**Archivo modificado:** `scripts/predictor_corregido_simple.py`

**Cambios:**
```python
# Después de calcular xG inicial con Dixon-Coles
home_goals, away_goals = self._intensity(row)

# NUEVA MEJORA: Ajustar según eficiencia histórica
eficiencia_home = analizador_eficiencia.calcular_eficiencia_equipo(
    self.df_historico, home_mapeado, ventana_partidos=10
)
eficiencia_away = analizador_eficiencia.calcular_eficiencia_equipo(
    self.df_historico, away_mapeado, ventana_partidos=10
)

# Aplicar ajuste
home_goals, away_goals = analizador_eficiencia.aplicar_ajuste_eficiencia(
    home_goals, away_goals, eficiencia_home, eficiencia_away
)
```

## Cómo Funciona

### Ejemplo: Man United

**Sin ajuste de eficiencia:**
- xG predicho: 1.08
- Probabilidad victoria: 19.3%

**Con ajuste de eficiencia (si ratio = 1.2):**
- xG ajustado: 1.08 × 1.06 = 1.14 (aumento de ~6%)
- Probabilidad victoria ajustada: ~25-30%
- **Resultado**: Mayor probabilidad para equipos eficientes

### Factor de Ajuste Moderado

El ajuste se aplica con **30% del impacto total** para evitar cambios extremos:

```python
ajuste = 1.0 + (ratio_eficiencia - 1.0) * 0.3
```

**Ejemplos:**
- Equipo con ratio 1.2 → ajuste de solo 6% (1.0 + 0.2 * 0.3)
- Equipo con ratio 0.8 → ajuste de solo -6% (1.0 + (-0.2) * 0.3)
- Equipo con ratio 1.0 → sin ajuste

## Beneficios Esperados

### 1. Mejor Captura de Equipos Eficientes
- Identifica equipos que puntúan más goles de los esperados
- Ayuda a predecir sorpresas cuando un equipo eficiente se enfrenta a uno ineficiente

### 2. Consideración de Forma Reciente
- Solo usa últimos 10 partidos (forma reciente)
- Captura cambios en el rendimiento ofensivo
- Detecta equipos en racha (buena o mala)

### 3. Ajuste Moderado y Seguro
- No sobreajusta las predicciones
- Mantiene el equilibrio entre xG y eficiencia
- Límites de seguridad previenen ajustes extremos

## Limitaciones Actuales

1. **Requiere datos históricos**: Necesita resultados de partidos previos
2. **Sin datos de xG real**: Usa aproximaciones cuando no hay datos
3. **Ventana fija**: 10 partidos puede no ser óptimo para todos los casos

## Próximas Mejoras Posibles

1. **Factor dinámico**: Ajustar el 30% según la confianza en los datos
2. **Ventana adaptativa**: Más partidos para equipos con menos datos
3. **Eficiencia local/visitante**: Ratios separados para casa y fuera
4. **Eficiencia vs rivales específicos**: H2H mejorado

## Resultados Esperados

- **Precisión general**: Aumento esperado del 2-5% en hit-rate
- **Equipos eficientes**: Mejor predicción de victorias de equipos con alta eficiencia
- **Equipos ineficientes**: Detección de equipos que marcan menos de lo esperado

## Testing

Para probar las mejoras:

```python
# Ejecutar predictor con las mejoras
predictor = PredictorCorregidoSimple()
result = predictor.predict_con_reglas_dinamicas('Man United', 'Brighton', 'E0')

# Verificar que se aplicó el ajuste de eficiencia
# (debería aparecer en el output: [Ajuste de eficiencia aplicado])
```

## Conclusión

Esta mejora introduce el análisis de **eficiencia de conversión** como factor adicional en las predicciones, complementando el análisis de xG con la capacidad real de los equipos para convertir oportunidades en goles. Esto debería mejorar especialmente las predicciones en partidos donde hay disparidades significativas en eficiencia entre los equipos.
