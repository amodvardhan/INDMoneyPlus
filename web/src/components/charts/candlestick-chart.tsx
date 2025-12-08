'use client'

import { useMemo, memo, useRef, useEffect } from 'react'
import {
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  Cell,
} from 'recharts'
import { formatCurrency, formatDate } from '@/lib/utils'
import type { PricePoint } from '@/lib/api/types'

interface CandlestickChartProps {
  data: PricePoint[]
  showVolume?: boolean
  showIndicators?: boolean
  periodHigh?: number
  periodLow?: number
}

// Memoized calculation functions for performance
const calculateSMA = (data: PricePoint[], period: number): number[] => {
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

const calculateRSI = (data: PricePoint[], period: number = 14): number[] => {
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

// Custom tooltip component with theme support
const CustomTooltip = memo(({ active, payload, label }: any) => {
  if (!active || !payload || !payload.length) return null

  const data = payload[0].payload
  const isUp = data.close >= data.open

  return (
    <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg shadow-xl p-3 min-w-[200px]">
      <p className="font-semibold mb-2 text-gray-900 dark:text-white text-sm border-b border-gray-200 dark:border-gray-700 pb-2">
        {label}
      </p>
      <div className="space-y-1.5 text-xs">
        <div className="grid grid-cols-2 gap-2">
          <div>
            <div className="text-gray-600 dark:text-gray-400 text-xs mb-0.5">Open</div>
            <div className="font-semibold text-gray-900 dark:text-white">{formatCurrency(data.open)}</div>
          </div>
          <div>
            <div className="text-gray-600 dark:text-gray-400 text-xs mb-0.5">Close</div>
            <div className={`font-semibold ${isUp ? 'text-green-600 dark:text-green-400' : 'text-gray-700 dark:text-gray-400'}`}>
              {formatCurrency(data.close)}
            </div>
          </div>
          <div>
            <div className="text-gray-600 dark:text-gray-400 text-xs mb-0.5">High</div>
            <div className="font-semibold text-green-600 dark:text-green-400">{formatCurrency(data.high)}</div>
          </div>
          <div>
            <div className="text-gray-600 dark:text-gray-400 text-xs mb-0.5">Low</div>
            <div className="font-semibold text-red-600 dark:text-red-400">{formatCurrency(data.low)}</div>
          </div>
        </div>
        {data.volume > 0 && (
          <div className="pt-2 border-t border-gray-200 dark:border-gray-700">
            <div className="text-gray-600 dark:text-gray-400 text-xs mb-0.5">Volume</div>
            <div className="font-semibold text-gray-900 dark:text-white">{data.volume.toLocaleString()}</div>
          </div>
        )}
      </div>
    </div>
  )
})

CustomTooltip.displayName = 'CustomTooltip'

export const CandlestickChart = memo(function CandlestickChart({
  data,
  showVolume = true,
  showIndicators = true,
  periodHigh,
  periodLow
}: CandlestickChartProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)

  // Memoize chart data processing for performance
  const chartData = useMemo(() => {
    if (!data || data.length === 0) return []

    return data.map((point) => ({
      date: formatDate(point.timestamp, 'short'),
      timestamp: point.timestamp,
      open: point.open,
      high: point.high,
      low: point.low,
      close: point.close,
      volume: point.volume || 0,
      isUp: point.close >= point.open,
    }))
  }, [data])

  // Calculate indicators
  const indicators = useMemo(() => {
    if (!data || data.length === 0) return { sma20: [], sma50: [], rsi: [] }

    return {
      sma20: calculateSMA(data, 20),
      sma50: calculateSMA(data, 50),
      rsi: calculateRSI(data, 14),
    }
  }, [data])

  // Enrich chart data with indicators
  const enrichedData = useMemo(() => {
    return chartData.map((d, i) => ({
      ...d,
      sma20: indicators.sma20[i],
      sma50: indicators.sma50[i],
      rsi: indicators.rsi[i],
    }))
  }, [chartData, indicators])

  // Calculate price range for Y-axis
  const priceRange = useMemo(() => {
    if (enrichedData.length === 0) return { min: 0, max: 0 }
    const highs = enrichedData.map(d => d.high)
    const lows = enrichedData.map(d => d.low)
    const min = Math.min(...lows)
    const max = Math.max(...highs)
    const padding = (max - min) * 0.05
    return {
      min: Math.max(0, min - padding),
      max: max + padding,
    }
  }, [enrichedData])

  // Render candlesticks on canvas overlay - optimized and aligned with chart
  useEffect(() => {
    if (!canvasRef.current || !enrichedData.length || !containerRef.current) return

    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const redraw = () => {
      const container = containerRef.current
      if (!container) return

      const rect = container.getBoundingClientRect()
      const dpr = window.devicePixelRatio || 1
      canvas.width = rect.width * dpr
      canvas.height = 500 * dpr
      canvas.style.width = `${rect.width}px`
      canvas.style.height = '500px'
      ctx.scale(dpr, dpr)

      // Clear canvas
      ctx.clearRect(0, 0, rect.width, 500)

      // Calculate scales matching Recharts margins
      const margin = { top: 20, right: 30, left: 70, bottom: 20 }
      const chartWidth = rect.width - margin.left - margin.right
      const chartHeight = 500 - margin.top - margin.bottom

      const xScale = (index: number) => {
        if (enrichedData.length === 1) return margin.left + chartWidth / 2
        return margin.left + (index / (enrichedData.length - 1)) * chartWidth
      }
      const yScale = (price: number) => {
        const range = priceRange.max - priceRange.min
        if (range === 0) return margin.top + chartHeight / 2
        return margin.top + chartHeight - ((price - priceRange.min) / range) * chartHeight
      }

      const candleWidth = Math.max(4, Math.min(10, chartWidth / enrichedData.length * 0.7))

      // Draw candlesticks
      enrichedData.forEach((entry, index) => {
        const isUp = entry.close >= entry.open
        const bodyTop = Math.max(entry.open, entry.close)
        const bodyBottom = Math.min(entry.open, entry.close)

        const x = xScale(index)
        const highY = yScale(entry.high)
        const lowY = yScale(entry.low)
        const bodyTopY = yScale(bodyTop)
        const bodyBottomY = yScale(bodyBottom)

        // Colors: teal for bullish, dark grey for bearish (matching reference)
        const upColor = '#10b981'
        const downColor = '#6b7280'
        const color = isUp ? upColor : downColor
        const borderColor = isUp ? '#059669' : '#4b5563'

        // Draw wick (high-low line)
        ctx.strokeStyle = color
        ctx.lineWidth = 1.5
        ctx.lineCap = 'round'
        ctx.beginPath()
        ctx.moveTo(x, highY)
        ctx.lineTo(x, lowY)
        ctx.stroke()

        // Draw body
        const bodyHeight = Math.max(Math.abs(bodyTopY - bodyBottomY), 2)
        ctx.fillStyle = color
        ctx.strokeStyle = borderColor
        ctx.lineWidth = 1
        ctx.fillRect(x - candleWidth / 2, bodyTopY, candleWidth, bodyHeight)
        ctx.strokeRect(x - candleWidth / 2, bodyTopY, candleWidth, bodyHeight)
      })
    }

    redraw()
    window.addEventListener('resize', redraw)
    return () => window.removeEventListener('resize', redraw)
  }, [enrichedData, priceRange])

  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-96 text-gray-500 dark:text-gray-400">
        <div className="text-center">
          <p className="text-lg font-medium">No data available</p>
          <p className="text-sm mt-2">Please select a different time period</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4 w-full" ref={containerRef}>
      {/* Main Candlestick Chart */}
      <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-4 shadow-sm relative">
        {/* Canvas overlay for candlesticks */}
        <canvas
          ref={canvasRef}
          className="absolute pointer-events-none z-10"
          style={{
            top: '20px',
            left: '20px',
            right: '30px',
            bottom: '20px',
            width: 'calc(100% - 50px)',
            height: 'calc(100% - 40px)'
          }}
        />
        <ResponsiveContainer width="100%" height={500}>
          <ComposedChart
            data={enrichedData}
            margin={{ top: 20, right: 30, left: 20, bottom: 20 }}
          >
            <defs>
              <linearGradient id="volumeGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#8884d8" stopOpacity={0.4} />
                <stop offset="95%" stopColor="#8884d8" stopOpacity={0.1} />
              </linearGradient>
            </defs>
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="#e5e7eb"
              className="dark:stroke-gray-800"
              opacity={0.5}
            />
            <XAxis
              dataKey="date"
              tick={{ fill: '#6b7280', fontSize: 11 }}
              axisLine={{ stroke: '#e5e7eb' }}
              tickLine={{ stroke: '#e5e7eb' }}
              interval="preserveStartEnd"
              minTickGap={50}
            />
            <YAxis
              yAxisId="price"
              orientation="left"
              tick={{ fill: '#6b7280', fontSize: 11 }}
              tickFormatter={(value) => `₹${value.toFixed(0)}`}
              domain={[priceRange.min, priceRange.max]}
              width={70}
              axisLine={{ stroke: '#e5e7eb' }}
              tickLine={{ stroke: '#e5e7eb' }}
            />
            {showVolume && (
              <YAxis
                yAxisId="volume"
                orientation="right"
                tick={{ fill: '#6b7280', fontSize: 10 }}
                tickFormatter={(value) => `${(value / 1000000).toFixed(1)}M`}
                width={50}
                axisLine={{ stroke: '#e5e7eb' }}
                tickLine={{ stroke: '#e5e7eb' }}
              />
            )}
            <Tooltip content={<CustomTooltip />} />

            {/* Support and Resistance Lines */}
            {showIndicators && (
              <>
                <ReferenceLine
                  yAxisId="price"
                  y={periodLow || Math.min(...enrichedData.map(d => d.low)) * 0.98}
                  stroke="#10b981"
                  strokeDasharray="5 5"
                  strokeWidth={1.5}
                  opacity={0.4}
                />
                <ReferenceLine
                  yAxisId="price"
                  y={periodHigh || Math.max(...enrichedData.map(d => d.high)) * 1.02}
                  stroke="#ef4444"
                  strokeDasharray="5 5"
                  strokeWidth={1.5}
                  opacity={0.4}
                />
              </>
            )}

            {/* Moving Averages - Yellow/Gold line matching reference */}
            {showIndicators && (
              <>
                <Line
                  yAxisId="price"
                  type="monotone"
                  dataKey="sma20"
                  stroke="#fbbf24"
                  strokeWidth={2}
                  dot={false}
                  strokeDasharray="0"
                  opacity={0.8}
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
                  opacity={0.6}
                  name="SMA 50"
                />
              </>
            )}

            {/* Hidden line for tooltip interaction */}
            <Line
              yAxisId="price"
              type="monotone"
              dataKey="close"
              stroke="transparent"
              strokeWidth={0}
              dot={false}
              activeDot={{ r: 4, fill: '#0ea5e9', strokeWidth: 2 }}
            />

            {/* Volume bars */}
            {showVolume && (
              <Bar yAxisId="volume" dataKey="volume" fill="url(#volumeGradient)" opacity={0.3} radius={[2, 2, 0, 0]}>
                {enrichedData.map((entry, index) => (
                  <Cell key={`volume-cell-${index}`} fill={entry.isUp ? '#10b981' : '#6b7280'} />
                ))}
              </Bar>
            )}
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      {/* Volume Chart */}
      {showVolume && (
        <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-4 shadow-sm">
          <ResponsiveContainer width="100%" height={100}>
            <ComposedChart data={enrichedData} margin={{ top: 5, right: 30, left: 20, bottom: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" className="dark:stroke-gray-800" opacity={0.5} />
              <XAxis
                dataKey="date"
                tick={{ fill: '#6b7280', fontSize: 10 }}
                axisLine={{ stroke: '#e5e7eb' }}
                tickLine={{ stroke: '#e5e7eb' }}
                interval="preserveStartEnd"
                minTickGap={50}
              />
              <YAxis
                tick={{ fill: '#6b7280', fontSize: 10 }}
                tickFormatter={(value) => `${(value / 1000000).toFixed(1)}M`}
                axisLine={{ stroke: '#e5e7eb' }}
                tickLine={{ stroke: '#e5e7eb' }}
              />
              <Tooltip
                formatter={(value: number) => [value.toLocaleString(), 'Volume']}
                labelStyle={{ color: '#374151', fontSize: 11 }}
                contentStyle={{ backgroundColor: '#ffffff', border: '1px solid #e5e7eb' }}
                wrapperStyle={{ backgroundColor: 'transparent' }}
              />
              <Bar dataKey="volume" radius={[2, 2, 0, 0]}>
                {enrichedData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.isUp ? '#10b981' : '#6b7280'} />
                ))}
              </Bar>
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* RSI Indicator */}
      {showIndicators && (
        <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-4 shadow-sm">
          <ResponsiveContainer width="100%" height={80}>
            <ComposedChart data={enrichedData} margin={{ top: 5, right: 30, left: 20, bottom: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" className="dark:stroke-gray-800" opacity={0.5} />
              <XAxis
                dataKey="date"
                tick={{ fill: '#6b7280', fontSize: 10 }}
                axisLine={{ stroke: '#e5e7eb' }}
                tickLine={{ stroke: '#e5e7eb' }}
                interval="preserveStartEnd"
                minTickGap={50}
              />
              <YAxis domain={[0, 100]} tick={{ fill: '#6b7280', fontSize: 10 }} axisLine={{ stroke: '#e5e7eb' }} tickLine={{ stroke: '#e5e7eb' }} />
              <ReferenceLine y={70} stroke="#ef4444" strokeDasharray="3 3" opacity={0.5} />
              <ReferenceLine y={30} stroke="#10b981" strokeDasharray="3 3" opacity={0.5} />
              <Tooltip
                formatter={(value: number) => [value.toFixed(1), 'RSI']}
                labelStyle={{ color: '#374151', fontSize: 11 }}
                contentStyle={{ backgroundColor: '#ffffff', border: '1px solid #e5e7eb' }}
                wrapperStyle={{ backgroundColor: 'transparent' }}
              />
              <Line
                type="monotone"
                dataKey="rsi"
                stroke="#8b5cf6"
                strokeWidth={2}
                dot={false}
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  )
})
