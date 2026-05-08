#!/usr/bin/env python3
"""
Genera el informe mensual del BTC Trading Bot en formato Markdown.
Lee los datos directamente de Supabase (trades + portfolio_snapshots).
Salida: reports/YYYY-MM.md  +  reports/latest.md

Uso:
    python generate_monthly_report.py [YYYY-MM]
    Si no se pasa mes, usa el mes anterior al día en que se ejecuta.
"""

import os
import sys
import json
from datetime import datetime, date, timedelta
from calendar import monthrange
from typing import Optional

try:
    from supabase import create_client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


# ─── Helpers de formato ────────────────────────────────────────────────────────

def fmt_usd(v: float, sign: bool = True) -> str:
    prefix = ("+" if v >= 0 else "") if sign else ""
    return f"{prefix}${v:,.2f}"

def fmt_pct(v: float) -> str:
    prefix = "+" if v >= 0 else ""
    return f"{prefix}{v:.2f}%"

def trend(v: float, good_above: float = 0) -> str:
    if v > good_above:
        return "🟢"
    elif v < good_above:
        return "🔴"
    return "🟡"


# ─── Obtener datos de Supabase ─────────────────────────────────────────────────

def get_supabase_client():
    if not SUPABASE_AVAILABLE:
        print("ERROR: supabase-py no instalado. Ejecuta: pip install supabase")
        sys.exit(1)
    url = os.getenv("SUPABASE_URL", "")
    key = os.getenv("SUPABASE_KEY", "")
    if not url or not key:
        print("ERROR: Faltan SUPABASE_URL o SUPABASE_KEY en las variables de entorno")
        sys.exit(1)
    return create_client(url, key)


def get_trades_for_month(client, year: int, month: int) -> list:
    """Devuelve todos los trades del mes indicado."""
    start = f"{year:04d}-{month:02d}-01T00:00:00"
    last_day = monthrange(year, month)[1]
    end = f"{year:04d}-{month:02d}-{last_day:02d}T23:59:59"
    try:
        result = (
            client.table("trades")
            .select("*")
            .gte("created_at", start)
            .lte("created_at", end)
            .order("created_at")
            .execute()
        )
        return result.data or []
    except Exception as e:
        print(f"⚠️  Error obteniendo trades de Supabase: {e}")
        return []


def get_snapshots_for_month(client, year: int, month: int) -> list:
    """Devuelve todos los portfolio_snapshots del mes indicado."""
    start = f"{year:04d}-{month:02d}-01T00:00:00"
    last_day = monthrange(year, month)[1]
    end = f"{year:04d}-{month:02d}-{last_day:02d}T23:59:59"
    try:
        result = (
            client.table("portfolio_snapshots")
            .select("*")
            .gte("created_at", start)
            .lte("created_at", end)
            .order("created_at")
            .execute()
        )
        return result.data or []
    except Exception as e:
        print(f"⚠️  Error obteniendo snapshots de Supabase: {e}")
        return []


def get_all_snapshots_until(client, year: int, month: int) -> list:
    """Devuelve todos los snapshots hasta el fin del mes indicado (para equity curve)."""
    last_day = monthrange(year, month)[1]
    end = f"{year:04d}-{month:02d}-{last_day:02d}T23:59:59"
    try:
        result = (
            client.table("portfolio_snapshots")
            .select("*")
            .lte("created_at", end)
            .order("created_at")
            .execute()
        )
        return result.data or []
    except Exception as e:
        print(f"⚠️  Error obteniendo equity history de Supabase: {e}")
        return []


# ─── BTC precio desde API pública ─────────────────────────────────────────────

def get_btc_price_at(target_date: date) -> Optional[float]:
    """Obtiene el precio de cierre de BTC en una fecha dada vía CoinGecko."""
    if not REQUESTS_AVAILABLE:
        return None
    date_str = target_date.strftime("%d-%m-%Y")
    try:
        url = f"https://api.coingecko.com/api/v3/coins/bitcoin/history?date={date_str}"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return data["market_data"]["current_price"]["usd"]
    except Exception:
        pass
    return None


# ─── Cálculo de métricas ───────────────────────────────────────────────────────

