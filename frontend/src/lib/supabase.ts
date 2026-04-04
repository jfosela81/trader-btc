import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

export const supabase = createClient(supabaseUrl, supabaseKey)

export interface Trade {
  id: number
  created_at: string
  type: 'buy' | 'sell'
  price: number
  btc_amount: number
  usd_amount: number
  fee_usd: number
  strategy: string
  reason: string
  balance_usd_after: number
  balance_btc_after: number
}

export interface PortfolioSnapshot {
  id: number
  created_at: string
  btc_price: number
  usd_balance: number
  btc_balance: number
  total_value_usd: number
  pnl_usd: number
  pnl_percent: number
}

export async function getLatestPortfolio(): Promise<PortfolioSnapshot | null> {
  const { data, error } = await supabase
    .from('portfolio_snapshots')
    .select('*')
    .order('created_at', { ascending: false })
    .limit(1)
    .single()

  if (error) {
    console.error('Error fetching portfolio:', error)
    return null
  }

  return data
}

export async function getPortfolioHistory(days: number = 7): Promise<PortfolioSnapshot[]> {
  const since = new Date()
  since.setDate(since.getDate() - days)

  const { data, error } = await supabase
    .from('portfolio_snapshots')
    .select('*')
    .gte('created_at', since.toISOString())
    .order('created_at', { ascending: true })

  if (error) {
    console.error('Error fetching portfolio history:', error)
    return []
  }

  return data || []
}

export async function getRecentTrades(limit: number = 20): Promise<Trade[]> {
  const { data, error } = await supabase
    .from('trades')
    .select('*')
    .order('created_at', { ascending: false })
    .limit(limit)

  if (error) {
    console.error('Error fetching trades:', error)
    return []
  }

  return data || []
}

export async function getStats() {
  const { data: trades, error } = await supabase
    .from('trades')
    .select('*')

  if (error) {
    console.error('Error fetching stats:', error)
    return null
  }

  const totalTrades = trades?.length || 0
  const buyTrades = trades?.filter(t => t.type === 'buy').length || 0
  const sellTrades = trades?.filter(t => t.type === 'sell').length || 0
  const totalFees = trades?.reduce((sum, t) => sum + Number(t.fee_usd), 0) || 0

  return {
    totalTrades,
    buyTrades,
    sellTrades,
    totalFees
  }
}
