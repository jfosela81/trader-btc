# 🤖 Bitcoin Trading Bot

Bot de trading algorítmico para Bitcoin con paper trading, estrategias configurables y dashboard web.

## 🎯 Características

- **Paper Trading**: Prueba estrategias sin arriesgar dinero real
- **Múltiples fuentes de datos**: Binance y CoinGecko como fallback
- **Estrategias configurables**: SMA Crossover, RSI, MACD (en desarrollo)
- **Gestión de riesgo**: Stop Loss, Take Profit, límites diarios
- **Dashboard web**: Visualiza rendimiento en tiempo real
- **GitHub Actions**: Ejecución automática cada 15 minutos (gratis)

## 📁 Estructura del proyecto

```
trader-btc/
├── .github/workflows/     # GitHub Actions para producción
├── backend/
│   ├── src/
│   │   ├── data/          # Fetchers de precios
│   │   ├── strategies/    # Estrategias de trading
│   │   ├── engine/        # Motor de paper trading
│   │   └── utils/         # Helpers
│   └── requirements.txt
├── frontend/              # Dashboard Next.js (próximamente)
└── README.md
```

## 🚀 Inicio rápido

### 1. Clonar y configurar entorno

```bash
cd trader-btc
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r backend/requirements.txt
```

### 2. Configurar variables de entorno

```bash
cp .env.example .env
# Editar .env con tus credenciales de Supabase
```

### 3. Ejecutar el bot

```bash
cd backend/src
python main.py
```

## ⚙️ Configuración

| Variable | Descripción | Default |
|----------|-------------|---------|
| `SUPABASE_URL` | URL de tu proyecto Supabase | - |
| `SUPABASE_KEY` | Clave anon de Supabase | - |
| `INITIAL_BALANCE_USD` | Balance inicial simulado | 1000 |
| `TRADING_FEE_PERCENT` | Fee por operación (%) | 0.1 |
| `DRY_RUN` | Paper trading activado | true |

## 📊 Estrategias disponibles

### SMA Crossover (en desarrollo)
Compra cuando la media móvil corta (ej: 10 períodos) cruza por encima de la larga (ej: 50 períodos). Vende cuando cruza por debajo.

### RSI (próximamente)
Compra en sobreventa (RSI < 30), vende en sobrecompra (RSI > 70).

## ⚠️ Disclaimer

Este bot es para **fines educativos**. El trading de criptomonedas conlleva riesgos significativos. No inviertas dinero que no puedas permitirte perder.

## 📝 Licencia

MIT
