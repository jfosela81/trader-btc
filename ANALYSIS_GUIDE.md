# Guía de Análisis del Trading Bot

## Cómo pedirle a Claude que analice los datos

Cuando quieras revisar el rendimiento del bot, simplemente di:

> "Analiza los resultados del bot de trading"

o

> "Ejecuta el análisis del bot y dame recomendaciones"

Claude se conectará a Supabase, analizará todos los trades y snapshots, y te dará:

1. **Métricas de rendimiento**
   - Win rate (% de trades ganadores)
   - Profit factor (ganancias / pérdidas)
   - P&L total

2. **Comparación vs HOLD**
   - ¿El bot rinde mejor que simplemente comprar y mantener BTC?

3. **Análisis de riesgo**
   - Drawdown máximo (peor racha de pérdidas)

4. **Recomendaciones de mejora**
   - Ajustes a parámetros SMA
   - Nuevos indicadores a añadir
   - Cambios en gestión de riesgo

---

## Ejecutar el análisis manualmente

Si quieres ejecutar el análisis tú mismo:

```bash
cd /Users/jorgefosela/MyApps/trader-btc
source venv/bin/activate
cd backend/src
python analysis/analyzer.py
```

---

## Frecuencia recomendada de análisis

| Fase | Frecuencia |
|------|------------|
| Primeras semanas | Cada 3-5 días |
| Mes 1-2 | Semanal |
| Mes 3+ | Cada 2 semanas |

---

## Métricas objetivo antes de usar dinero real

- [ ] Mínimo 50-100 trades ejecutados
- [ ] Win rate > 55%
- [ ] Profit factor > 1.5
- [ ] Drawdown máximo < 15%
- [ ] Bot supera a HOLD en al menos 2 de 3 meses
- [ ] Ganancias > 3x los fees pagados

---

## Historial de análisis

*(Añadir aquí notas de cada sesión de análisis)*

### Fecha: ____
- Trades totales: 
- Win rate: 
- P&L: 
- Recomendaciones aplicadas:
- Próxima revisión:

---

## Mejoras implementadas

| Fecha | Cambio | Resultado |
|-------|--------|-----------|
| (inicial) | SMA 10/50, 50% posición | Baseline |

