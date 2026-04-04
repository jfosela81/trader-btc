'use client'

interface StatsCardProps {
  title: string
  value: string
  subtitle?: string
  trend?: 'up' | 'down' | 'neutral'
  icon?: React.ReactNode
}

export function StatsCard({ title, value, subtitle, trend, icon }: StatsCardProps) {
  const trendColor = {
    up: 'text-green-500',
    down: 'text-red-500',
    neutral: 'text-gray-500'
  }

  return (
    <div className="bg-gray-900 rounded-xl p-6 border border-gray-800">
      <div className="flex items-center justify-between mb-2">
        <span className="text-gray-400 text-sm font-medium">{title}</span>
        {icon && <span className="text-gray-500">{icon}</span>}
      </div>
      <div className={`text-2xl font-bold ${trend ? trendColor[trend] : 'text-white'}`}>
        {value}
      </div>
      {subtitle && (
        <div className={`text-sm mt-1 ${trend ? trendColor[trend] : 'text-gray-500'}`}>
          {subtitle}
        </div>
      )}
    </div>
  )
}
