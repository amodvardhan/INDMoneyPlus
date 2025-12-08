'use client'

import {
  ComposedChart,
  Line,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  Legend,
} from 'recharts'
import { formatCurrency, formatDate } from '@/lib/utils'
import type { PricePoint } from '@/lib/api/types'

interface StockChartProps {
  data: PricePoint[]
  type?: 'line' | 'area' | 'candlestick'
  showVolume?: boolean
  showIndicators?: boolean
  periodHigh?: number
  periodLow?: number
}

// Calculate Simple Moving Average
function calculateSMA(data: PricePoint[], period: number): number[] {
  const sma: number[] = []
  for (let i = 0; i < data.length; i++) {
    if (i < period - 1) {
      sma.push(NaN)
    } else {
      const sum = data.slice(i - period + 1, i + 1).reduce((acc, point) => acc + point.close, 0)
      sma.push(sum / period)
    }
  }
  return sma
}

// Calculate RSI (Relative Strength Index)
function calculateRSI(data: PricePoint[], period: number = 14): number[] {
  const rsi: number[] = []
  const changes: number[] = []

  for (let i = 1; i < data.length; i++) {
    changes.push(data[i].close - data[i - 1].close)
  }

  for (let i = 0; i < data.length; i++) {
    if (i < period) {
      rsi.push(NaN)
    } else {
      const recentChanges = changes.slice(i - period, i)
      const gains = recentChanges.filter(c => c > 0).reduce((a, b) => a + b, 0) / period
      const losses = Math.abs(recentChanges.filter(c => c < 0).reduce((a, b) => a + b, 0)) / period

      if (losses === 0) {
        rsi.push(100)
      } else {
        const rs = gains / losses
        rsi.push(100 - (100 / (1 + rs)))
      }
    }
  }

  return rsi
}

// Custom Candlestick component
const Candlestick = ({ x, y, width, height, open, close, high, low }: any) => {
  const isUp = close >= open
  const bodyHeight = Math.abs(close - open)
  const bodyY = Math.min(open, close)
  const wickTop = Math.max(open, close, high)
  const wickBottom = Math.min(open, close, low)

  return (
    <g>
      {/* Wick */}
      <line
        x1={x + width / 2}
        y1={y + (high - wickTop) * height / (high - low)}
        x2={x + width / 2}
        y2={y + (low - wickBottom) * height / (high - low)}
        stroke={isUp ? '#10b981' : '#ef4444'}
        strokeWidth={1}
      />
      {/* Body */}
      <rect
        x={x}
        y={y + (bodyY - wickBottom) * height / (high - low)}
        width={width}
        height={Math.max(bodyHeight * height / (high - low), 2)}
        fill={isUp ? '#10b981' : '#ef4444'}
        stroke={isUp ? '#059669' : '#dc2626'}
        strokeWidth={1}
      />
    </g>
  )
}

