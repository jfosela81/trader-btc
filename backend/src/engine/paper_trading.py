"""
Motor de Paper Trading (Trading Simulado)

Simula operaciones de compra/venta sin dinero real.
Incluye:
- Balance virtual (USD y BTC)
- Simulación de fees
- Historial de trades
- Cálculo de P&L
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from enum import Enum
import json
import sys
import os

# Para imports del proyecto
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from data.supabase_client import get_supabase
except ImportError:
    get_supabase = None


class TradeType(Enum):
    BUY = "buy"
    SELL = "sell"


@dataclass
class Trade:
    """Registro de un trade ejecutado"""
    id: int
    timestamp: datetime
    type: TradeType
    price: float
    btc_amount: float
    usd_amount: float
    fee_usd: float
    balance_usd_after: float
    balance_btc_after: float
    strategy: str
    reason: str
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "type": self.type.value,
            "price": self.price,
            "btc_amount": self.btc_amount,
            "usd_amount": self.usd_amount,
            "fee_usd": self.fee_usd,
            "balance_usd_after": self.balance_usd_after,
            "balance_btc_after": self.balance_btc_after,
            "strategy": self.strategy,
            "reason": self.reason
        }


@dataclass
class Portfolio:
    """Estado actual del portfolio"""
    usd_balance: float
    btc_balance: float
    initial_usd: float
    
    def total_value_usd(self, btc_price: float) -> float:
        """Valor total en USD"""
        return self.usd_balance + (self.btc_balance * btc_price)
    
    def pnl_usd(self, btc_price: float) -> float:
        """Ganancia/Pérdida en USD"""
        return self.total_value_usd(btc_price) - self.initial_usd
    
    def pnl_percent(self, btc_price: float) -> float:
        """Ganancia/Pérdida en porcentaje"""
        return (self.pnl_usd(btc_price) / self.initial_usd) * 100
    
    def to_dict(self, btc_price: float) -> dict:
        return {
            "usd_balance": self.usd_balance,
            "btc_balance": self.btc_balance,
            "total_value_usd": self.total_value_usd(btc_price),
            "pnl_usd": self.pnl_usd(btc_price),
            "pnl_percent": self.pnl_percent(btc_price)
        }


class PaperTradingEngine:
    """
    Motor de paper trading para simular operaciones.
    Guarda trades en Supabase si está configurado.
    """
    
    def __init__(self, 
                 initial_usd: float = 1000.0,
                 fee_percent: float = 0.1,
                 min_trade_usd: float = 10.0,
                 use_supabase: bool = True):
        """
        Args:
            initial_usd: Balance inicial en USD
            fee_percent: Comisión por trade (0.1 = 0.1%)
            min_trade_usd: Mínimo USD por operación
            use_supabase: Si True, guarda trades en Supabase
        """
        self.portfolio = Portfolio(
            usd_balance=initial_usd,
            btc_balance=0.0,
            initial_usd=initial_usd
        )
        self.fee_percent = fee_percent
        self.min_trade_usd = min_trade_usd
        self.trades: List[Trade] = []
        self._trade_counter = 0
        
        # Métricas
        self.winning_trades = 0
        self.losing_trades = 0
        self.last_buy_price: Optional[float] = None
        
        # Supabase
        self.supabase = None
        if use_supabase and get_supabase is not None:
            self.supabase = get_supabase()
    
    def buy(self, 
            price: float, 
            usd_amount: Optional[float] = None,
            strategy: str = "manual",
            reason: str = "") -> Optional[Trade]:
        """
        Compra BTC con USD.
        
        Args:
            price: Precio actual de BTC
            usd_amount: Cantidad USD a gastar (None = todo el balance)
            strategy: Nombre de la estrategia que genera la orden
            reason: Razón de la compra
            
        Returns:
            Trade si se ejecutó, None si no fue posible
        """
        # Usar todo el balance si no se especifica cantidad
        if usd_amount is None:
            usd_amount = self.portfolio.usd_balance
        
        # Validaciones
        if usd_amount < self.min_trade_usd:
            print(f"⚠️  Cantidad muy pequeña: ${usd_amount:.2f} (mínimo: ${self.min_trade_usd})")
            return None
        
        if usd_amount > self.portfolio.usd_balance:
            print(f"⚠️  Balance insuficiente: ${self.portfolio.usd_balance:.2f} disponible")
            return None
        
        # Calcular fee
        fee_usd = usd_amount * (self.fee_percent / 100)
        usd_after_fee = usd_amount - fee_usd
        
        # Calcular BTC a recibir
        btc_amount = usd_after_fee / price
        
        # Ejecutar trade
        self.portfolio.usd_balance -= usd_amount
        self.portfolio.btc_balance += btc_amount
        self.last_buy_price = price
        
        # Registrar trade
        self._trade_counter += 1
        trade = Trade(
            id=self._trade_counter,
            timestamp=datetime.now(),
            type=TradeType.BUY,
            price=price,
            btc_amount=btc_amount,
            usd_amount=usd_amount,
            fee_usd=fee_usd,
            balance_usd_after=self.portfolio.usd_balance,
            balance_btc_after=self.portfolio.btc_balance,
            strategy=strategy,
            reason=reason
        )
        self.trades.append(trade)
        
        print(f"🟢 COMPRA ejecutada:")
        print(f"   Precio: ${price:,.2f}")
        print(f"   Gastado: ${usd_amount:.2f} (fee: ${fee_usd:.2f})")
        print(f"   Recibido: {btc_amount:.8f} BTC")
        print(f"   Balance: ${self.portfolio.usd_balance:.2f} USD | {self.portfolio.btc_balance:.8f} BTC")
        
        # Guardar en Supabase
        if self.supabase and self.supabase.is_connected:
            self.supabase.save_trade(trade.to_dict())
        
        return trade
    
    def sell(self,
             price: float,
             btc_amount: Optional[float] = None,
             strategy: str = "manual",
             reason: str = "") -> Optional[Trade]:
        """
        Vende BTC por USD.
        
        Args:
            price: Precio actual de BTC
            btc_amount: Cantidad BTC a vender (None = todo el balance)
            strategy: Nombre de la estrategia que genera la orden
            reason: Razón de la venta
            
        Returns:
            Trade si se ejecutó, None si no fue posible
        """
        # Usar todo el balance si no se especifica cantidad
        if btc_amount is None:
            btc_amount = self.portfolio.btc_balance
        
        # Validaciones
        if btc_amount <= 0:
            print(f"⚠️  No hay BTC para vender")
            return None
        
        if btc_amount > self.portfolio.btc_balance:
            print(f"⚠️  Balance BTC insuficiente: {self.portfolio.btc_balance:.8f} disponible")
            return None
        
        # Calcular USD bruto y fee
        usd_gross = btc_amount * price
        fee_usd = usd_gross * (self.fee_percent / 100)
        usd_net = usd_gross - fee_usd
        
        # Validar mínimo
        if usd_net < self.min_trade_usd:
            print(f"⚠️  Valor muy pequeño: ${usd_net:.2f} (mínimo: ${self.min_trade_usd})")
            return None
        
        # Ejecutar trade
        self.portfolio.btc_balance -= btc_amount
        self.portfolio.usd_balance += usd_net
        
        # Calcular si fue ganador o perdedor
        if self.last_buy_price:
            if price > self.last_buy_price:
                self.winning_trades += 1
            else:
                self.losing_trades += 1
        
        # Registrar trade
        self._trade_counter += 1
        trade = Trade(
            id=self._trade_counter,
            timestamp=datetime.now(),
            type=TradeType.SELL,
            price=price,
            btc_amount=btc_amount,
            usd_amount=usd_net,
            fee_usd=fee_usd,
            balance_usd_after=self.portfolio.usd_balance,
            balance_btc_after=self.portfolio.btc_balance,
            strategy=strategy,
            reason=reason
        )
        self.trades.append(trade)
        
        # Calcular P&L de este trade
        pnl_trade = ""
        if self.last_buy_price:
            pnl_percent = ((price - self.last_buy_price) / self.last_buy_price) * 100
            emoji = "📈" if pnl_percent > 0 else "📉"
            pnl_trade = f"\n   P&L trade: {emoji} {pnl_percent:+.2f}%"
        
        print(f"🔴 VENTA ejecutada:")
        print(f"   Precio: ${price:,.2f}")
        print(f"   Vendido: {btc_amount:.8f} BTC")
        print(f"   Recibido: ${usd_net:.2f} (fee: ${fee_usd:.2f}){pnl_trade}")
        print(f"   Balance: ${self.portfolio.usd_balance:.2f} USD | {self.portfolio.btc_balance:.8f} BTC")
        
        # Guardar en Supabase
        if self.supabase and self.supabase.is_connected:
            self.supabase.save_trade(trade.to_dict())
        
        self.last_buy_price = None
        return trade
    
    def get_stats(self, current_price: float) -> dict:
        """Obtiene estadísticas del trading"""
        total_trades = len(self.trades)
        total_fees = sum(t.fee_usd for t in self.trades)
        win_rate = (self.winning_trades / max(self.losing_trades + self.winning_trades, 1)) * 100
        
        return {
            "total_trades": total_trades,
            "winning_trades": self.winning_trades,
            "losing_trades": self.losing_trades,
            "win_rate": win_rate,
            "total_fees_paid": total_fees,
            "portfolio": self.portfolio.to_dict(current_price)
        }
    
    def print_summary(self, current_price: float):
        """Imprime resumen del estado actual"""
        stats = self.get_stats(current_price)
        portfolio = stats["portfolio"]
        
        print("\n" + "=" * 50)
        print("📊 RESUMEN DE TRADING")
        print("=" * 50)
        print(f"💰 Balance USD: ${portfolio['usd_balance']:,.2f}")
        print(f"₿  Balance BTC: {self.portfolio.btc_balance:.8f}")
        print(f"📈 Valor total: ${portfolio['total_value_usd']:,.2f}")
        
        pnl_emoji = "🟢" if portfolio['pnl_usd'] >= 0 else "🔴"
        print(f"{pnl_emoji} P&L: ${portfolio['pnl_usd']:+,.2f} ({portfolio['pnl_percent']:+.2f}%)")
        
        print(f"\n📊 Estadísticas:")
        print(f"   Trades totales: {stats['total_trades']}")
        print(f"   Ganadores: {stats['winning_trades']} | Perdedores: {stats['losing_trades']}")
        print(f"   Win rate: {stats['win_rate']:.1f}%")
        print(f"   Fees pagados: ${stats['total_fees_paid']:.2f}")
        print("=" * 50)
    
    def save_snapshot_to_supabase(self, current_price: float):
        """Guarda un snapshot del portfolio en Supabase"""
        if not self.supabase or not self.supabase.is_connected:
            return False
        
        return self.supabase.save_portfolio_snapshot(
            btc_price=current_price,
            usd_balance=self.portfolio.usd_balance,
            btc_balance=self.portfolio.btc_balance,
            total_value_usd=self.portfolio.total_value_usd(current_price),
            pnl_usd=self.portfolio.pnl_usd(current_price),
            pnl_percent=self.portfolio.pnl_percent(current_price)
        )
    
    def save_state(self, filepath: str):
        """Guarda el estado a un archivo JSON"""
        state = {
            "portfolio": {
                "usd_balance": self.portfolio.usd_balance,
                "btc_balance": self.portfolio.btc_balance,
                "initial_usd": self.portfolio.initial_usd
            },
            "trades": [t.to_dict() for t in self.trades],
            "metrics": {
                "winning_trades": self.winning_trades,
                "losing_trades": self.losing_trades,
                "last_buy_price": self.last_buy_price
            }
        }
        with open(filepath, 'w') as f:
            json.dump(state, f, indent=2)
        print(f"💾 Estado guardado en {filepath}")
    
    def load_state(self, filepath: str):
        """Carga el estado desde un archivo JSON"""
        with open(filepath, 'r') as f:
            state = json.load(f)
        
        self.portfolio.usd_balance = state["portfolio"]["usd_balance"]
        self.portfolio.btc_balance = state["portfolio"]["btc_balance"]
        self.portfolio.initial_usd = state["portfolio"]["initial_usd"]
        self.winning_trades = state["metrics"]["winning_trades"]
        self.losing_trades = state["metrics"]["losing_trades"]
        self.last_buy_price = state["metrics"]["last_buy_price"]
        
        print(f"📂 Estado cargado desde {filepath}")


# Test del motor
if __name__ == "__main__":
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from data.price_fetcher import get_btc_price
    
    print("=" * 60)
    print("Testing Paper Trading Engine")
    print("=" * 60)
    
    # Crear motor con $1000 iniciales
    engine = PaperTradingEngine(initial_usd=1000.0, fee_percent=0.1)
    
    # Obtener precio actual
    price_data = get_btc_price()
    price = price_data.price
    print(f"\n📊 Precio actual BTC: ${price:,.2f}")
    
    # Simular algunos trades
    print("\n" + "-" * 40)
    print("Simulando trades...")
    print("-" * 40)
    
    # Comprar con $500
    engine.buy(price, usd_amount=500, strategy="test", reason="Test de compra")
    
    # Simular subida de precio (+2%)
    new_price = price * 1.02
    print(f"\n📈 Precio sube a ${new_price:,.2f} (+2%)")
    
    # Vender todo
    engine.sell(new_price, strategy="test", reason="Test de venta con ganancia")
    
    # Mostrar resumen
    engine.print_summary(new_price)
