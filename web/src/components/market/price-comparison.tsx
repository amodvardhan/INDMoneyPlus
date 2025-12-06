'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { TrendingUp, TrendingDown, ArrowRightLeft, Info } from 'lucide-react'
import { formatCurrency } from '@/lib/utils'
import { motion } from 'framer-motion'
import { cn } from '@/lib/utils'

export interface PriceComparisonData {
  ticker: string
  prices: {
    NSE?: {
      price: number
      change: number
      change_percent: number
      volume: number | null
      high: number
      low: number
      timestamp: string
    }
    BSE?: {
      price: number
      change: number
      change_percent: number
      volume: number | null
      high: number
      low: number
      timestamp: string
    }
  }
  arbitrage?: {
    difference: number
    difference_percent: number
    cheaper_exchange: 'NSE' | 'BSE'
    opportunity: 'Significant' | 'Minor' | 'None'
  }
  recommendation?: string
}

interface PriceComparisonProps {
  data: PriceComparisonData | null
  isLoading?: boolean
}

export function PriceComparison({ data, isLoading }: PriceComparisonProps) {
  if (isLoading || !data) {
    return (
      <Card className="border-2 shadow-lg">
        <CardHeader>
          <CardTitle className="text-xl">Price Comparison</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="animate-pulse space-y-4">
            <div className="h-20 bg-gray-200 rounded"></div>
            <div className="h-20 bg-gray-200 rounded"></div>
          </div>
        </CardContent>
      </Card>
    )
  }

  const hasNSE = !!data.prices.NSE
  const hasBSE = !!data.prices.BSE
  const hasBoth = hasNSE && hasBSE

  return (
    <Card className="border-2 shadow-lg">
      <CardHeader>
        <CardTitle className="text-xl flex items-center gap-2">
          <ArrowRightLeft className="h-5 w-5" />
          {data.ticker} - Exchange Comparison
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* NSE Price */}
          {hasNSE && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="p-4 border-2 border-blue-200 dark:border-blue-800 rounded-lg bg-blue-50/50 dark:bg-blue-900/20"
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <Badge variant="outline" className="bg-blue-100 text-blue-700 border-blue-300">
                    NSE
                  </Badge>
                  <span className="text-sm text-gray-600 dark:text-gray-400">
                    National Stock Exchange
                  </span>
                </div>
                {data.prices.NSE!.change_percent >= 0 ? (
                  <TrendingUp className="h-5 w-5 text-green-600" />
                ) : (
                  <TrendingDown className="h-5 w-5 text-red-600" />
                )}
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">Current Price</div>
                  <div className="text-2xl font-bold text-gray-900 dark:text-white">
                    ₹{data.prices.NSE!.price.toFixed(2)}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">Change</div>
                  <div className={cn(
                    'text-xl font-semibold',
                    data.prices.NSE!.change_percent >= 0 ? 'text-green-600' : 'text-red-600'
                  )}>
                    {data.prices.NSE!.change_percent >= 0 ? '+' : ''}
                    {data.prices.NSE!.change_percent.toFixed(2)}%
                  </div>
                </div>
                <div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">High</div>
                  <div className="text-lg font-medium text-gray-900 dark:text-white">
                    ₹{data.prices.NSE!.high.toFixed(2)}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">Low</div>
                  <div className="text-lg font-medium text-gray-900 dark:text-white">
                    ₹{data.prices.NSE!.low.toFixed(2)}
                  </div>
                </div>
              </div>
              {data.prices.NSE!.volume && (
                <div className="mt-2 text-xs text-gray-500 dark:text-gray-400">
                  Volume: {data.prices.NSE!.volume.toLocaleString()}
                </div>
              )}
            </motion.div>
          )}

          {/* BSE Price */}
          {hasBSE && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="p-4 border-2 border-orange-200 dark:border-orange-800 rounded-lg bg-orange-50/50 dark:bg-orange-900/20"
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <Badge variant="outline" className="bg-orange-100 text-orange-700 border-orange-300">
                    BSE
                  </Badge>
                  <span className="text-sm text-gray-600 dark:text-gray-400">
                    Bombay Stock Exchange
                  </span>
                </div>
                {data.prices.BSE!.change_percent >= 0 ? (
                  <TrendingUp className="h-5 w-5 text-green-600" />
                ) : (
                  <TrendingDown className="h-5 w-5 text-red-600" />
                )}
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">Current Price</div>
                  <div className="text-2xl font-bold text-gray-900 dark:text-white">
                    ₹{data.prices.BSE!.price.toFixed(2)}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">Change</div>
                  <div className={cn(
                    'text-xl font-semibold',
                    data.prices.BSE!.change_percent >= 0 ? 'text-green-600' : 'text-red-600'
                  )}>
                    {data.prices.BSE!.change_percent >= 0 ? '+' : ''}
                    {data.prices.BSE!.change_percent.toFixed(2)}%
                  </div>
                </div>
                <div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">High</div>
                  <div className="text-lg font-medium text-gray-900 dark:text-white">
                    ₹{data.prices.BSE!.high.toFixed(2)}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">Low</div>
                  <div className="text-lg font-medium text-gray-900 dark:text-white">
                    ₹{data.prices.BSE!.low.toFixed(2)}
                  </div>
                </div>
              </div>
              {data.prices.BSE!.volume && (
                <div className="mt-2 text-xs text-gray-500 dark:text-gray-400">
                  Volume: {data.prices.BSE!.volume.toLocaleString()}
                </div>
              )}
            </motion.div>
          )}

          {/* Arbitrage Opportunity */}
          {hasBoth && data.arbitrage && data.arbitrage.opportunity !== 'None' && (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className={cn(
                'p-4 rounded-lg border-2 flex items-start gap-3',
                data.arbitrage.opportunity === 'Significant'
                  ? 'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-300 dark:border-yellow-700'
                  : 'bg-blue-50 dark:bg-blue-900/20 border-blue-300 dark:border-blue-700'
              )}
            >
              <Info className="h-5 w-5 text-yellow-600 mt-0.5 flex-shrink-0" />
              <div className="flex-1">
                <div className="font-semibold text-gray-900 dark:text-white mb-1">
                  Arbitrage Opportunity
                </div>
                <p className="text-sm text-gray-700 dark:text-gray-300 mb-2">
                  Price difference of ₹{data.arbitrage.difference.toFixed(2)} (
                  {data.arbitrage.difference_percent.toFixed(2)}%) between exchanges.
                </p>
                <p className="text-sm font-medium text-gray-900 dark:text-white">
                  💡 Consider buying on <strong>{data.arbitrage.cheaper_exchange}</strong> for better value.
                </p>
              </div>
            </motion.div>
          )}

          {/* Recommendation */}
          {data.recommendation && (
            <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg text-sm text-gray-700 dark:text-gray-300">
              {data.recommendation}
            </div>
          )}

          {/* Educational Note */}
          {hasBoth && (
            <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
              <p className="text-xs text-blue-800 dark:text-blue-200">
                <strong>Note:</strong> Many stocks trade on both NSE and BSE. Prices may differ slightly due to
                liquidity and trading volumes. Always check both exchanges before making investment decisions.
              </p>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}

