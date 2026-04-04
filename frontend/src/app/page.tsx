import { Suspense } from 'react'
import { getLatestPortfolio, getPortfolioHistory, getRecentTrades, getStats } from '@/lib/supabase'
import { StatsCard } from '@/components/StatsCard'
import { PortfolioChart } from '@/components/PortfolioChart'
import { TradesTable } from '@/components/TradesTable'

async function DashboardContent() {
  const [portfolio, history, trades, stats] = await Promise.all([
    getLatestPortfolio(),
    getPortfolioHistory(7),
    getRecentTrades(20),
    getStats()
  ])

  const pnlTrend = portfolio 
    ? (Number(portfolio.pnl_usd) >= 0 ? 'up' : 'down')
    : 'neutral'

  return (
    <div className="space-y-6">
      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatsCard
          title="Valor del Portfolio"
          value={portfolio ? `$${Number(portfolio.total_value_usd).toLocaleString('es-ES', { minimumFractionDigits: 2 })}` : '$1,000.00'}
          subtitle={portfolio ? `BTC: $${Number(portfolio.btc_price).toLocaleString('es-ES', { maximumFractionDigits: 0 })}` : 'Esperando datos...'}
        />
        <StatsCard
          title="P&L Total"
          value={portfolio ? `${Number(portfolio.pnl_usd) >= 0 ? '+' : ''}$${Number(portfolio.pnl_usd).toFixed(2)}` : '$0.00'}
          subtitle={portfolio ? `${Number(portfolio.pnl_percent) >= 0 ? '+' : ''}${Number(portfolio.pnl_percent).toFixed(2)}%` : '0.00%'}
          trend={pnlTrend}
        />
        <StatsCard
          title="Balance USD"
          value={portfolio ? `$${Number(portfolio.usd_balance).toLocaleString('es-ES', { minimumFractionDigits: 2 })}` : '$1,000.00'}
        />
        <StatsCard
          title="Balance BTC"
          value={portfolio ? `${Number(portfolio.btc_balance).toFixed(6)}` : '0.000000'}
          subtitle="BTC"
        />
      </div>

      {/* Stats secundarios */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <StatsCard
          title="Trades Totales"
          value={stats?.totalTrades?.toString() || '0'}
          subtitle={`${stats?.buyTrades || 0} compras / ${stats?.sellTrades || 0} ventas`}
        />
        <StatsCard
          title="Fees Pagados"
          value={`$${(stats?.totalFees || 0).toFixed(2)}`}
          subtitle="Total acumulado"
        />
        <StatsCard
          title="Última Actualización"
          value={portfolio ? new Date(portfolio.created_at).toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' }) : '--:--'}
          subtitle={portfolio ? new Date(portfolio.created_at).toLocaleDateString('es-ES') : 'Sin datos'}
        />
      </div>

      {/* Chart */}
      <PortfolioChart data={history} />

      {/* Trades Table */}
      <TradesTable trades={trades} />
    </div>
  )
}

function LoadingState() {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="bg-gray-900 rounded-xl p-6 border border-gray-800 animate-pulse">
            <div className="h-4 bg-gray-800 rounded w-24 mb-3"></div>
            <div className="h-8 bg-gray-800 rounded w-32"></div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default function Home() {
  return (
    <main className="min-h-screen bg-black text-white">
      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 bg-orange-500 rounded-lg flex items-center justify-center">
              <span className="text-xl">₿</span>
            </div>
            <h1 className="text-2xl font-bold">BTC Trading Bot</h1>
            <span className="px-2 py-1 bg-green-500/20 text-green-400 text-xs rounded-full">
              Paper Trading
            </span>
          </div>
          <p className="text-gray-400">
            Dashboard de seguimiento del bot de trading algorítmico
          </p>
        </div>

        {/* Dashboard Content */}
        <Suspense fallback={<LoadingState />}>
          <DashboardContent />
        </Suspense>

        {/* Footer */}
        <footer className="mt-12 pt-6 border-t border-gray-800 text-center text-gray-500 text-sm">
          <p>Bot ejecutándose cada hora via GitHub Actions</p>
          <p className="mt-1">Estrategia: SMA Crossover (10/50)</p>
        </footer>
      </div>
    </main>
  )
}

export const revalidate = 60 // Revalidar cada 60 segundos
