"""
Base class para estrategias de trading
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Optional, List
from datetime import datetime


class Signal(Enum):
    """Señales de trading"""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


@dataclass
class TradeSignal:
    """Resultado del análisis de una estrategia"""
    signal: Signal
    strategy_name: str
    timestamp: datetime
    price: float
    confidence: float  # 0.0 a 1.0
    reason: str
    
    def __str__(self):
        emoji = {"buy": "🟢", "sell": "🔴", "hold": "⚪"}
        return f"{emoji[self.signal.value]} {self.signal.value.upper()} | {self.strategy_name} | Confianza: {self.confidence:.0%} | {self.reason}"


class BaseStrategy(ABC):
    """Clase base para todas las estrategias de trading"""
    
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    def analyze(self, prices: List[float], current_price: float) -> TradeSignal:
        """
        Analiza los precios y genera una señal de trading.
        
        Args:
            prices: Lista de precios históricos (del más antiguo al más reciente)
            current_price: Precio actual
            
        Returns:
            TradeSignal con la recomendación
        """
        pass
    
    def _calculate_sma(self, prices: List[float], period: int) -> Optional[float]:
        """Calcula la media móvil simple"""
        if len(prices) < period:
            return None
        return sum(prices[-period:]) / period
    
    def _calculate_ema(self, prices: List[float], period: int) -> Optional[float]:
        """Calcula la media móvil exponencial"""
        if len(prices) < period:
            return None
        
        multiplier = 2 / (period + 1)
        ema = prices[0]
        
        for price in prices[1:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
        
        return ema
    
    def _calculate_rsi(self, prices: List[float], period: int = 14) -> Optional[float]:
        """Calcula el RSI (Relative Strength Index)"""
        if len(prices) < period + 1:
            return None
        
        gains = []
        losses = []
        
        for i in range(1, len(prices)):
            change = prices[i] - prices[i-1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