export function StockChart({
  data,
  type = 'candlestick',
  showVolume = true,
  showIndicators = true,
  periodHigh,
  periodLow
}: StockChartProps) {
  const chartData = data.map((point, index) => ({
    date: formatDate(point.timestamp, 'short'),
    timestamp: point.timestamp,
    price: point.close,
    open: point.open,
    high: point.high,
    low: point.low,
    volume: point.volume || 0,
    index,
  }))

  // Calculate indicators
  const sma20 = calculateSMA(data, 20)
  const sma50 = calculateSMA(data, 50)
  const rsi = calculateRSI(data, 14)

  const enrichedData = chartData.map((d, i) => ({
    ...d,
    sma20: sma20[i],
    sma50: sma50[i],
    rsi: rsi[i],
  }))

  // Calculate support and resistance levels
  const prices = data.map(d => d.close)
  const support = periodLow || Math.min(...prices) * 0.98
  const resistance = periodHigh || Math.max(...prices) * 1.02

  if (type === 'candlestick') {
    return (
      <div className="space-y-4">
        {/* Price Chart with Candlesticks */}
        <ResponsiveContainer width="100%" height={400}>
          <ComposedChart
            data={enrichedData}
            margin={{ top: 20, right: 30, left: 20, bottom: 0 }}
          >
            <defs>
              <linearGradient id="volumeGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#8884d8" stopOpacity={0.8} />
                <stop offset="95%" stopColor="#8884d8" stopOpacity={0.1} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" className="stroke-gray-200 dark:stroke-gray-800" />
            <XAxis
              dataKey="date"
              className="text-xs"
              tick={{ fill: 'currentColor', fontSize: 11 }}
              angle={-45}
              textAnchor="end"
              height={60}
            />
            <YAxis
              yAxisId="price"
              orientation="left"
              className="text-xs"
              tick={{ fill: 'currentColor', fontSize: 11 }}
              tickFormatter={(value) => `₹${value.toFixed(0)}`}
              domain={['dataMin - 5', 'dataMax + 5']}
            />
            {showVolume && (
              <YAxis
                yAxisId="volume"
                orientation="right"
                className="text-xs"
                tick={{ fill: 'currentColor', fontSize: 11 }}
                tickFormatter={(value) => `${(value / 1000000).toFixed(1)}M`}
              />
            )}
            <Tooltip
              content={({ active, payload, label }) => {
                if (active && payload && payload.length) {
                  const data = payload[0].payload
                  return (
                    <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-xl p-4 min-w-[200px]">
                      <p className="font-semibold mb-3 text-gray-900 dark:text-white border-b border-gray-200 dark:border-gray-700 pb-2">
                        {label}
                      </p>
                      <div className="space-y-2 text-sm">
                        <div className="grid grid-cols-2 gap-3">
                          <div>
                            <div className="text-gray-600 dark:text-gray-400 text-xs mb-1">Open</div>
                            <div className="font-semibold text-gray-900 dark:text-white">{formatCurrency(data.open)}</div>
                          </div>
                          <div>
                            <div className="text-gray-600 dark:text-gray-400 text-xs mb-1">Close</div>
                            <div className={`font-semibold ${data.close >= data.open ? 'text-green-600' : 'text-red-600'}`}>
                              {formatCurrency(data.close)}
                            </div>
                          </div>
                          <div>
                            <div className="text-gray-600 dark:text-gray-400 text-xs mb-1">High</div>
                            <div className="font-semibold text-green-600">{formatCurrency(data.high)}</div>
                          </div>
                          <div>
                            <div className="text-gray-600 dark:text-gray-400 text-xs mb-1">Low</div>
                            <div className="font-semibold text-red-600">{formatCurrency(data.low)}</div>
                          </div>
                        </div>
                        {data.volume > 0 && (
                          <div className="pt-2 border-t border-gray-200 dark:border-gray-700">
                            <div className="text-gray-600 dark:text-gray-400 text-xs mb-1">Volume</div>
                            <div className="font-semibold text-gray-900 dark:text-white">{data.volume.toLocaleString()}</div>
                          </div>
                        )}
                        {showIndicators && data.sma20 && !isNaN(data.sma20) && (
                          <div className="pt-2 border-t border-gray-200 dark:border-gray-700 space-y-1">
                            <div className="flex justify-between text-xs">
                              <span className="text-gray-600 dark:text-gray-400">SMA 20:</span>
                              <span className="font-medium">{formatCurrency(data.sma20)}</span>
                            </div>
                            {data.sma50 && !isNaN(data.sma50) && (
                              <div className="flex justify-between text-xs">
                                <span className="text-gray-600 dark:text-gray-400">SMA 50:</span>
                                <span className="font-medium">{formatCurrency(data.sma50)}</span>
                              </div>
                            )}
                            {data.rsi && !isNaN(data.rsi) && (
                              <div className="flex justify-between text-xs">
                                <span className="text-gray-600 dark:text-gray-400">RSI:</span>
                                <span className={`font-medium ${data.rsi > 70 ? 'text-red-600' : data.rsi < 30 ? 'text-green-600' : 'text-gray-600'
                                  }`}>
                                  {data.rsi.toFixed(1)}
                                </span>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  )
                }
                return null
              }}
            />
            {/* Support and Resistance Lines */}
            <ReferenceLine
              yAxisId="price"
              y={support}
              stroke="#10b981"
              strokeDasharray="5 5"
              label={{ value: 'Support', position: 'right', fill: '#10b981', fontSize: 10 }}
            />
            <ReferenceLine
              yAxisId="price"
              y={resistance}
              stroke="#ef4444"
              strokeDasharray="5 5"
              label={{ value: 'Resistance', position: 'right', fill: '#ef4444', fontSize: 10 }}
            />
            {/* Moving Averages */}
            {showIndicators && (
              <>
                <Line
                  yAxisId="price"
                  type="monotone"
                  dataKey="sma20"
                  stroke="#f59e0b"
                  strokeWidth={1.5}
                  dot={false}
                  strokeDasharray="3 3"
                  name="SMA 20"
                />
                <Line
                  yAxisId="price"
                  type="monotone"
                  dataKey="sma50"
                  stroke="#8b5cf6"
                  strokeWidth={1.5}
                  dot={false}
                  strokeDasharray="3 3"
                  name="SMA 50"
                />
              </>
            )}
            {/* Candlestick representation using bars and lines */}
            {enrichedData.map((d, i) => {
              const isUp = d.close >= d.open
              const bodyHeight = Math.abs(d.close - d.open)
              const maxPrice = Math.max(...enrichedData.map(x => x.high))
              const minPrice = Math.min(...enrichedData.map(x => x.low))
              const range = maxPrice - minPrice

              return (
                <g key={i}>
                  {/* Wick */}
                  <line
                    x1={i * (100 / enrichedData.length) + 2}
                    y1={((maxPrice - d.high) / range) * 400}
                    x2={i * (100 / enrichedData.length) + 2}
                    y2={((maxPrice - d.low) / range) * 400}
                    stroke={isUp ? '#10b981' : '#ef4444'}
                    strokeWidth={1}
                  />
                  {/* Body */}
                  <rect
                    x={i * (100 / enrichedData.length)}
                    y={((maxPrice - Math.max(d.open, d.close)) / range) * 400}
                    width={100 / enrichedData.length - 2}
                    height={Math.max((bodyHeight / range) * 400, 2)}
                    fill={isUp ? '#10b981' : '#ef4444'}
                    stroke={isUp ? '#059669' : '#dc2626'}
                    strokeWidth={1}
                  />
                </g>
              )
            })}
            {/* Volume bars */}
            {showVolume && (
              <Bar
                yAxisId="volume"
                dataKey="volume"
                fill="url(#volumeGradient)"
                opacity={0.6}
              />
            )}
            <Legend />
          </ComposedChart>
        </ResponsiveContainer>

        {/* Volume Chart */}
        {showVolume && (
          <ResponsiveContainer width="100%" height={120}>
            <ComposedChart data={enrichedData} margin={{ top: 5, right: 30, left: 20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-gray-200 dark:stroke-gray-800" />
              <XAxis
                dataKey="date"
                className="text-xs"
                tick={{ fill: 'currentColor', fontSize: 10 }}
                angle={-45}
                textAnchor="end"
                height={60}
              />
              <YAxis
                className="text-xs"
                tick={{ fill: 'currentColor', fontSize: 10 }}
                tickFormatter={(value) => `${(value / 1000000).toFixed(1)}M`}
              />
              <Tooltip
                formatter={(value: number) => [value.toLocaleString(), 'Volume']}
                labelStyle={{ color: 'currentColor', fontSize: 11 }}
              />
              <Bar dataKey="volume" fill="#8884d8" opacity={0.7} />
            </ComposedChart>
          </ResponsiveContainer>
        )}

        {/* RSI Indicator */}
        {showIndicators && (
          <ResponsiveContainer width="100%" height={100}>
            <ComposedChart data={enrichedData} margin={{ top: 5, right: 30, left: 20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-gray-200 dark:stroke-gray-800" />
              <XAxis
                dataKey="date"
                className="text-xs"
                tick={{ fill: 'currentColor', fontSize: 10 }}
                angle={-45}
                textAnchor="end"
                height={60}
              />
              <YAxis domain={[0, 100]} className="text-xs" tick={{ fill: 'currentColor', fontSize: 10 }} />
              <ReferenceLine y={70} stroke="#ef4444" strokeDasharray="3 3" label="Overbought" />
              <ReferenceLine y={30} stroke="#10b981" strokeDasharray="3 3" label="Oversold" />
              <Tooltip
                formatter={(value: number) => [value.toFixed(1), 'RSI']}
                labelStyle={{ color: 'currentColor', fontSize: 11 }}
              />
              <Line
                type="monotone"
                dataKey="rsi"
                stroke="#8b5cf6"
                strokeWidth={2}
                dot={false}
                name="RSI (14)"
              />
            </ComposedChart>
          </ResponsiveContainer>
        )}
      </div>
    )
  }

  // Fallback to existing line/area chart
  return null
}
