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
      <ResponsiveContainer width="100%" height={400}>
        <AreaChart data={chartData}>
          <defs>
            <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#0ea5e9" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#0ea5e9" stopOpacity={0} />
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
            formatter={(value: number) => [formatCurrency(value), 'Price']}
            labelStyle={{ color: 'currentColor' }}
            contentStyle={{
              backgroundColor: 'var(--card-background)',
              border: '1px solid var(--border)',
              borderRadius: '0.5rem',
            }}
          />
          <Area
            type="monotone"
            dataKey="price"
            stroke="#0ea5e9"
            fillOpacity={1}
            fill="url(#colorPrice)"
          />
        </AreaChart>
      </ResponsiveContainer>
    )
  }

  return (
    <ResponsiveContainer width="100%" height={400}>
      <LineChart data={chartData}>
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
          formatter={(value: number) => [formatCurrency(value), 'Price']}
          labelStyle={{ color: 'currentColor' }}
          contentStyle={{
            backgroundColor: 'var(--card-background)',
            border: '1px solid var(--border)',
            borderRadius: '0.5rem',
          }}
        />
        <Line
          type="monotone"
          dataKey="price"
          stroke="#0ea5e9"
          strokeWidth={2}
          dot={false}
        />
      </LineChart>
    </ResponsiveContainer>
  )
}