def calculate_metrics(trades: list, snapshots: list, initial_usd: float):
    """
    Calcula todas las métricas del mes a partir de los trades y snapshots.
    Devuelve un dict con todos los valores para el informe.
    """
    sells = [t for t in trades if t["type"] == "sell"]
    buys  = [t for t in trades if t["type"] == "buy"]

    # Capital inicio y fin de mes
    capital_start = initial_usd
    capital_end   = initial_usd

    if snapshots:
        capital_start = float(snapshots[0]["total_value_usd"])
        capital_end   = float(snapshots[-1]["total_value_usd"])
    elif trades:
        # Fallback: primero y último trade
        capital_start = float(trades[0].get("balance_usd_after", initial_usd))
        capital_end   = float(trades[-1].get("balance_usd_after", initial_usd))

    pnl_month     = capital_end - capital_start
    pnl_month_pct = (pnl_month / capital_start * 100) if capital_start else 0.0

    # P&L acumulado (desde initial_usd original)
    pnl_accum     = capital_end - initial_usd
    pnl_accum_pct = (pnl_accum / initial_usd * 100) if initial_usd else 0.0

    # Trades y win rate (solo ciclos cerrados: buy → sell)
    win_trades  = 0
    loss_trades = 0
    wins_pnl    = []
    losses_pnl  = []

    for sell in sells:
        sell_price = float(sell["price"])
        # Busca el buy más cercano antes de esta venta
        sell_ts = sell["created_at"]
        prior_buys = [b for b in buys if b["created_at"] < sell_ts]
        if prior_buys:
            last_buy = max(prior_buys, key=lambda b: b["created_at"])
            buy_price = float(last_buy["price"])
            trade_pnl = (sell_price - buy_price) / buy_price * float(sell["usd_amount"])
            if sell_price > buy_price:
                win_trades += 1
                wins_pnl.append(trade_pnl)
            else:
                loss_trades += 1
                losses_pnl.append(trade_pnl)

    closed_trades = win_trades + loss_trades
    win_rate = (win_trades / closed_trades * 100) if closed_trades else 0.0

    avg_win  = (sum(wins_pnl)   / len(wins_pnl))   if wins_pnl   else 0.0
    avg_loss = (sum(losses_pnl) / len(losses_pnl)) if losses_pnl else 0.0

    gross_profit = sum(wins_pnl)
    gross_loss   = abs(sum(losses_pnl))
    profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else (float("inf") if gross_profit > 0 else 0.0)

    # Max drawdown del mes (sobre equity curve de snapshots)
    max_drawdown = 0.0
    if snapshots:
        peak = float(snapshots[0]["total_value_usd"])
        for s in snapshots:
            val = float(s["total_value_usd"])
            if val > peak:
                peak = val
            dd = peak - val
            if dd > max_drawdown:
                max_drawdown = dd

    # Fees totales
    total_fees = sum(float(t.get("fee_usd", 0)) for t in trades)

    # Por estrategia
    strategies = {}
    for sell in sells:
        strat = sell.get("strategy", "unknown")
        if strat not in strategies:
            strategies[strat] = {"trades": 0, "wins": 0, "pnl": 0.0}
        strategies[strat]["trades"] += 1
        sell_price = float(sell["price"])
        sell_ts    = sell["created_at"]
        prior_buys = [b for b in buys if b["created_at"] < sell_ts]
        if prior_buys:
            last_buy  = max(prior_buys, key=lambda b: b["created_at"])
            buy_price = float(last_buy["price"])
            trade_pnl = (sell_price - buy_price) / buy_price * float(sell["usd_amount"])
            strategies[strat]["pnl"] += trade_pnl
            if sell_price > buy_price:
                strategies[strat]["wins"] += 1

    return {
        "capital_start":  capital_start,
        "capital_end":    capital_end,
        "initial_usd":    initial_usd,
        "pnl_month":      pnl_month,
        "pnl_month_pct":  pnl_month_pct,
        "pnl_accum":      pnl_accum,
        "pnl_accum_pct":  pnl_accum_pct,
        "total_trades":   len(trades),
        "closed_trades":  closed_trades,
        "win_trades":     win_trades,
        "loss_trades":    loss_trades,
        "win_rate":       win_rate,
        "avg_win":        avg_win,
        "avg_loss":       avg_loss,
        "profit_factor":  profit_factor,
        "max_drawdown":   max_drawdown,
        "total_fees":     total_fees,
        "strategies":     strategies,
    }


# ─── Equity curve mensual ──────────────────────────────────────────────────────

def build_equity_curve(all_snapshots: list, report_year: int, report_month: int) -> list:
    """
    Agrupa los snapshots por mes y devuelve el último valor de cada mes.
    Incluye todos los meses desde el primero hasta el mes del informe.
    """
    monthly = {}
    for s in all_snapshots:
        ts = s["created_at"][:7]  # YYYY-MM
        monthly[ts] = s  # sobreescribe → queda el último del mes

    if not monthly:
        return []

    rows = []
    for month_key in sorted(monthly.keys()):
        snap = monthly[month_key]
        rows.append({
            "month": month_key,
            "total_value_usd": float(snap["total_value_usd"]),
            "pnl_usd":         float(snap["pnl_usd"]),
            "pnl_percent":     float(snap["pnl_percent"]),
            "btc_price":       float(snap.get("btc_price", 0)),
        })
    return rows


