"""
Analizador de rendimiento del Trading Bot
Ejecutar periódicamente para evaluar la estrategia y proponer mejoras.

Uso:
    python analyzer.py

Genera un informe completo con:
- Métricas de rendimiento
- Comparación vs HOLD
- Análisis de trades
- Recomendaciones de mejora
"""

import sys
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env'))

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.supabase_client import get_supabase


class TradingAnalyzer:
    """Analiza el rendimiento del bot de trading"""
    
    def __init__(self):
        self.supabase = get_supabase()
        self.trades: List[Dict] = []
        self.snapshots: List[Dict] = []
        self.initial_balance = 1000.0
        
    def fetch_data(self):
        """Obtiene todos los datos de Supabase"""
        if not self.supabase.is_connected:
            print("❌ No se pudo conectar a Supabase")
            return False
        
        # Obtener trades
        result = self.supabase.client.table("trades").select("*").order("created_at").execute()
        self.trades = result.data or []
        
        # Obtener snapshots
        result = self.supabase.client.table("portfolio_snapshots").select("*").order("created_at").execute()
        self.snapshots = result.data or []
        
        print(f"📊 Datos cargados: {len(self.trades)} trades, {len(self.snapshots)} snapshots")
        return True
    
    def calculate_metrics(self) -> Dict[str, Any]:
        """Calcula métricas principales de rendimiento"""
        if not self.trades:
            return {"error": "No hay trades para analizar"}
        
        # Separar compras y ventas
        buys = [t for t in self.trades if t['type'] == 'buy']
        sells = [t for t in self.trades if t['type'] == 'sell']
        
        # Calcular trades ganadores/perdedores
        winning_trades = 0
        losing_trades = 0
        total_profit = 0
        total_loss = 0
        
        # Emparejar compras con ventas para calcular P&L por trade
        buy_prices = []
        for trade in self.trades:
            if trade['type'] == 'buy':
                buy_prices.append(float(trade['price']))
            elif trade['type'] == 'sell' and buy_prices:
                buy_price = buy_prices.pop(0)
                sell_price = float(trade['price'])
                pnl = sell_price - buy_price
                if pnl > 0:
                    winning_trades += 1
                    total_profit += pnl
                else:
                    losing_trades += 1
                    total_loss += abs(pnl)
        
        # Win rate
        completed_trades = winning_trades + losing_trades
        win_rate = (winning_trades / completed_trades * 100) if completed_trades > 0 else 0
        
        # Profit factor
        profit_factor = (total_profit / total_loss) if total_loss > 0 else float('inf')
        
        # Fees totales
        total_fees = sum(float(t['fee_usd']) for t in self.trades)
        
        # Valor actual del portfolio
        current_value = self.initial_balance
        if self.snapshots:
            current_value = float(self.snapshots[-1]['total_value_usd'])
        
        # P&L total
        total_pnl = current_value - self.initial_balance
        total_pnl_percent = (total_pnl / self.initial_balance) * 100
        
        return {
            "total_trades": len(self.trades),
            "buy_trades": len(buys),
            "sell_trades": len(sells),
            "completed_cycles": completed_trades,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "win_rate": win_rate,
            "profit_factor": profit_factor,
            "total_fees": total_fees,
            "current_value": current_value,
            "total_pnl": total_pnl,
            "total_pnl_percent": total_pnl_percent,
        }
    
    def calculate_hold_comparison(self) -> Dict[str, Any]:
        """Compara rendimiento del bot vs simplemente holdear BTC"""
        if not self.snapshots or len(self.snapshots) < 2:
            return {"error": "Datos insuficientes para comparar"}
        
        first_snapshot = self.snapshots[0]
        last_snapshot = self.snapshots[-1]
        
        # Precio BTC al inicio y ahora
        btc_price_start = float(first_snapshot['btc_price'])
        btc_price_now = float(last_snapshot['btc_price'])
        
        # Si hubiéramos comprado todo en BTC al inicio
        btc_bought = self.initial_balance / btc_price_start
        hold_value_now = btc_bought * btc_price_now
        hold_pnl = hold_value_now - self.initial_balance
        hold_pnl_percent = (hold_pnl / self.initial_balance) * 100
        
        # Rendimiento del bot
        bot_value = float(last_snapshot['total_value_usd'])
        bot_pnl = bot_value - self.initial_balance
        bot_pnl_percent = (bot_pnl / self.initial_balance) * 100
        
        # Diferencia
        outperformance = bot_pnl_percent - hold_pnl_percent
        
        return {
            "period_start": first_snapshot['created_at'],
            "period_end": last_snapshot['created_at'],
            "btc_price_start": btc_price_start,
            "btc_price_now": btc_price_now,
            "btc_change_percent": ((btc_price_now - btc_price_start) / btc_price_start) * 100,
            "hold_value": hold_value_now,
            "hold_pnl": hold_pnl,
            "hold_pnl_percent": hold_pnl_percent,
            "bot_value": bot_value,
            "bot_pnl": bot_pnl,
            "bot_pnl_percent": bot_pnl_percent,
            "outperformance": outperformance,
            "bot_beats_hold": outperformance > 0
        }
    
    def calculate_drawdown(self) -> Dict[str, Any]:
        """Calcula el drawdown máximo (peor racha de pérdidas)"""
        if not self.snapshots:
            return {"error": "Sin datos"}
        
        values = [float(s['total_value_usd']) for s in self.snapshots]
        
        peak = values[0]
        max_drawdown = 0
        max_drawdown_percent = 0
        
        for value in values:
            if value > peak:
                peak = value
            drawdown = peak - value
            drawdown_percent = (drawdown / peak) * 100 if peak > 0 else 0
            if drawdown_percent > max_drawdown_percent:
                max_drawdown = drawdown
                max_drawdown_percent = drawdown_percent
        
        return {
            "max_drawdown_usd": max_drawdown,
            "max_drawdown_percent": max_drawdown_percent,
        }
    
    def analyze_trade_patterns(self) -> Dict[str, Any]:
        """Analiza patrones en los trades"""
        if not self.trades:
            return {"error": "Sin trades"}
        
        # Analizar por hora del día
        hour_performance = {}
        for trade in self.trades:
            hour = datetime.fromisoformat(trade['created_at'].replace('Z', '+00:00')).hour
            if hour not in hour_performance:
                hour_performance[hour] = {"count": 0, "types": []}
            hour_performance[hour]["count"] += 1
            hour_performance[hour]["types"].append(trade['type'])
        
        # Trades promedio por día
        if self.trades:
            first_trade = datetime.fromisoformat(self.trades[0]['created_at'].replace('Z', '+00:00'))
            last_trade = datetime.fromisoformat(self.trades[-1]['created_at'].replace('Z', '+00:00'))
            days_active = max((last_trade - first_trade).days, 1)
            trades_per_day = len(self.trades) / days_active
        else:
            trades_per_day = 0
        
        return {
            "trades_per_day": trades_per_day,
            "most_active_hours": sorted(hour_performance.items(), key=lambda x: x[1]["count"], reverse=True)[:3],
        }
    
    def generate_recommendations(self, metrics: Dict, hold_comparison: Dict, drawdown: Dict) -> List[str]:
        """Genera recomendaciones basadas en el análisis"""
        recommendations = []
        
        # Basado en win rate
        if metrics.get("win_rate", 0) < 50:
            recommendations.append(
                "⚠️ Win rate bajo (<50%). Considerar añadir filtros adicionales (RSI, volumen) "
                "para reducir señales falsas."
            )
        elif metrics.get("win_rate", 0) > 60:
            recommendations.append(
                "✅ Win rate saludable (>60%). La estrategia está identificando bien las tendencias."
            )
        
        # Basado en profit factor
        pf = metrics.get("profit_factor", 0)
        if pf < 1:
            recommendations.append(
                "⚠️ Profit factor <1 (pierdes más de lo que ganas). Revisar stop-loss y take-profit."
            )
        elif pf < 1.5:
            recommendations.append(
                "⚡ Profit factor entre 1-1.5. Aceptable pero mejorable. Considerar ajustar períodos SMA."
            )
        
        # Basado en comparación con HOLD
        if hold_comparison.get("bot_beats_hold") == False:
            recommendations.append(
                f"📉 El bot rinde PEOR que simplemente holdear BTC "
                f"({hold_comparison.get('outperformance', 0):.2f}% diferencia). "
                "En mercado alcista, esto es común. Evaluar si añadir más señales de compra."
            )
        else:
            recommendations.append(
                f"📈 El bot SUPERA a la estrategia HOLD por {hold_comparison.get('outperformance', 0):.2f}%. ¡Buen trabajo!"
            )
        
        # Basado en drawdown
        if drawdown.get("max_drawdown_percent", 0) > 10:
            recommendations.append(
                f"⚠️ Drawdown máximo alto ({drawdown.get('max_drawdown_percent', 0):.1f}%). "
                "Implementar stop-loss más agresivo para proteger capital."
            )
        
        # Basado en frecuencia de trades
        if metrics.get("total_trades", 0) < 10:
            recommendations.append(
                "📊 Pocos trades aún. Necesitas más datos (mínimo 50-100 trades) para conclusiones fiables."
            )
        
        # Fees
        if metrics.get("total_fees", 0) > abs(metrics.get("total_pnl", 1)) * 0.5:
            recommendations.append(
                "💸 Los fees representan >50% de tu P&L. Considerar reducir frecuencia de trades "
                "o usar exchange con menores comisiones."
            )
        
        return recommendations
    
    def print_report(self):
        """Genera e imprime el informe completo"""
        print("\n" + "="*70)
        print("📊 INFORME DE ANÁLISIS - BTC TRADING BOT")
        print("="*70)
        print(f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*70)
        
        # Obtener datos
        if not self.fetch_data():
            return
        
        # Métricas principales
        metrics = self.calculate_metrics()
        print("\n📈 MÉTRICAS DE RENDIMIENTO")
        print("-"*40)
        print(f"Total trades:        {metrics.get('total_trades', 0)}")
        print(f"  - Compras:         {metrics.get('buy_trades', 0)}")
        print(f"  - Ventas:          {metrics.get('sell_trades', 0)}")
        print(f"Ciclos completados:  {metrics.get('completed_cycles', 0)}")
        print(f"  - Ganadores:       {metrics.get('winning_trades', 0)}")
        print(f"  - Perdedores:      {metrics.get('losing_trades', 0)}")
        print(f"Win Rate:            {metrics.get('win_rate', 0):.1f}%")
        print(f"Profit Factor:       {metrics.get('profit_factor', 0):.2f}")
        print(f"Fees pagados:        ${metrics.get('total_fees', 0):.2f}")
        print(f"\nValor actual:        ${metrics.get('current_value', 0):.2f}")
        print(f"P&L Total:           ${metrics.get('total_pnl', 0):+.2f} ({metrics.get('total_pnl_percent', 0):+.2f}%)")
        
        # Comparación con HOLD
        hold = self.calculate_hold_comparison()
        if "error" not in hold:
            print("\n📊 COMPARACIÓN VS HOLD BTC")
            print("-"*40)
            print(f"Período:             {hold.get('period_start', '')[:10]} → {hold.get('period_end', '')[:10]}")
            print(f"BTC inicio:          ${hold.get('btc_price_start', 0):,.0f}")
            print(f"BTC ahora:           ${hold.get('btc_price_now', 0):,.0f} ({hold.get('btc_change_percent', 0):+.1f}%)")
            print(f"\nSi HOLD BTC:         ${hold.get('hold_value', 0):.2f} ({hold.get('hold_pnl_percent', 0):+.2f}%)")
            print(f"Con el BOT:          ${hold.get('bot_value', 0):.2f} ({hold.get('bot_pnl_percent', 0):+.2f}%)")
            winner = "🤖 BOT GANA" if hold.get('bot_beats_hold') else "📈 HOLD GANA"
            print(f"\n{winner} por {abs(hold.get('outperformance', 0)):.2f}%")
        
        # Drawdown
        drawdown = self.calculate_drawdown()
        if "error" not in drawdown:
            print("\n📉 ANÁLISIS DE RIESGO")
            print("-"*40)
            print(f"Drawdown máximo:     ${drawdown.get('max_drawdown_usd', 0):.2f} ({drawdown.get('max_drawdown_percent', 0):.1f}%)")
        
        # Patrones
        patterns = self.analyze_trade_patterns()
        if "error" not in patterns:
            print("\n🕐 PATRONES DE TRADING")
            print("-"*40)
            print(f"Trades/día promedio: {patterns.get('trades_per_day', 0):.2f}")
        
        # Recomendaciones
        recommendations = self.generate_recommendations(metrics, hold, drawdown)
        print("\n💡 RECOMENDACIONES")
        print("-"*40)
        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. {rec}")
        
        print("\n" + "="*70)
        print("Fin del informe")
        print("="*70 + "\n")
        
        return {
            "metrics": metrics,
            "hold_comparison": hold,
            "drawdown": drawdown,
            "patterns": patterns,
            "recommendations": recommendations
        }


def main():
    """Ejecuta el análisis"""
    analyzer = TradingAnalyzer()
    analyzer.print_report()


if __name__ == "__main__":
    main()
