'use client'

import { useAuth } from '@/hooks/useAuth'
import { useRouter, useSearchParams } from 'next/navigation'
import { useEffect, useState, useMemo } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { Badge } from '@/components/ui/badge'
import { formatCurrency, formatDate } from '@/lib/utils'
import { ArrowLeft, TrendingUp, TrendingDown, Sparkles, Clock, AlertCircle, CheckCircle2, ExternalLink, BarChart3, Info, Building2 } from 'lucide-react'
import { motion } from 'framer-motion'
import { apiClient } from '@/lib/api/client'
import { useQuery } from '@tanstack/react-query'
import { toast } from 'sonner'
import { PriceChart } from '@/components/charts/price-chart'
import { CandlestickChart } from '@/components/charts/candlestick-chart'
import { usePriceTimeseries } from '@/hooks/useLivePrice'
import type { StockFundamentals, StockNewsResponse, NewsArticle } from '@/lib/api/types'
import { Newspaper, Calendar, Globe } from 'lucide-react'
import { cn } from '@/lib/utils'

interface Recommendation {
  id: number
  ticker: string
  exchange: string
  recommendation_type: 'buy' | 'sell' | 'hold' | 'strong_buy' | 'strong_sell'
  target_price: number | null
  current_price: number | null
  reasoning: string
  risk_level: 'low' | 'medium' | 'high'
  confidence_score: number
  source: {
    id: number
    name: string
    source_type: string
    credibility_score: number
    is_verified: string
  }
  source_url: string | null
  source_date: string
  is_active: string
  expires_at: string | null
  created_at: string
  price_is_stale?: boolean
  price_age_hours?: number
  price_last_updated?: string
  price_source?: string
}

