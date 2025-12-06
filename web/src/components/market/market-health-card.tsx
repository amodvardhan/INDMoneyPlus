'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { TrendingUp, TrendingDown, Activity, AlertCircle, CheckCircle2 } from 'lucide-react'
import { motion } from 'framer-motion'
import { cn } from '@/lib/utils'

export interface MarketHealthData {
  condition: 'strong_bull' | 'bull' | 'neutral' | 'bear' | 'strong_bear'
  health_score: number
  sentiment: string
  overall_change_percent: number
  volatility: 'Low' | 'Medium' | 'High'
  recommendation: string
  last_updated: string
  indices?: Array<{
    name: string
    ticker: string
    exchange: string
    current_value: number
    change: number
    change_percent: number
    trend: string
  }>
}

interface MarketHealthCardProps {
  data: MarketHealthData | null
  isLoading?: boolean
}

export function MarketHealthCard({ data, isLoading }: MarketHealthCardProps) {
  if (isLoading || !data) {
    return (
      <Card className="border-2 shadow-lg">
        <CardHeader>
          <CardTitle className="text-xl">Market Health</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="animate-pulse space-y-4">
            <div className="h-8 bg-gray-200 rounded"></div>
            <div className="h-4 bg-gray-200 rounded"></div>
          </div>
        </CardContent>
      </Card>
    )
  }

  const getConditionColor = () => {
    switch (data.condition) {
      case 'strong_bull':
        return 'from-green-500 to-emerald-600'
      case 'bull':
        return 'from-green-400 to-green-500'
      case 'neutral':
        return 'from-gray-400 to-gray-500'
      case 'bear':
        return 'from-orange-400 to-orange-500'
      case 'strong_bear':
        return 'from-red-500 to-red-600'
      default:
        return 'from-gray-400 to-gray-500'
    }
  }

  const getConditionLabel = () => {
    switch (data.condition) {
      case 'strong_bull':
        return 'Strong Bull Market'
      case 'bull':
        return 'Bull Market'
      case 'neutral':
        return 'Neutral Market'
      case 'bear':
        return 'Bear Market'
      case 'strong_bear':
        return 'Strong Bear Market'
      default:
        return 'Unknown'
    }
  }

  const getVolatilityColor = () => {
    switch (data.volatility) {
      case 'Low':
        return 'bg-green-100 text-green-700 border-green-200'
      case 'Medium':
        return 'bg-yellow-100 text-yellow-700 border-yellow-200'
      case 'High':
        return 'bg-red-100 text-red-700 border-red-200'
      default:
        return 'bg-gray-100 text-gray-700 border-gray-200'
    }
  }

  const healthPercentage = Math.round(data.health_score)
  const isPositive = data.overall_change_percent >= 0

  return (
    <Card className="border-2 shadow-lg">
      <CardHeader className="bg-gradient-to-r from-white to-gray-50 dark:from-gray-900 dark:to-gray-800 border-b">
        <div className="flex items-center justify-between">
          <CardTitle className="text-xl flex items-center gap-2">
            <Activity className="h-5 w-5" />
            Market Health
          </CardTitle>
          <Badge
            className={cn(
              'px-3 py-1 text-sm font-semibold',
              getVolatilityColor()
            )}
          >
            {data.volatility} Volatility
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="pt-6">
        <div className="space-y-6">
          {/* Main Health Indicator */}
          <div className="text-center">
            <motion.div
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              className={cn(
                'inline-flex items-center justify-center w-32 h-32 rounded-full bg-gradient-to-br shadow-xl mb-4',
                getConditionColor()
              )}
            >
              <div className="text-center">
                <div className="text-4xl font-bold text-white">{healthPercentage}</div>
                <div className="text-xs text-white/90 mt-1">Health Score</div>
              </div>
            </motion.div>
            <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
              {getConditionLabel()}
            </h3>
            <p className="text-gray-600 dark:text-gray-400">{data.sentiment}</p>
          </div>

          {/* Overall Change */}
          <div className="flex items-center justify-center gap-2 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
            {isPositive ? (
              <TrendingUp className="h-6 w-6 text-green-600" />
            ) : (
              <TrendingDown className="h-6 w-6 text-red-600" />
            )}
            <div className="text-center">
              <div className={cn(
                'text-2xl font-bold',
                isPositive ? 'text-green-600' : 'text-red-600'
              )}>
                {isPositive ? '+' : ''}{data.overall_change_percent.toFixed(2)}%
              </div>
              <div className="text-sm text-gray-500 dark:text-gray-400">Overall Change</div>
            </div>
          </div>

          {/* Recommendation */}
          <div className={cn(
            'p-4 rounded-lg border-2 flex items-start gap-3',
            data.recommendation === 'Buy' || data.recommendation === 'Hold'
              ? 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800'
              : 'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800'
          )}>
            {data.recommendation === 'Buy' ? (
              <CheckCircle2 className="h-5 w-5 text-green-600 mt-0.5" />
            ) : (
              <AlertCircle className="h-5 w-5 text-yellow-600 mt-0.5" />
            )}
            <div>
              <div className="font-semibold text-gray-900 dark:text-white mb-1">
                Recommendation: {data.recommendation}
              </div>
              <p className="text-sm text-gray-700 dark:text-gray-300">
                {data.recommendation === 'Buy'
                  ? 'Market conditions are favorable for investments. Consider buying opportunities.'
                  : data.recommendation === 'Hold'
                  ? 'Market is stable. Maintain current positions and monitor closely.'
                  : 'Exercise caution. Market conditions suggest waiting or reducing exposure.'}
              </p>
            </div>
          </div>

          {/* Indices Performance */}
          {data.indices && data.indices.length > 0 && (
            <div className="space-y-3">
              <h4 className="font-semibold text-gray-900 dark:text-white">Major Indices</h4>
              {data.indices.map((index, idx) => {
                const isIndexPositive = index.change_percent >= 0
                return (
                  <motion.div
                    key={idx}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: idx * 0.1 }}
                    className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg"
                  >
                    <div>
                      <div className="font-medium text-gray-900 dark:text-white">
                        {index.name}
                      </div>
                      <div className="text-xs text-gray-500 dark:text-gray-400">
                        {index.ticker} • {index.exchange}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="font-bold text-gray-900 dark:text-white">
                        {index.current_value.toLocaleString('en-IN', {
                          maximumFractionDigits: 2,
                        })}
                      </div>
                      <div className={cn(
                        'text-sm font-medium flex items-center gap-1',
                        isIndexPositive ? 'text-green-600' : 'text-red-600'
                      )}>
                        {isIndexPositive ? (
                          <TrendingUp className="h-3 w-3" />
                        ) : (
                          <TrendingDown className="h-3 w-3" />
                        )}
                        {isIndexPositive ? '+' : ''}{index.change_percent.toFixed(2)}%
                      </div>
                    </div>
                  </motion.div>
                )
              })}
            </div>
          )}

          {/* Last Updated */}
          <div className="text-xs text-gray-500 dark:text-gray-400 text-center pt-2 border-t">
            Last updated: {new Date(data.last_updated).toLocaleString()}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

