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

interface NetWorthDataPoint {
  date: string
  value: number
}

interface NetWorthChartProps {
  data: NetWorthDataPoint[]
}

export function NetWorthChart({ data }: NetWorthChartProps) {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <AreaChart data={data}>
        <defs>
          <linearGradient id="colorNetWorth" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#22c55e" stopOpacity={0.3} />
            <stop offset="95%" stopColor="#22c55e" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" className="stroke-gray-200 dark:stroke-gray-800" />
        <XAxis
          dataKey="date"
          className="text-xs"
          tick={{ fill: 'currentColor' }}
          tickFormatter={(value) => formatDate(value, 'short')}
        />
        <YAxis
          className="text-xs"
          tick={{ fill: 'currentColor' }}
          tickFormatter={(value) => formatCurrency(value, 'INR').replace('₹', '₹')}
        />
        <Tooltip
          formatter={(value: number) => [formatCurrency(value), 'Net Worth']}
          labelStyle={{ color: 'currentColor' }}
          contentStyle={{
            backgroundColor: 'var(--card-background)',
            border: '1px solid var(--border)',
            borderRadius: '0.5rem',
          }}
        />
        <Area
          type="monotone"
          dataKey="value"
          stroke="#22c55e"
          fillOpacity={1}
          fill="url(#colorNetWorth)"
          strokeWidth={2}
        />
      </AreaChart>
    </ResponsiveContainer>
  )
}