export default function RecommendationDetailPage({
  params,
}: {
  params: { ticker: string }
}) {
  const router = useRouter()
  const searchParams = useSearchParams()
  const exchange = searchParams.get('exchange') || 'NSE'
  const { user, isAuthenticated, isLoading: authLoading } = useAuth()

  const [selectedPeriod, setSelectedPeriod] = useState<'1d' | '1w' | '1m' | '3m' | '6m' | '1y'>('1m')
  const [chartType, setChartType] = useState<'line' | 'area' | 'candlestick'>('candlestick')
  const [fundamentals, setFundamentals] = useState<StockFundamentals | null>(null)
  const [fundamentalsLoading, setFundamentalsLoading] = useState(false)
  const [news, setNews] = useState<any>(null)
  const [newsLoading, setNewsLoading] = useState(false)
  const [currentPrice, setCurrentPrice] = useState<number | null>(null)
  const [priceLoading, setPriceLoading] = useState(false)

  const { data: recommendations, isLoading, error } = useQuery({
    queryKey: ['recommendation', params.ticker, exchange],
    queryFn: () => apiClient.getRecommendationsForTicker(params.ticker, exchange),
    enabled: !!params.ticker && !!exchange,
    staleTime: 30000,
    refetchInterval: 60000,
  })

  const getDateRange = (period: '1d' | '1w' | '1m' | '3m' | '6m' | '1y') => {
    const today = new Date()
    const to = today.toISOString().split('T')[0]

    let fromDate = new Date()
    switch (period) {
      case '1d':
        fromDate.setDate(today.getDate() - 1)
        break
      case '1w':
        fromDate.setDate(today.getDate() - 7)
        break
      case '1m':
        fromDate.setMonth(today.getMonth() - 1)
        break
      case '3m':
        fromDate.setMonth(today.getMonth() - 3)
        break
      case '6m':
        fromDate.setMonth(today.getMonth() - 6)
        break
      case '1y':
        fromDate.setFullYear(today.getFullYear() - 1)
        break
    }
    const from = fromDate.toISOString().split('T')[0]
    return { from, to }
  }

  // Memoize date range to ensure stable reference and proper date formatting
  const dateRange = useMemo(() => {
    const range = getDateRange(selectedPeriod)
    console.log('📅 Period changed:', selectedPeriod, '→ Date range:', range)
    return range
  }, [selectedPeriod])

  const { data: timeseries, isLoading: timeseriesLoading } = usePriceTimeseries(
    params.ticker,
    exchange,
    dateRange.from,
    dateRange.to
  )

  // Fetch fundamentals
  useEffect(() => {
    const fetchFundamentals = async () => {
      setFundamentalsLoading(true)
      try {
        const data = await apiClient.getStockFundamentals(params.ticker, exchange)
        setFundamentals(data)
      } catch (error) {
        console.error('Failed to fetch fundamentals:', error)
      } finally {
        setFundamentalsLoading(false)
      }
    }

    if (params.ticker && exchange) {
      fetchFundamentals()
    }
  }, [params.ticker, exchange])

  // Fetch news
  useEffect(() => {
    const fetchNews = async () => {
      if (!params.ticker || !exchange) {
        return
      }

      setNewsLoading(true)
      setNews(null)

      try {
        const data = await apiClient.getStockNews(params.ticker, exchange, 10)
        setNews(data)
      } catch (error: any) {
        console.error('❌ Failed to fetch news:', error)
        setNews({
          ticker: params.ticker,
          exchange,
          articles: [],
          count: 0,
          error: error?.response?.data?.detail || error?.message || 'Failed to fetch news'
        })
      } finally {
        setNewsLoading(false)
      }
    }

    fetchNews()
  }, [params.ticker, exchange])

  // Fetch current price
  useEffect(() => {
    const fetchPrice = async () => {
      if (!params.ticker || !exchange) return
      setPriceLoading(true)
      try {
        const priceData = await apiClient.getLatestPrice(params.ticker, exchange)
        setCurrentPrice(priceData.close)
      } catch (error) {
        console.error('Failed to fetch price:', error)
      } finally {
        setPriceLoading(false)
      }
    }
    fetchPrice()
  }, [params.ticker, exchange])

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login')
    }
  }, [isAuthenticated, authLoading, router])

  if (authLoading || !isAuthenticated) {
    return (
      <div className="container mx-auto px-4 py-6 max-w-7xl">
        <Skeleton className="h-64 w-full" />
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="container mx-auto px-4 py-6 max-w-7xl">
        <Skeleton className="h-96 w-full" />
      </div>
    )
  }

  // If no recommendations, show stock details page anyway
  const hasRecommendations = recommendations && recommendations.length > 0
  const primaryRec = hasRecommendations ? recommendations[0] : null
  const potentialReturn = primaryRec && primaryRec.target_price && primaryRec.current_price
    ? ((primaryRec.target_price - primaryRec.current_price) / primaryRec.current_price * 100)
    : null

  const getRecommendationColor = (type: string) => {
    switch (type) {
      case 'strong_buy':
        return 'bg-green-600 text-white'
      case 'buy':
        return 'bg-green-500 text-white'
      case 'hold':
        return 'bg-yellow-500 text-white'
      case 'sell':
        return 'bg-orange-500 text-white'
      case 'strong_sell':
        return 'bg-red-600 text-white'
      default:
        return 'bg-gray-500 text-white'
    }
  }

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'low':
        return 'bg-green-50 text-green-700 border-green-200 dark:bg-green-900/20 dark:text-green-400'
      case 'medium':
        return 'bg-yellow-50 text-yellow-700 border-yellow-200 dark:bg-yellow-900/20 dark:text-yellow-400'
      case 'high':
        return 'bg-red-50 text-red-700 border-red-200 dark:bg-red-900/20 dark:text-red-400'
      default:
        return 'bg-gray-50 text-gray-700 border-gray-200'
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      <div className="container mx-auto px-4 py-4 max-w-7xl">
        {/* Compact Header */}
        <div className="mb-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => router.back()}
            className="mb-3 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100"
          >
            <ArrowLeft className="h-4 w-4 mr-1" />
            Back
          </Button>

          <div className="flex items-center justify-between flex-wrap gap-3">
            <div className="flex items-center gap-3">
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
                {params.ticker}
              </h1>
              <Badge variant="outline" className="text-xs">{exchange}</Badge>
              {primaryRec && (
                <Badge className={cn('text-xs px-2 py-0.5', getRecommendationColor(primaryRec.recommendation_type))}>
                  {primaryRec.recommendation_type.replace('_', ' ').toUpperCase()}
                </Badge>
              )}
            </div>

            <div className="flex items-center gap-4 text-sm">
              <div className="text-right">
                <div className="text-xs text-gray-500 dark:text-gray-400">Current Price</div>
                <div className="text-xl font-bold text-gray-900 dark:text-white">
                  {priceLoading ? (
                    <Skeleton className="h-6 w-24 inline-block" />
                  ) : currentPrice ? (
                    formatCurrency(currentPrice)
                  ) : primaryRec && primaryRec.current_price ? (
                    formatCurrency(primaryRec.current_price)
                  ) : (
                    'N/A'
                  )}
                </div>
              </div>
              {potentialReturn !== null && (
                <div className={cn('text-right', potentialReturn > 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400')}>
                  <div className="text-xs">Potential</div>
                  <div className="text-xl font-bold flex items-center gap-1">
                    {potentialReturn > 0 ? <TrendingUp className="h-4 w-4" /> : <TrendingDown className="h-4 w-4" />}
                    {potentialReturn > 0 ? '+' : ''}{potentialReturn.toFixed(1)}%
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Main Content Grid - Chart First, News Sidebar */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          {/* Left Column - Chart & Key Info (2/3 width) */}
          <div className="lg:col-span-2 space-y-4">
            {/* Price Chart - Main Focus */}
            <Card className="border shadow-sm">
              <CardHeader className="pb-3 border-b">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-lg font-semibold">Price Chart</CardTitle>
                  <div className="flex items-center gap-2">
                    {/* Period Selector */}
                    <div className="flex items-center gap-1 bg-gray-100 dark:bg-gray-800 rounded-md p-0.5">
                      {(['1d', '1w', '1m', '3m', '6m', '1y'] as const).map((period) => (
                        <Button
                          key={period}
                          variant={selectedPeriod === period ? 'default' : 'ghost'}
                          size="sm"
                          onClick={() => setSelectedPeriod(period)}
                          className={cn(
                            'text-xs h-7 px-2',
                            selectedPeriod === period && 'bg-white dark:bg-gray-700 shadow-sm'
                          )}
                        >
                          {period.toUpperCase()}
                        </Button>
                      ))}
                    </div>
                    {/* Chart Type */}
                    <div className="flex items-center gap-1 bg-gray-100 dark:bg-gray-800 rounded-md p-0.5">
                      <Button
                        variant={chartType === 'candlestick' ? 'default' : 'ghost'}
                        size="sm"
                        onClick={() => setChartType('candlestick')}
                        className="text-xs h-7 px-2"
                      >
                        Candle
                      </Button>
                      <Button
                        variant={chartType === 'area' ? 'default' : 'ghost'}
                        size="sm"
                        onClick={() => setChartType('area')}
                        className="text-xs h-7 px-2"
                      >
                        Area
                      </Button>
                    </div>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="pt-4">
                {timeseriesLoading ? (
                  <Skeleton className="h-96 w-full" />
                ) : timeseries && timeseries.data && timeseries.data.length > 0 ? (
                  <div>
                    {chartType === 'candlestick' ? (
                      <CandlestickChart
                        data={timeseries.data}
                        periodHigh={fundamentals?.week_52_high || Math.max(...timeseries.data.map(d => d.high))}
                        periodLow={fundamentals?.week_52_low || Math.min(...timeseries.data.map(d => d.low))}
                      />
                    ) : (
                      <PriceChart data={timeseries.data} type={chartType} showVolume={false} />
                    )}
                  </div>
                ) : (
                  <div className="h-96 flex items-center justify-center text-gray-500">
                    No price data available
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Key Metrics Grid - Compact (only show if recommendation exists) */}
            {primaryRec && (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <Card className="border shadow-sm">
                  <CardContent className="p-4">
                    <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">Target Price</div>
                    <div className="text-lg font-bold text-gray-900 dark:text-white">
                      {primaryRec.target_price ? formatCurrency(primaryRec.target_price) : 'N/A'}
                    </div>
                  </CardContent>
                </Card>
                <Card className="border shadow-sm">
                  <CardContent className="p-4">
                    <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">Confidence</div>
                    <div className="text-lg font-bold text-gray-900 dark:text-white">
                      {Math.round(primaryRec.confidence_score * 100)}%
                    </div>
                  </CardContent>
                </Card>
                <Card className="border shadow-sm">
                  <CardContent className="p-4">
                    <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">Risk Level</div>
                    <Badge className={cn('text-xs', getRiskColor(primaryRec.risk_level))}>
                      {primaryRec.risk_level.toUpperCase()}
                    </Badge>
                  </CardContent>
                </Card>
                <Card className="border shadow-sm">
                  <CardContent className="p-4">
                    <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">Source</div>
                    <div className="text-sm font-medium text-gray-900 dark:text-white truncate">
                      {primaryRec.source.name}
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}

            {/* Fundamentals - Compact Grid */}
            {fundamentals && (
              <Card className="border shadow-sm">
                <CardHeader className="pb-3 border-b">
                  <CardTitle className="text-lg font-semibold flex items-center gap-2">
                    <Building2 className="h-4 w-4" />
                    Fundamentals
                  </CardTitle>
                </CardHeader>
                <CardContent className="pt-4">
                  <div className="grid grid-cols-3 md:grid-cols-5 gap-3">
                    {fundamentals.market_cap && (
                      <div>
                        <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">Market Cap</div>
                        <div className="text-sm font-semibold text-gray-900 dark:text-white">
                          {fundamentals.market_cap.toFixed(1)} Cr
                        </div>
                      </div>
                    )}
                    {fundamentals.pe_ratio && (
                      <div>
                        <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">P/E Ratio</div>
                        <div className="text-sm font-semibold text-gray-900 dark:text-white">
                          {fundamentals.pe_ratio.toFixed(2)}
                        </div>
                      </div>
                    )}
                    {fundamentals.dividend_yield && (
                      <div>
                        <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">Div Yield</div>
                        <div className="text-sm font-semibold text-gray-900 dark:text-white">
                          {fundamentals.dividend_yield.toFixed(2)}%
                        </div>
                      </div>
                    )}
                    {fundamentals.week_52_high && (
                      <div>
                        <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">52W High</div>
                        <div className="text-sm font-semibold text-green-600 dark:text-green-400">
                          {formatCurrency(fundamentals.week_52_high)}
                        </div>
                      </div>
                    )}
                    {fundamentals.week_52_low && (
                      <div>
                        <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">52W Low</div>
                        <div className="text-sm font-semibold text-red-600 dark:text-red-400">
                          {formatCurrency(fundamentals.week_52_low)}
                        </div>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Reasoning - Only show if recommendation exists */}
            {primaryRec && (
              <Card className="border shadow-sm">
                <CardHeader className="pb-3 border-b">
                  <CardTitle className="text-lg font-semibold flex items-center gap-2">
                    <Info className="h-4 w-4" />
                    Analysis & Reasoning
                  </CardTitle>
                </CardHeader>
                <CardContent className="pt-4">
                  <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
                    {primaryRec.reasoning}
                  </p>
                  {primaryRec.source_url && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => window.open(primaryRec.source_url!, '_blank')}
                      className="mt-3"
                    >
                      <ExternalLink className="h-3 w-3 mr-1" />
                      View Source
                    </Button>
                  )}
                </CardContent>
              </Card>
            )}

            {/* No Recommendation Message */}
            {!hasRecommendations && !isLoading && (
              <Card className="border shadow-sm bg-yellow-50 dark:bg-yellow-900/10 border-yellow-200 dark:border-yellow-800">
                <CardContent className="p-4">
                  <div className="flex items-start gap-3">
                    <AlertCircle className="h-5 w-5 text-yellow-600 dark:text-yellow-400 mt-0.5" />
                    <div>
                      <p className="text-sm font-medium text-yellow-900 dark:text-yellow-200">
                        No active recommendations available
                      </p>
                      <p className="text-xs text-yellow-700 dark:text-yellow-300 mt-1">
                        This stock doesn't have any active recommendations yet. View the chart, fundamentals, and news below.
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>

          {/* Right Column - News Sidebar (1/3 width) */}
          <div className="lg:col-span-1">
            <Card className="border shadow-sm sticky top-4">
              <CardHeader className="pb-3 border-b">
                <CardTitle className="text-lg font-semibold flex items-center justify-between">
                  <span className="flex items-center gap-2">
                    <Newspaper className="h-4 w-4" />
                    Latest News
                  </span>
                  {news && news.count > 0 && (
                    <Badge variant="secondary" className="text-xs">
                      {news.count}
                    </Badge>
                  )}
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-3 p-0">
                <div className="max-h-[calc(100vh-200px)] overflow-y-auto">
                  {newsLoading ? (
                    <div className="space-y-3 p-3">
                      {[1, 2, 3].map((i) => (
                        <Skeleton key={i} className="h-20 w-full" />
                      ))}
                    </div>
                  ) : news && Array.isArray(news.articles) && news.articles.length > 0 ? (
                    <div className="space-y-0 divide-y divide-gray-200 dark:divide-gray-800">
                      {news.articles
                        .filter((article: NewsArticle) => article.title && article.title.trim() && article.url && article.url.trim())
                        .slice(0, 8)
                        .map((article: NewsArticle, index: number) => (
                          <a
                            key={index}
                            href={article.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="block p-3 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors group"
                          >
                            <h4 className="text-sm font-semibold text-gray-900 dark:text-white line-clamp-2 mb-1.5 group-hover:text-primary-600 dark:group-hover:text-primary-400 transition-colors">
                              {article.title}
                            </h4>
                            <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
                              <span className="truncate">{article.source}</span>
                              <span>•</span>
                              <span>{formatDate(article.published_at, 'relative')}</span>
                            </div>
                          </a>
                        ))}
                    </div>
                  ) : (
                    <div className="p-6 text-center text-sm text-gray-500 dark:text-gray-400">
                      <Newspaper className="h-8 w-8 mx-auto mb-2 opacity-50" />
                      <p>No news available</p>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  )
}
