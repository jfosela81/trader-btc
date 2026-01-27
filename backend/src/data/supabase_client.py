"""
Cliente de Supabase para persistencia de datos
"""

import os
from datetime import datetime
from typing import Optional, List, Dict, Any

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    Client = None


class SupabaseClient:
    """
    Cliente para interactuar con Supabase.
    Si no está configurado, opera en modo offline (solo logs).
    """
    
    def __init__(self):
        self.client: Optional[Client] = None
        self.is_connected = False
        
        if not SUPABASE_AVAILABLE:
            print("⚠️  Supabase no instalado. Operando en modo offline.")
            return
        
        url = os.getenv("SUPABASE_URL", "")
        key = os.getenv("SUPABASE_KEY", "")
        
        if url and key:
            try:
                self.client = create_client(url, key)
                self.is_connected = True
                print("✅ Conectado a Supabase")
            except Exception as e:
                print(f"⚠️  Error conectando a Supabase: {e}")
                print("   Operando en modo offline.")
        else:
            print("⚠️  Supabase no configurado (faltan SUPABASE_URL o SUPABASE_KEY)")
            print("   Operando en modo offline.")
    
    def save_trade(self, trade_data: Dict[str, Any]) -> bool:
        """
        Guarda un trade en la tabla 'trades'.
        
        Args:
            trade_data: Diccionario con los datos del trade
            
        Returns:
            True si se guardó correctamente
        """
        if not self.is_connected:
            return False
        
        try:
            # Preparar datos para Supabase
            data = {
                "type": trade_data.get("type"),
                "price": trade_data.get("price"),
                "btc_amount": trade_data.get("btc_amount"),
                "usd_amount": trade_data.get("usd_amount"),
                "fee_usd": trade_data.get("fee_usd"),
                "strategy": trade_data.get("strategy"),
                "reason": trade_data.get("reason"),
                "balance_usd_after": trade_data.get("balance_usd_after"),
                "balance_btc_after": trade_data.get("balance_btc_after")
            }
            
            result = self.client.table("trades").insert(data).execute()
            print(f"   💾 Trade guardado en Supabase (id: {result.data[0]['id']})")
            return True
            
        except Exception as e:
            print(f"   ⚠️  Error guardando trade en Supabase: {e}")
            return False
    
    def save_portfolio_snapshot(self, 
                                 btc_price: float,
                                 usd_balance: float,
                                 btc_balance: float,
                                 total_value_usd: float,
                                 pnl_usd: float,
                                 pnl_percent: float) -> bool:
        """
        Guarda un snapshot del portfolio.
        """
        if not self.is_connected:
            return False
        
        try:
            data = {
                "btc_price": btc_price,
                "usd_balance": usd_balance,
                "btc_balance": btc_balance,
                "total_value_usd": total_value_usd,
                "pnl_usd": pnl_usd,
                "pnl_percent": pnl_percent
            }
            
            result = self.client.table("portfolio_snapshots").insert(data).execute()
            print(f"   💾 Portfolio snapshot guardado en Supabase")
            return True
            
        except Exception as e:
            print(f"   ⚠️  Error guardando snapshot en Supabase: {e}")
            return False
    
    def get_latest_portfolio(self) -> Optional[Dict[str, Any]]:
        """
        Obtiene el último estado del portfolio guardado.
        Útil para restaurar el estado al iniciar el bot.
        """
        if not self.is_connected:
            return None
        
        try:
            result = self.client.table("portfolio_snapshots") \
                .select("*") \
                .order("created_at", desc=True) \
                .limit(1) \
                .execute()
            
            if result.data:
                return result.data[0]
            return None
            
        except Exception as e:
            print(f"⚠️  Error obteniendo portfolio de Supabase: {e}")
            return None
    
    def get_recent_trades(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Obtiene los trades más recientes.
        """
        if not self.is_connected:
            return []
        
        try:
            result = self.client.table("trades") \
                .select("*") \
                .order("created_at", desc=True) \
                .limit(limit) \
                .execute()
            
            return result.data
            
        except Exception as e:
            print(f"⚠️  Error obteniendo trades de Supabase: {e}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas agregadas de trading.
        """
        if not self.is_connected:
            return {}
        
        try:
            # Total de trades
            trades = self.client.table("trades").select("*").execute()
            
            total_trades = len(trades.data)
            buy_trades = [t for t in trades.data if t['type'] == 'buy']
            sell_trades = [t for t in trades.data if t['type'] == 'sell']
            total_fees = sum(float(t['fee_usd']) for t in trades.data)
            
            return {
                "total_trades": total_trades,
                "buy_trades": len(buy_trades),
                "sell_trades": len(sell_trades),
                "total_fees_paid": total_fees
            }
            
        except Exception as e:
            print(f"⚠️  Error obteniendo stats de Supabase: {e}")
            return {}


# Singleton para reutilizar la conexión
_supabase_instance: Optional[SupabaseClient] = None

def get_supabase() -> SupabaseClient:
    """Obtiene la instancia singleton del cliente de Supabase"""
    global _supabase_instance
    if _supabase_instance is None:
        _supabase_instance = SupabaseClient()
    return _supabase_instance
