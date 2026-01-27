"""
Bitcoin Trading Bot - Punto de entrada principal

Ejecuta un ciclo de trading:
1. Obtiene precio actual y histórico
2. Analiza con estrategia(s) configuradas
3. Ejecuta trade si hay señal (paper trading)
4. Guarda resultados
"""

import sys
import os
from datetime import datetime
from pathlib import Path

# Añadir src al path para imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data.price_fetcher import PriceFetcher
from strategies.sma_crossover import SMACrossoverStrategy
from strategies.base import Signal
from engine.paper_trading import PaperTradingEngine
from config import get_trading_config, get_bot_config


# Archivo para persistir estado del bot
STATE_FILE = Path(__file__).parent.parent / "data" / "bot_state.json"


def ensure_data_dir():
    """Asegura que existe el directorio de datos"""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)


def run_trading_cycle():
    """
    Ejecuta un ciclo completo de trading.
    """
    print(f"\n{'='*60}")
    print(f"🤖 BITCOIN TRADING BOT - Ciclo iniciado")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    # Cargar configuración
    trading_config = get_trading_config()
    bot_config = get_bot_config()
    
    mode = "PAPER TRADING (simulado)" if trading_config.dry_run else "⚠️  TRADING REAL"
    print(f"⚙️  Modo: {mode}")
    
    # Inicializar o cargar motor de paper trading
    ensure_data_dir()
    engine = PaperTradingEngine(
        initial_usd=trading_config.initial_balance_usd,
        fee_percent=trading_config.trading_fee_percent
    )
    
    if STATE_FILE.exists():
        try:
            engine.load_state(str(STATE_FILE))
        except Exception as e:
            print(f"⚠️  No se pudo cargar estado anterior: {e}")
            print(f"   Iniciando con balance fresco: ${trading_config.initial_balance_usd}")
    else:
        print(f"💰 Balance inicial: ${trading_config.initial_balance_usd:,.2f}")
    
    # Obtener precio actual
    print(f"\n📊 Obteniendo datos de mercado...")
    fetcher = PriceFetcher(primary_source=bot_config.primary_price_source)
    
    try:
        # Precio actual
        price_data = fetcher.get_price()
        current_price = price_data.price
        print(f"✅ Precio BTC: ${current_price:,.2f} ({price_data.source})")
        
        if price_data.change_24h_percent:
            emoji = "📈" if price_data.change_24h_percent > 0 else "📉"
            print(f"   Cambio 24h: {emoji} {price_data.change_24h_percent:+.2f}%")
        
        # Obtener precios históricos para análisis
        print(f"\n📈 Obteniendo datos históricos...")
        historical = fetcher.get_historical_prices(interval="1h", limit=100)
        prices = [candle.close for candle in historical]
        print(f"   Obtenidas {len(prices)} velas (1h)")
        
        # Ejecutar estrategia
        print(f"\n🎯 Analizando con estrategia SMA Crossover...")
        strategy = SMACrossoverStrategy(short_period=10, long_period=50)
        signal = strategy.analyze(prices, current_price)
        print(f"   {signal}")
        
        # Mostrar valores SMA
        smas = strategy.get_sma_values(prices)
        for name, value in smas.items():
            if value:
                print(f"   {name.upper()}: ${value:,.2f}")
        
        # Ejecutar trade si hay señal
        print(f"\n💱 Decisión de trading...")
        
        if signal.signal == Signal.BUY:
            # Calcular cantidad a comprar (máx 50% del balance USD)
            max_usd = engine.portfolio.usd_balance * (trading_config.max_position_percent / 100)
            if max_usd >= engine.min_trade_usd:
                print(f"   🟢 Señal de COMPRA detectada")
                engine.buy(
                    price=current_price,
                    usd_amount=max_usd,
                    strategy=strategy.name,
                    reason=signal.reason
                )
            else:
                print(f"   ⚠️  Señal BUY pero balance USD insuficiente: ${engine.portfolio.usd_balance:.2f}")
        
        elif signal.signal == Signal.SELL:
            if engine.portfolio.btc_balance > 0:
                print(f"   🔴 Señal de VENTA detectada")
                engine.sell(
                    price=current_price,
                    strategy=strategy.name,
                    reason=signal.reason
                )
            else:
                print(f"   ⚠️  Señal SELL pero no hay BTC para vender")
        
        else:
            print(f"   ⚪ HOLD - Manteniendo posición actual")
        
        # Mostrar estado del portfolio
        engine.print_summary(current_price)
        
        # Guardar estado
        print(f"\n💾 Guardando estado...")
        engine.save_state(str(STATE_FILE))
        
        print(f"\n{'='*60}")
        print(f"✅ Ciclo completado exitosamente")
        print(f"{'='*60}\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error en el ciclo de trading: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Punto de entrada principal"""
    print("\n" + "🚀 " * 15)
    print("BITCOIN TRADING BOT - v0.2.0")
    print("🚀 " * 15 + "\n")
    
    success = run_trading_cycle()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
