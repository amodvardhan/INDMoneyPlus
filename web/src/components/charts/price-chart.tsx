'use client'

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Area,
  AreaChart,
} from 'recharts'
import { formatCurrency, formatDate } from '@/lib/utils'
import type { PricePoint } from '@/lib/api/types'

interface PriceChartProps {
  data: PricePoint[]
  type?: 'line' | 'area'
  showVolume?: boolean
}

export function PriceChart({ data, type = 'line', showVolume = false }: PriceChartProps) {
  const chartData = data.map((point) => ({
    date: formatDate(point.timestamp, 'short'),
    timestamp: point.timestamp,
    price: point.close,
    open: point.open,
    high: point.high,
    low: point.low,
    volume: point.volume,
  }))

  if (type === 'area') {
    return (
      <ResponsiveContainer width="100%" height={450}>
        <AreaChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#0ea5e9" stopOpacity={0.4} />
              <stop offset="95%" stopColor="#0ea5e9" stopOpacity={0.05} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" className="stroke-gray-200 dark:stroke-gray-800" />
          <XAxis
            dataKey="date"
            className="text-xs"
            tick={{ fill: 'currentColor' }}
          />
          <YAxis
            className="text-xs"
            tick={{ fill: 'currentColor' }}
            tickFormatter={(value) => `₹${value.toLocaleString()}`}
          />
          <Tooltip
            content={({ active, payload, label }) => {
              if (active && payload && payload.length) {
                const data = payload[0].payload
                return (
                  <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg p-3">
                    <p className="font-semibold mb-2 text-gray-900 dark:text-white">{label}</p>
                    <div className="space-y-1 text-sm">
                      <div className="flex justify-between gap-4">
                        <span className="text-gray-600 dark:text-gray-400">Close:</span>
                        <span className="font-medium text-gray-900 dark:text-white">{formatCurrency(data.price)}</span>
                      </div>
                      <div className="flex justify-between gap-4">
                        <span className="text-gray-600 dark:text-gray-400">Open:</span>
                        <span className="font-medium text-gray-900 dark:text-white">{formatCurrency(data.open)}</span>
                      </div>
                      <div className="flex justify-between gap-4">
                        <span className="text-gray-600 dark:text-gray-400">High:</span>
                        <span className="font-medium text-green-600">{formatCurrency(data.high)}</span>
                      </div>
                      <div className="flex justify-between gap-4">
                        <span className="text-gray-600 dark:text-gray-400">Low:</span>
                        <span className="font-medium text-red-600">{formatCurrency(data.low)}</span>
                      </div>
                      {data.volume && (
                        <div className="flex justify-between gap-4 pt-1 border-t border-gray-200 dark:border-gray-700">
                          <span className="text-gray-600 dark:text-gray-400">Volume:</span>
                          <span className="font-medium text-gray-900 dark:text-white">{data.volume.toLocaleString()}</span>
                        </div>
                      )}
                    </div>
                  </div>
                )
              }
              return null
            }}
          />
          <Area
            type="monotone"
            dataKey="price"
            stroke="#0ea5e9"
            strokeWidth={2}
            fillOpacity={1}
            fill="url(#colorPrice)"
            dot={false}
            activeDot={{ r: 4, fill: '#0ea5e9' }}
          />
        </AreaChart>
      </ResponsiveContainer>
    )
  }

  return (
    <ResponsiveContainer width="100%" height={450}>
      <LineChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" className="stroke-gray-200 dark:stroke-gray-800" />
        <XAxis
          dataKey="date"
          className="text-xs"
          tick={{ fill: 'currentColor' }}
        />
        <YAxis
          className="text-xs"
          tick={{ fill: 'currentColor' }}
          tickFormatter={(value) => `₹${value.toLocaleString()}`}
        />
        <Tooltip
          content={({ active, payload, label }) => {
            if (active && payload && payload.length) {
              const data = payload[0].payload
              return (
                <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg p-3">
                  <p className="font-semibold mb-2 text-gray-900 dark:text-white">{label}</p>
                  <div className="space-y-1 text-sm">
                    <div className="flex justify-between gap-4">
                      <span className="text-gray-600 dark:text-gray-400">Close:</span>
                      <span className="font-medium text-gray-900 dark:text-white">{formatCurrency(data.price)}</span>
                    </div>
                    <div className="flex justify-between gap-4">
                      <span className="text-gray-600 dark:text-gray-400">Open:</span>
                      <span className="font-medium text-gray-900 dark:text-white">{formatCurrency(data.open)}</span>
                    </div>
                    <div className="flex justify-between gap-4">
                      <span className="text-gray-600 dark:text-gray-400">High:</span>
                      <span className="font-medium text-green-600">{formatCurrency(data.high)}</span>
                    </div>
                    <div className="flex justify-between gap-4">
                      <span className="text-gray-600 dark:text-gray-400">Low:</span>
                      <span className="font-medium text-red-600">{formatCurrency(data.low)}</span>
                    </div>
                    {data.volume && (
                      <div className="flex justify-between gap-4 pt-1 border-t border-gray-200 dark:border-gray-700">
                        <span className="text-gray-600 dark:text-gray-400">Volume:</span>
                        <span className="font-medium text-gray-900 dark:text-white">{data.volume.toLocaleString()}</span>
                      </div>
                    )}
                  </div>
                </div>
              )
            }
            return null
          }}
        />
        <Line
          type="monotone"
          dataKey="price"
          stroke="#0ea5e9"
          strokeWidth={2}
          dot={false}
          activeDot={{ r: 5, fill: '#0ea5e9', strokeWidth: 2 }}
        />
      </LineChart>
    </ResponsiveContainer>
  )
}

