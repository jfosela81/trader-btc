'use client'

import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, Area, AreaChart } from 'recharts'
import { format } from 'date-fns'
import { es } from 'date-fns/locale'
import { PortfolioSnapshot } from '@/lib/supabase'

interface PortfolioChartProps {
  data: PortfolioSnapshot[]
}

export function PortfolioChart({ data }: PortfolioChartProps) {
  if (data.length === 0) {
    return (
      <div className="bg-gray-900 rounded-xl p-6 border border-gray-800 h-80 flex items-center justify-center">
        <p className="text-gray-500">No hay datos suficientes para mostrar el gráfico</p>
      </div>
    )
  }

  const chartData = data.map(snapshot => ({
    date: format(new Date(snapshot.created_at), 'dd MMM HH:mm', { locale: es }),
    value: Number(snapshot.total_value_usd),
    btcPrice: Number(snapshot.btc_price),
    pnl: Number(snapshot.pnl_percent)
  }))

  const minValue = Math.min(...chartData.map(d => d.value)) * 0.99
  const maxValue = Math.max(...chartData.map(d => d.value)) * 1.01

  const isPositive = chartData.length > 1 && 
    chartData[chartData.length - 1].value >= chartData[0].value

  return (
    <div className="bg-gray-900 rounded-xl p-6 border border-gray-800">
      <h3 className="text-lg font-semibold text-white mb-4">Evolución del Portfolio</h3>
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData}>
            <defs>
              <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                <stop 
                  offset="5%" 
                  stopColor={isPositive ? '#10B981' : '#EF4444'} 
                  stopOpacity={0.3}
                />
                <stop 
                  offset="95%" 
                  stopColor={isPositive ? '#10B981' : '#EF4444'} 
                  stopOpacity={0}
                />
              </linearGradient>
            </defs>
            <XAxis 
              dataKey="date" 
              stroke="#6B7280" 
              fontSize={12}
              tickLine={false}
              axisLine={false}
            />
            <YAxis 
              stroke="#6B7280" 
              fontSize={12}
              tickLine={false}
              axisLine={false}
              domain={[minValue, maxValue]}
              tickFormatter={(value) => `$${value.toFixed(0)}`}
            />
            <Tooltip 
              contentStyle={{ 
                backgroundColor: '#1F2937', 
                border: '1px solid #374151',
                borderRadius: '8px'
              }}
              labelStyle={{ color: '#9CA3AF' }}
              formatter={(value) => [`$${Number(value).toFixed(2)}`, 'Valor']}
            />
            <Area
              type="monotone"
              dataKey="value"
              stroke={isPositive ? '#10B981' : '#EF4444'}
              strokeWidth={2}
              fill="url(#colorValue)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
