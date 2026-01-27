"""
Estrategia SMA Crossover (Cruce de Medias Móviles)

Lógica:
- COMPRAR: Cuando la SMA corta cruza POR ENCIMA de la SMA larga (tendencia alcista)
- VENDER: Cuando la SMA corta cruza POR DEBAJO de la SMA larga (tendencia bajista)
- HOLD: Cuando no hay cruce o no hay suficientes datos

Parámetros típicos:
- SMA corta: 10-20 períodos
- SMA larga: 50-200 períodos
"""

from typing import List
from datetime import datetime

try:
    from .base import BaseStrategy, TradeSignal, Signal
except ImportError:
    from base import BaseStrategy, TradeSignal, Signal


class SMACrossoverStrategy(BaseStrategy):
    """
    Estrategia de cruce de medias móviles simples (SMA Crossover).
    
    Una de las estrategias más básicas y probadas en trading algorítmico.
    Funciona mejor en mercados con tendencia clara.
    """
    
    def __init__(self, short_period: int = 10, long_period: int = 50):
        """
        Args:
            short_period: Período de la SMA corta (más sensible)
            long_period: Período de la SMA larga (más estable)
        """
        super().__init__(f"SMA Crossover ({short_period}/{long_period})")
        self.short_period = short_period
        self.long_period = long_period
        
        # Estado para detectar cruces
        self._last_short_above_long = None
    
    def analyze(self, prices: List[float], current_price: float) -> TradeSignal:
        """
        Analiza precios históricos y genera señal basada en cruce de SMAs.
        """
        # Verificar que tenemos suficientes datos
        min_required = self.long_period + 2  # +2 para detectar cruce
        if len(prices) < min_required:
            return TradeSignal(
                signal=Signal.HOLD,
                strategy_name=self.name,
                timestamp=datetime.now(),
                price=current_price,
                confidence=0.0,
                reason=f"Datos insuficientes: {len(prices)}/{min_required} velas requeridas"
            )
        
        # Calcular SMAs actuales y anteriores
        sma_short = self._calculate_sma(prices, self.short_period)
        sma_long = self._calculate_sma(prices, self.long_period)
        
        # SMAs del período anterior (para detectar cruce)
        prices_prev = prices[:-1]
        sma_short_prev = self._calculate_sma(prices_prev, self.short_period)
        sma_long_prev = self._calculate_sma(prices_prev, self.long_period)
        
        if None in [sma_short, sma_long, sma_short_prev, sma_long_prev]:
            return TradeSignal(
                signal=Signal.HOLD,
                strategy_name=self.name,
                timestamp=datetime.now(),
                price=current_price,
                confidence=0.0,
                reason="No se pudieron calcular las SMAs"
            )
        
        # Estado actual: ¿SMA corta está por encima de la larga?
        short_above_long = sma_short > sma_long
        short_above_long_prev = sma_short_prev > sma_long_prev
        
        # Calcular fuerza de la señal (distancia entre SMAs)
        sma_diff_percent = abs(sma_short - sma_long) / sma_long * 100
        confidence = min(sma_diff_percent / 2, 1.0)  # Máx 1.0 cuando diff >= 2%
        
        # Detectar cruces
        if short_above_long and not short_above_long_prev:
            # GOLDEN CROSS: SMA corta cruza hacia arriba
            return TradeSignal(
                signal=Signal.BUY,
                strategy_name=self.name,
                timestamp=datetime.now(),
                price=current_price,
                confidence=confidence,
                reason=f"Golden Cross: SMA{self.short_period} (${sma_short:,.0f}) cruzó por encima de SMA{self.long_period} (${sma_long:,.0f})"
            )
        
        elif not short_above_long and short_above_long_prev:
            # DEATH CROSS: SMA corta cruza hacia abajo
            return TradeSignal(
                signal=Signal.SELL,
                strategy_name=self.name,
                timestamp=datetime.now(),
                price=current_price,
                confidence=confidence,
                reason=f"Death Cross: SMA{self.short_period} (${sma_short:,.0f}) cruzó por debajo de SMA{self.long_period} (${sma_long:,.0f})"
            )
        
        else:
            # Sin cruce - mantener posición
            position = "alcista" if short_above_long else "bajista"
            return TradeSignal(
                signal=Signal.HOLD,
                strategy_name=self.name,
                timestamp=datetime.now(),
                price=current_price,
                confidence=confidence,
                reason=f"Sin cruce. Tendencia {position}. SMA{self.short_period}: ${sma_short:,.0f} | SMA{self.long_period}: ${sma_long:,.0f}"
            )
    
    def get_sma_values(self, prices: List[float]) -> dict:
        """Devuelve los valores actuales de las SMAs para debugging/display"""
        return {
            f"sma_{self.short_period}": self._calculate_sma(prices, self.short_period),
            f"sma_{self.long_period}": self._calculate_sma(prices, self.long_period),
        }


# Test de la estrategia
if __name__ == "__main__":
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from data.price_fetcher import PriceFetcher
    
    print("=" * 60)
    print("Testing SMA Crossover Strategy")
    print("=" * 60)
    
    # Obtener datos históricos
    fetcher = PriceFetcher()
    print("\n📊 Obteniendo datos históricos (100 velas de 1h)...")
    historical = fetcher.get_historical_prices(interval="1h", limit=100)
    
    # Extraer precios de cierre
    prices = [candle.close for candle in historical]
    current_price = prices[-1]
    
    print(f"✅ Obtenidos {len(prices)} precios")
    print(f"   Rango: ${min(prices):,.0f} - ${max(prices):,.0f}")
    print(f"   Precio actual: ${current_price:,.2f}")
    
    # Crear y ejecutar estrategia
    strategy = SMACrossoverStrategy(short_period=10, long_period=50)
    signal = strategy.analyze(prices, current_price)
    
    print(f"\n📈 Resultado del análisis:")
    print(f"   {signal}")
    
    # Mostrar valores SMA
    smas = strategy.get_sma_values(prices)
    print(f"\n📊 Valores SMA:")
    for name, value in smas.items():
        if value:
            print(f"   {name}: ${value:,.2f}")
