'use client'

import { useAuth } from '@/hooks/useAuth'
import { useLatestPrice, usePriceTimeseries } from '@/hooks/useLivePrice'
import { useRouter, useSearchParams } from 'next/navigation'
import { useEffect, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { Badge } from '@/components/ui/badge'
import { PriceChart } from '@/components/charts/price-chart'
import { formatCurrency, formatPercentage, formatDate } from '@/lib/utils'
import { ArrowLeft, TrendingUp, TrendingDown } from 'lucide-react'
import { motion } from 'framer-motion'
import { useAnalyzePortfolio } from '@/hooks/useAgent'
import { toast } from 'sonner'

export default function InstrumentDetailPage({
  params,
}: {
  params: { ticker: string }
}) {
  const router = useRouter()
  const searchParams = useSearchParams()
  const exchange = searchParams.get('exchange') || 'NSE'
  const { user, isAuthenticated, isLoading: authLoading } = useAuth()
  const { data: latestPrice, isLoading: priceLoading } = useLatestPrice(
    params.ticker,
    exchange
  )
  const [dateRange, setDateRange] = useState({ from: '2024-01-01', to: new Date().toISOString().split('T')[0] })
  const { data: timeseries, isLoading: timeseriesLoading } = usePriceTimeseries(
    params.ticker,
    exchange,
    dateRange.from,
    dateRange.to
  )
  const analyzeMutation = useAnalyzePortfolio()

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login')
    }
  }, [isAuthenticated, authLoading, router])

  const handleAnalyze = async () => {
    if (!user) return
    try {
      const result = await analyzeMutation.mutateAsync({
        user_id: user.id,
        portfolio_id: 1, // Mock portfolio ID
      })
      toast.success('Analysis complete', {
        description: result.explanation.substring(0, 100) + '...',
      })
    } catch (error) {
      toast.error('Analysis failed')
    }
  }

  if (authLoading || !isAuthenticated) {
    return (
      <div className="container mx-auto px-4 py-8">
        <Skeleton className="h-64 w-full" />
      </div>
    )
  }

  const priceChange = latestPrice
    ? ((latestPrice.close - latestPrice.open) / latestPrice.open) * 100
    : 0
  const priceChangeAmount = latestPrice ? latestPrice.close - latestPrice.open : 0

  return (
    <div className="container mx-auto px-4 py-8">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-6"
      >
        <Button
          variant="ghost"
          onClick={() => router.back()}
          className="mb-6 hover:bg-gray-100 dark:hover:bg-gray-800"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Portfolio
        </Button>

        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-6">
          <div>
            <h1 className="text-4xl md:text-5xl font-bold mb-2 bg-gradient-to-r from-gray-900 to-gray-700 dark:from-white dark:to-gray-300 bg-clip-text text-transparent">
              {params.ticker}
            </h1>
            <div className="flex items-center gap-3">
              <Badge className="text-sm px-3 py-1">{exchange}</Badge>
              {priceLoading ? (
                <Skeleton className="h-4 w-32" />
              ) : latestPrice ? (
                <span className="text-sm text-gray-500 dark:text-gray-400">
                  Last updated: {formatDate(latestPrice.timestamp, 'relative')}
                </span>
              ) : null}
            </div>
          </div>
          <Button 
            onClick={handleAnalyze} 
            disabled={analyzeMutation.isPending}
            className="shadow-lg hover:shadow-xl transition-all"
            size="lg"
          >
            {analyzeMutation.isPending ? 'Analyzing...' : 'AI Analyze'}
          </Button>
        </div>
      </motion.div>

      {/* Price Card */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="mb-6"
      >
        <Card className="border-2 border-primary-100 dark:border-primary-900/50 shadow-xl bg-gradient-to-br from-white to-primary-50/30 dark:from-gray-900 dark:to-primary-950/30">
          <CardContent className="pt-6">
            {priceLoading ? (
              <Skeleton className="h-32 w-full" />
            ) : latestPrice ? (
              <div>
                <div className="flex flex-col sm:flex-row items-start sm:items-baseline gap-4 mb-6">
                  <div className="text-5xl md:text-6xl font-extrabold bg-gradient-to-r from-primary-600 to-primary-800 bg-clip-text text-transparent">
                    {formatCurrency(latestPrice.price)}
                  </div>
                  <div
                    className={`flex items-center gap-2 px-4 py-2 rounded-full ${
                      priceChange >= 0 
                        ? 'bg-success-100 text-success-700 dark:bg-success-900/30 dark:text-success-400' 
                        : 'bg-error-100 text-error-700 dark:bg-error-900/30 dark:text-error-400'
                    }`}
                  >
                    {priceChange >= 0 ? (
                      <TrendingUp className="h-5 w-5" />
                    ) : (
                      <TrendingDown className="h-5 w-5" />
                    )}
                    <span className="text-lg font-semibold">
                      {formatCurrency(Math.abs(priceChangeAmount))} ({formatPercentage(priceChange)})
                    </span>
                  </div>
                </div>
                <div className="grid grid-cols-4 gap-4 text-sm">
                  <div>
                    <div className="text-gray-500">Open</div>
                    <div className="font-medium">{formatCurrency(latestPrice.open)}</div>
                  </div>
                  <div>
                    <div className="text-gray-500">High</div>
                    <div className="font-medium">{formatCurrency(latestPrice.high)}</div>
                  </div>
                  <div>
                    <div className="text-gray-500">Low</div>
                    <div className="font-medium">{formatCurrency(latestPrice.low)}</div>
                  </div>
                  <div>
                    <div className="text-gray-500">Volume</div>
                    <div className="font-medium">
                      {latestPrice.volume
                        ? latestPrice.volume.toLocaleString()
                        : 'N/A'}
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                Price data not available
              </div>
            )}
          </CardContent>
        </Card>
      </motion.div>

      {/* Chart */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
      >
        <Card className="border-2 shadow-lg">
          <CardHeader>
            <CardTitle className="text-xl">Price History</CardTitle>
          </CardHeader>
          <CardContent>
            {timeseriesLoading ? (
              <Skeleton className="h-96 w-full" />
            ) : timeseries && timeseries.data.length > 0 ? (
              <PriceChart data={timeseries.data} type="area" />
            ) : (
              <div className="text-center py-12 text-gray-500">
                No historical data available
              </div>
            )}
          </CardContent>
        </Card>
      </motion.div>
    </div>
  )
}

