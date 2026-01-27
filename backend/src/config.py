"""
Configuración del bot de trading
"""

import os
from dotenv import load_dotenv
from dataclasses import dataclass

# Cargar variables de entorno
load_dotenv()


@dataclass
class TradingConfig:
    """Configuración de trading"""
    initial_balance_usd: float = 1000.0
    trading_fee_percent: float = 0.1  # 0.1% por trade (similar a Binance)
    
    # Stop Loss y Take Profit (porcentajes)
    stop_loss_percent: float = 3.0    # Vender si pierde 3%
    take_profit_percent: float = 5.0  # Vender si gana 5%
    
    # Gestión de riesgo
    max_position_percent: float = 50.0  # Máximo 50% del capital en una posición
    daily_loss_limit_percent: float = 5.0  # Pausar si pierde 5% en un día
    
    # Modo de operación
    dry_run: bool = True  # True = paper trading, False = trading real


@dataclass 
class SupabaseConfig:
    """Configuración de Supabase"""
    url: str = ""
    key: str = ""
    
    def __post_init__(self):
        self.url = os.getenv("SUPABASE_URL", "")
        self.key = os.getenv("SUPABASE_KEY", "")
    
    @property
    def is_configured(self) -> bool:
        return bool(self.url and self.key)


@dataclass
class BotConfig:
    """Configuración general del bot"""
    check_interval_minutes: int = 15
    primary_price_source: str = "binance"  # "binance" o "coingecko"


def get_trading_config() -> TradingConfig:
    """Obtiene la configuración de trading desde env vars"""
    return TradingConfig(
        initial_balance_usd=float(os.getenv("INITIAL_BALANCE_USD", "1000")),
        trading_fee_percent=float(os.getenv("TRADING_FEE_PERCENT", "0.1")),
        dry_run=os.getenv("DRY_RUN", "true").lower() == "true"
    )


def get_supabase_config() -> SupabaseConfig:
    """Obtiene la configuración de Supabase"""
    return SupabaseConfig()


def get_bot_config() -> BotConfig:
    """Obtiene la configuración del bot"""
    return BotConfig(
        check_interval_minutes=int(os.getenv("CHECK_INTERVAL_MINUTES", "15"))
    )
