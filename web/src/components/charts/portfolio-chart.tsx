'use client'

import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts'
import { formatCurrency } from '@/lib/utils'

interface PortfolioChartData {
  name: string
  value: number
  color: string
}

interface PortfolioChartProps {
  data: PortfolioChartData[]
  totalValue: number
}

const COLORS = [
  '#0ea5e9',
  '#22c55e',
  '#f59e0b',
  '#ef4444',
  '#8b5cf6',
  '#ec4899',
  '#14b8a6',
  '#f97316',
]

export function PortfolioChart({ data, totalValue }: PortfolioChartProps) {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          labelLine={false}
          label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
          outerRadius={100}
          fill="#8884d8"
          dataKey="value"
        >
          {data.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={entry.color || COLORS[index % COLORS.length]} />
          ))}
        </Pie>
        <Tooltip
          formatter={(value: number) => [
            formatCurrency(value),
            'Value',
          ]}
        />
        <Legend />
      </PieChart>
    </ResponsiveContainer>
  )
}