# ─── Generación del Markdown ───────────────────────────────────────────────────

def generate_markdown(metrics: dict, equity_curve: list, month: str,
                      btc_start: Optional[float], btc_end: Optional[float]) -> str:
    dt = datetime.strptime(month + "-01", "%Y-%m-%d")
    last_day = monthrange(dt.year, dt.month)[1]
    period_str = f"{month}-01 → {month}-{last_day:02d}"

    # Comparativa Buy & Hold
    if btc_start and btc_end and btc_start > 0:
        bh_pct = (btc_end - btc_start) / btc_start * 100
        bh_usd = metrics["capital_start"] * bh_pct / 100
        bh_line = f"{fmt_pct(bh_pct)} ({fmt_usd(bh_usd)}) · Bot: {fmt_pct(metrics['pnl_month_pct'])}"
    else:
        bh_line = "N/D (precio BTC no disponible)"

    # DCA mensual: comprar 1/12 del capital al inicio cada mes
    dca_monthly_usd = metrics["initial_usd"] / 12
    if btc_start and btc_end and btc_start > 0:
        btc_bought_dca = dca_monthly_usd / btc_start
        dca_pnl = btc_bought_dca * (btc_end - btc_start)
        dca_pnl_pct = dca_pnl / dca_monthly_usd * 100
        dca_line = f"{fmt_pct(dca_pnl_pct)} ({fmt_usd(dca_pnl)}) · Bot: {fmt_pct(metrics['pnl_month_pct'])}"
    else:
        dca_line = "N/D (precio BTC no disponible)"

    # Tabla por estrategia
    strat_rows = []
    for strat_name, s in metrics["strategies"].items():
        t   = s["trades"]
        wr  = (s["wins"] / t * 100) if t > 0 else 0.0
        pnl = s["pnl"]
        strat_rows.append(f"| {strat_name} | {t} | {wr:.0f}% | {fmt_usd(pnl)} |")
    if not strat_rows:
        strat_rows = ["| — | — | — | — |"]

    # Tabla equity curve
    ec_rows = []
    for row in equity_curve:
        ec_rows.append(
            f"| {row['month']} | ${row['total_value_usd']:,.2f} | "
            f"{fmt_usd(row['pnl_usd'])} | {fmt_pct(row['pnl_percent'])} | "
            f"${row['btc_price']:,.0f} |"
        )
    if not ec_rows:
        ec_rows = ["| — | — | — | — | — |"]

    pf_val = metrics["profit_factor"]
    pf_str = f"{pf_val:.2f}" if pf_val != float("inf") else "∞"

    lines = [
        f"# BTC Trader — Informe Mensual {month}",
        f"",
        f"> Generado automáticamente el 1 de {dt.strftime('%B %Y')}.",
        f"> Paper trading · Estrategia SMA Crossover · BTC/USD.",
        f"",
        f"---",
        f"",
        f"## Resumen",
        f"",
        f"| Métrica | Valor |",
        f"|---------|-------|",
        f"| Período | {period_str} |",
        f"| Capital inicial (histórico) | ${metrics['initial_usd']:,.2f} |",
        f"| Capital inicio de mes | ${metrics['capital_start']:,.2f} |",
        f"| Capital fin de mes | ${metrics['capital_end']:,.2f} |",
        f"| P&L mes | {fmt_usd(metrics['pnl_month'])} ({fmt_pct(metrics['pnl_month_pct'])}) |",
        f"| P&L acumulado | {fmt_usd(metrics['pnl_accum'])} ({fmt_pct(metrics['pnl_accum_pct'])}) |",
        f"",
        f"---",
        f"",
        f"## Métricas",
        f"",
        f"| Métrica | Valor |",
        f"|---------|-------|",
        f"| Trades totales | {metrics['total_trades']} |",
        f"| Ciclos cerrados (buy→sell) | {metrics['closed_trades']} |",
        f"| Win rate | {metrics['win_rate']:.1f}% |",
        f"| Profit factor | {pf_str} |",
        f"| Max drawdown | {fmt_usd(metrics['max_drawdown'], sign=False)} |",
        f"| Avg win / Avg loss | {fmt_usd(metrics['avg_win'])} / {fmt_usd(metrics['avg_loss'])} |",
        f"| Fees totales pagados | ${metrics['total_fees']:.2f} |",
        f"",
        f"---",
        f"",
        f"## Desglose por Estrategia",
        f"",
        f"| Estrategia | Trades | Win Rate | P&L |",
        f"|-----------|--------|----------|-----|",
        *strat_rows,
        f"",
        f"---",
        f"",
        f"## Comparativa",
        f"",
        f"| Benchmark | Resultado mes | vs Bot |",
        f"|-----------|---------------|--------|",
        f"| Bot BTC Trader | {fmt_pct(metrics['pnl_month_pct'])} ({fmt_usd(metrics['pnl_month'])}) | — |",
        f"| Buy & Hold BTC | {bh_line} | — |",
        f"| DCA mensual BTC | {dca_line} | — |",
        f"",
        f"---",
        f"",
        f"## Equity Curve",
        f"",
        f"| Mes | Capital Total | P&L Acum. | P&L % | Precio BTC |",
        f"|-----|--------------|-----------|-------|------------|",
        *ec_rows,
        f"",
        f"---",
        f"",
        f"*Fuente: Supabase · Repo: [jfosela81/btc-trader](https://github.com/jfosela81/btc-trader) · "
        f"URL fija: https://raw.githubusercontent.com/jfosela81/btc-trader/main/reports/latest.md*",
    ]

    return "\n".join(lines) + "\n"


