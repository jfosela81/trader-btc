'use client'

import { format } from 'date-fns'
import { es } from 'date-fns/locale'
import { Trade } from '@/lib/supabase'

interface TradesTableProps {
  trades: Trade[]
}

export function TradesTable({ trades }: TradesTableProps) {
  if (trades.length === 0) {
    return (
      <div className="bg-gray-900 rounded-xl p-6 border border-gray-800">
        <h3 className="text-lg font-semibold text-white mb-4">Historial de Trades</h3>
        <p className="text-gray-500 text-center py-8">
          No hay trades ejecutados todavía. El bot está esperando señales de compra/venta.
        </p>
      </div>
    )
  }

  return (
    <div className="bg-gray-900 rounded-xl p-6 border border-gray-800">
      <h3 className="text-lg font-semibold text-white mb-4">Historial de Trades</h3>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="text-left text-gray-400 text-sm border-b border-gray-800">
              <th className="pb-3 font-medium">Fecha</th>
              <th className="pb-3 font-medium">Tipo</th>
              <th className="pb-3 font-medium">Precio BTC</th>
              <th className="pb-3 font-medium">Cantidad</th>
              <th className="pb-3 font-medium">USD</th>
              <th className="pb-3 font-medium">Fee</th>
              <th className="pb-3 font-medium">Estrategia</th>
            </tr>
          </thead>
          <tbody>
            {trades.map((trade) => (
              <tr key={trade.id} className="border-b border-gray-800/50">
                <td className="py-3 text-gray-300 text-sm">
                  {format(new Date(trade.created_at), 'dd MMM HH:mm', { locale: es })}
                </td>
                <td className="py-3">
                  <span className={`px-2 py-1 rounded text-xs font-medium ${
                    trade.type === 'buy' 
                      ? 'bg-green-500/20 text-green-400' 
                      : 'bg-red-500/20 text-red-400'
                  }`}>
                    {trade.type === 'buy' ? 'COMPRA' : 'VENTA'}
                  </span>
                </td>
                <td className="py-3 text-white font-mono">
                  ${Number(trade.price).toLocaleString('es-ES', { maximumFractionDigits: 0 })}
                </td>
                <td className="py-3 text-gray-300 font-mono text-sm">
                  {Number(trade.btc_amount).toFixed(6)} BTC
                </td>
                <td className="py-3 text-white font-mono">
                  ${Number(trade.usd_amount).toFixed(2)}
                </td>
                <td className="py-3 text-gray-500 font-mono text-sm">
                  ${Number(trade.fee_usd).toFixed(2)}
                </td>
                <td className="py-3 text-gray-400 text-sm">
                  {trade.strategy}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
