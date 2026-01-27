"""
Bitcoin Price Fetcher
Obtiene precios de BTC desde múltiples fuentes (Binance, CoinGecko)
Usa requests directamente para máxima compatibilidad.
"""

import requests
from typing import Optional, List
from dataclasses import dataclass
from datetime import datetime


@dataclass
class PriceData:
    """Estructura de datos para precio de BTC"""
    price: float
    timestamp: datetime
    source: str
    volume_24h: Optional[float] = None
    high_24h: Optional[float] = None
    low_24h: Optional[float] = None
    change_24h_percent: Optional[float] = None


@dataclass
class OHLCV:
    """Datos OHLCV (Open, High, Low, Close, Volume)"""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


class PriceFetcher:
    """Fetcher de precios de BTC con múltiples fuentes"""
    
    BINANCE_API = "https://api.binance.com/api/v3"
    COINGECKO_API = "https://api.coingecko.com/api/v3"
    
    def __init__(self, primary_source: str = "binance"):
        self.primary_source = primary_source
        self.timeout = 10
        
    def get_price(self) -> PriceData:
        """
        Obtiene el precio actual de BTC.
        Intenta primero la fuente primaria, si falla usa el fallback.
        """
        try:
            if self.primary_source == "binance":
                return self._fetch_from_binance()
            else:
                return self._fetch_from_coingecko()
        except Exception as e:
            print(f"Error con {self.primary_source}: {e}")
            # Fallback a la otra fuente
            try:
                if self.primary_source == "binance":
                    return self._fetch_from_coingecko()
                else:
                    return self._fetch_from_binance()
            except Exception as e2:
                raise Exception(f"No se pudo obtener precio de ninguna fuente: {e2}")
    
    def _fetch_from_binance(self) -> PriceData:
        """Obtiene precio desde Binance API pública"""
        url = f"{self.BINANCE_API}/ticker/24hr"
        params = {"symbol": "BTCUSDT"}
        
        response = requests.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()
        data = response.json()
        
        return PriceData(
            price=float(data['lastPrice']),
            timestamp=datetime.now(),
            source="binance",
            volume_24h=float(data['quoteVolume']),
            high_24h=float(data['highPrice']),
            low_24h=float(data['lowPrice']),
            change_24h_percent=float(data['priceChangePercent'])
        )
    
    def _fetch_from_coingecko(self) -> PriceData:
        """Obtiene precio desde CoinGecko (fallback gratuito)"""
        url = f"{self.COINGECKO_API}/simple/price"
        params = {
            "ids": "bitcoin",
            "vs_currencies": "usd",
            "include_24hr_vol": "true",
            "include_24hr_change": "true"
        }
        
        response = requests.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()
        data = response.json()
        
        return PriceData(
            price=data['bitcoin']['usd'],
            timestamp=datetime.now(),
            source="coingecko",
            volume_24h=data['bitcoin'].get('usd_24h_vol'),
            change_24h_percent=data['bitcoin'].get('usd_24h_change')
        )
    
    def get_historical_prices(self, 
                               interval: str = "1h", 
                               limit: int = 100) -> List[OHLCV]:
        """
        Obtiene precios históricos para análisis técnico.
        Intenta Binance primero, si falla usa CoinGecko.
        
        Args:
            interval: Intervalo ('1m', '5m', '15m', '1h', '4h', '1d')
            limit: Número de velas a obtener (máximo 1000)
            
        Returns:
            Lista de objetos OHLCV
        """
        try:
            return self._get_historical_from_binance(interval, limit)
        except Exception as e:
            print(f"   ⚠️  Binance históricos falló: {e}")
            print(f"   Usando CoinGecko como fallback...")
            return self._get_historical_from_coingecko(interval, limit)
    
    def _get_historical_from_binance(self, interval: str, limit: int) -> List[OHLCV]:
        """Obtiene históricos desde Binance"""
        url = f"{self.BINANCE_API}/klines"
        params = {
            "symbol": "BTCUSDT",
            "interval": interval,
            "limit": min(limit, 1000)
        }
        
        response = requests.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()
        data = response.json()
        
        result = []
        for candle in data:
            result.append(OHLCV(
                timestamp=datetime.fromtimestamp(candle[0] / 1000),
                open=float(candle[1]),
                high=float(candle[2]),
                low=float(candle[3]),
                close=float(candle[4]),
                volume=float(candle[5])
            ))
        
        return result
    
    def _get_historical_from_coingecko(self, interval: str, limit: int) -> List[OHLCV]:
        """
        Obtiene históricos desde CoinGecko.
        CoinGecko no tiene OHLCV gratuito, así que usamos precios y simulamos.
        """
        # Mapear intervalo a días de historia
        interval_to_days = {
            "1m": 1,
            "5m": 1,
            "15m": 1,
            "1h": 4,      # 100 horas ≈ 4 días
            "4h": 17,     # 100 * 4h ≈ 17 días
            "1d": 100,
        }
        days = interval_to_days.get(interval, 4)
        
        url = f"{self.COINGECKO_API}/coins/bitcoin/market_chart"
        params = {
            "vs_currency": "usd",
            "days": days,
        }
        
        response = requests.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()
        data = response.json()
        
        prices = data.get("prices", [])
        
        # CoinGecko devuelve [timestamp_ms, price]
        # Convertimos a OHLCV (usando el mismo precio para OHLC ya que no tenemos velas reales)
        result = []
        for i, (ts_ms, price) in enumerate(prices[-limit:]):
            result.append(OHLCV(
                timestamp=datetime.fromtimestamp(ts_ms / 1000),
                open=price,
                high=price,
                low=price,
                close=price,
                volume=0  # CoinGecko no da volumen por vela
            ))
        
        return result


# Función de conveniencia para uso rápido
def get_btc_price() -> PriceData:
    """Obtiene el precio actual de BTC"""
    fetcher = PriceFetcher()
    return fetcher.get_price()


if __name__ == "__main__":
    # Test rápido
    print("=" * 50)
    print("Testing BTC Price Fetcher")
    print("=" * 50)
    
    print("\n📊 Obteniendo precio actual de BTC...")
    price_data = get_btc_price()
    print(f"✅ Precio: ${price_data.price:,.2f}")
    print(f"   Fuente: {price_data.source}")
    print(f"   Timestamp: {price_data.timestamp}")
    if price_data.high_24h and price_data.low_24h:
        print(f"   Rango 24h: ${price_data.low_24h:,.2f} - ${price_data.high_24h:,.2f}")
    if price_data.change_24h_percent:
        emoji = "📈" if price_data.change_24h_percent > 0 else "📉"
        print(f"   Cambio 24h: {emoji} {price_data.change_24h_percent:+.2f}%")
    
    print("\n📈 Obteniendo datos históricos (últimas 10 velas de 1h)...")
    fetcher = PriceFetcher()
    historical = fetcher.get_historical_prices(interval="1h", limit=10)
    print(f"✅ Obtenidas {len(historical)} velas")
    for candle in historical[-3:]:  # Mostrar últimas 3
        print(f"   {candle.timestamp.strftime('%Y-%m-%d %H:%M')} | "
              f"O: ${candle.open:,.0f} H: ${candle.high:,.0f} "
              f"L: ${candle.low:,.0f} C: ${candle.close:,.0f}")