# ─── Main ──────────────────────────────────────────────────────────────────────

def main():
    # Determinar mes del informe
    if len(sys.argv) >= 2:
        month_str = sys.argv[1]  # YYYY-MM
    else:
        today = date.today()
        # El script corre el día 1 del mes actual → reporta el mes anterior
        first_of_this_month = today.replace(day=1)
        prev_month_end = first_of_this_month - timedelta(days=1)
        month_str = prev_month_end.strftime("%Y-%m")

    try:
        report_dt = datetime.strptime(month_str + "-01", "%Y-%m-%d")
    except ValueError:
        print(f"ERROR: Formato de mes inválido '{month_str}'. Usa YYYY-MM")
        sys.exit(1)

    report_year  = report_dt.year
    report_month = report_dt.month
    print(f"📅 Generando informe para: {month_str}")

    # Conectar a Supabase
    client = get_supabase_client()
    print("✅ Conectado a Supabase")

    # Obtener datos
    print("📊 Obteniendo trades del mes...")
    trades = get_trades_for_month(client, report_year, report_month)
    print(f"   → {len(trades)} trades encontrados")

    print("📈 Obteniendo snapshots del mes...")
    snapshots = get_snapshots_for_month(client, report_year, report_month)
    print(f"   → {len(snapshots)} snapshots encontrados")

    print("📉 Obteniendo historial de equity...")
    all_snaps = get_all_snapshots_until(client, report_year, report_month)

    # Capital inicial desde env var o el valor por defecto
    initial_usd = float(os.getenv("INITIAL_BALANCE_USD", "1000"))

    # Calcular métricas
    metrics = calculate_metrics(trades, snapshots, initial_usd)

    # Precio BTC al inicio y fin del mes para comparativa
    first_day = date(report_year, report_month, 1)
    last_day_num = monthrange(report_year, report_month)[1]
    last_day = date(report_year, report_month, last_day_num)

    print("💱 Obteniendo precios BTC para comparativa...")
    btc_start = get_btc_price_at(first_day)
    btc_end   = get_btc_price_at(last_day)

    # Si tenemos snapshots, usar esos precios como fallback
    if btc_start is None and snapshots:
        btc_start = float(snapshots[0].get("btc_price", 0)) or None
    if btc_end is None and snapshots:
        btc_end = float(snapshots[-1].get("btc_price", 0)) or None

    print(f"   BTC inicio de mes: {'$' + f'{btc_start:,.0f}' if btc_start else 'N/D'}")
    print(f"   BTC fin de mes:    {'$' + f'{btc_end:,.0f}' if btc_end else 'N/D'}")

    # Equity curve
    equity_curve = build_equity_curve(all_snaps, report_year, report_month)

    # Generar Markdown
    content = generate_markdown(metrics, equity_curve, month_str, btc_start, btc_end)

    # Guardar archivos
    reports_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reports")
    os.makedirs(reports_dir, exist_ok=True)

    monthly_path = os.path.join(reports_dir, f"{month_str}.md")
    latest_path  = os.path.join(reports_dir, "latest.md")

    with open(monthly_path, "w") as f:
        f.write(content)
    with open(latest_path, "w") as f:
        f.write(content)

    print(f"✅ Informe guardado en: {monthly_path}")
    print(f"✅ Latest actualizado:  {latest_path}")
    print(f"🔗 URL fija: https://raw.githubusercontent.com/jfosela81/btc-trader/main/reports/latest.md")


if __name__ == "__main__":
    main()
