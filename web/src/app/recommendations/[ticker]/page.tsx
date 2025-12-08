'use client'

import { useAuth } from '@/hooks/useAuth'
import { useRouter, useSearchParams } from 'next/navigation'
import { useEffect, useState, useMemo } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { Badge } from '@/components/ui/badge'
import { formatCurrency, formatDate } from '@/lib/utils'
import { ArrowLeft, TrendingUp, TrendingDown, Sparkles, Clock, AlertCircle, CheckCircle2, ExternalLink, BarChart3 } from 'lucide-react'
import { motion } from 'framer-motion'
import { apiClient } from '@/lib/api/client'
import { useQuery } from '@tanstack/react-query'
import { toast } from 'sonner'
import { PriceChart } from '@/components/charts/price-chart'
import { CandlestickChart } from '@/components/charts/candlestick-chart'
import { usePriceTimeseries } from '@/hooks/useLivePrice'
import type { StockFundamentals, StockNewsResponse, NewsArticle } from '@/lib/api/types'
import { Newspaper, Calendar, Globe } from 'lucide-react'

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

  const { data: recommendations, isLoading, error } = useQuery<Recommendation[]>({
    queryKey: ['recommendations', params.ticker, exchange],
    queryFn: () => apiClient.getRecommendationsForTicker(params.ticker, exchange),
    enabled: !!params.ticker,
  })

  // Calculate date range based on selected period
  const getDateRange = (period: string) => {
    const now = new Date()
    const toDate = now.toISOString().split('T')[0]
    let fromDate = new Date()

    switch (period) {
      case '1d':
        fromDate.setDate(now.getDate() - 1)
        break
      case '1w':
        fromDate.setDate(now.getDate() - 7)
        break
      case '1m':
        fromDate.setMonth(now.getMonth() - 1)
        break
      case '3m':
        fromDate.setMonth(now.getMonth() - 3)
        break
      case '6m':
        fromDate.setMonth(now.getMonth() - 6)
        break
      case '1y':
        fromDate.setFullYear(now.getFullYear() - 1)
        break
      default:
        fromDate.setMonth(now.getMonth() - 1)
    }

    return {
      from: fromDate.toISOString().split('T')[0],
      to: toDate
    }
  }

  // Memoize date range to ensure stable reference and proper date formatting
  const dateRange = useMemo(() => {
    const range = getDateRange(selectedPeriod)
    // Debug log to verify date calculation
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
        // Don't show error to user, just don't display fundamentals
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
        console.warn('⚠️ Cannot fetch news: missing ticker or exchange', { ticker: params.ticker, exchange })
        return
      }

      console.log(`📰 Starting news fetch for ${params.ticker} on ${exchange}...`)
      setNewsLoading(true)
      setNews(null) // Reset news state

      try {
        const apiUrl = `/api/v1/news/${params.ticker}?exchange=${exchange}&limit=10`
        console.log(`📡 Making API call to: ${apiUrl}`)

        const data = await apiClient.getStockNews(params.ticker, exchange, 10)

        console.log(`✅ News API response:`, {
          ticker: data.ticker,
          exchange: data.exchange,
          count: data.count,
          articlesCount: data.articles?.length || 0,
          hasError: !!data.error
        })

        if (data.error) {
          console.warn('⚠️ News API returned error:', data.error)
        }

        setNews(data)
      } catch (error: any) {
        console.error('❌ Failed to fetch news:', error)
        console.error('Error details:', {
          message: error?.message,
          response: error?.response?.data,
          status: error?.response?.status,
          statusText: error?.response?.statusText,
          url: error?.config?.url || error?.request?.responseURL,
          config: error?.config
        })

        // Set empty news object so UI shows "no news" instead of loading forever
        setNews({
          ticker: params.ticker,
          exchange,
          articles: [],
          count: 0,
          error: error?.response?.data?.detail || error?.message || 'Failed to fetch news'
        })
      } finally {
        setNewsLoading(false)
        console.log('🏁 News fetch completed')
      }
    }

    fetchNews()
  }, [params.ticker, exchange])

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login')
    }
  }, [isAuthenticated, authLoading, router])

  if (authLoading || !isAuthenticated) {
    return (
      <div className="container mx-auto px-4 py-8">
        <Skeleton className="h-64 w-full" />
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <Skeleton className="h-96 w-full" />
      </div>
    )
  }

  if (error || !recommendations || recommendations.length === 0) {
    return (
      <div className="container mx-auto px-4 py-8">
        <Button
          variant="ghost"
          onClick={() => router.back()}
          className="mb-6"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back
        </Button>
        <Card className="border-2">
          <CardContent className="pt-6">
            <div className="text-center py-12">
              <AlertCircle className="h-16 w-16 text-gray-400 mx-auto mb-4" />
              <h2 className="text-2xl font-bold mb-2">No Recommendations Found</h2>
              <p className="text-gray-600 dark:text-gray-400 mb-4">
                No active recommendations found for {params.ticker} on {exchange}
              </p>
              <Button onClick={() => router.push('/market')}>
                View All Recommendations
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  const primaryRec = recommendations[0]
  const potentialReturn = primaryRec.target_price && primaryRec.current_price
    ? ((primaryRec.target_price - primaryRec.current_price) / primaryRec.current_price * 100)
    : null

  const getRecommendationColor = (type: string) => {
    switch (type) {
      case 'strong_buy':
        return 'bg-gradient-to-r from-green-600 to-emerald-600 text-white'
      case 'buy':
        return 'bg-gradient-to-r from-green-500 to-teal-500 text-white'
      case 'hold':
        return 'bg-gradient-to-r from-yellow-500 to-amber-500 text-white'
      case 'sell':
        return 'bg-gradient-to-r from-orange-500 to-red-500 text-white'
      case 'strong_sell':
        return 'bg-gradient-to-r from-red-600 to-rose-600 text-white'
      default:
        return 'bg-gray-500 text-white'
    }
  }

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'low':
        return 'bg-green-100 text-green-700 border-green-300 dark:bg-green-900/30 dark:text-green-400'
      case 'medium':
        return 'bg-yellow-100 text-yellow-700 border-yellow-300 dark:bg-yellow-900/30 dark:text-yellow-400'
      case 'high':
        return 'bg-red-100 text-red-700 border-red-300 dark:bg-red-900/30 dark:text-red-400'
      default:
        return 'bg-gray-100 text-gray-700 border-gray-300'
    }
  }

  const getPriceSourceBadge = (source?: string) => {
    if (!source) return null
    const sourceMap: Record<string, { label: string; color: string }> = {
      'yahoo_finance': { label: 'Yahoo Finance', color: 'bg-purple-100 text-purple-700 border-purple-300 dark:bg-purple-900/30 dark:text-purple-400' },
      'tiingo': { label: 'Tiingo', color: 'bg-blue-100 text-blue-700 border-blue-300 dark:bg-blue-900/30 dark:text-blue-400' },
      'stored': { label: 'Stored', color: 'bg-gray-100 text-gray-700 border-gray-300' },
      'market_data_service': { label: 'Market Data', color: 'bg-indigo-100 text-indigo-700 border-indigo-300 dark:bg-indigo-900/30 dark:text-indigo-400' },
    }
    const sourceInfo = sourceMap[source.toLowerCase()] || { label: source, color: 'bg-gray-100 text-gray-700' }
    return (
      <Badge variant="outline" className={`text-xs ${sourceInfo.color}`}>
        {sourceInfo.label}
      </Badge>
    )
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-6xl">
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
          Back
        </Button>

        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-6">
          <div>
            <h1 className="text-4xl md:text-5xl font-bold mb-2 bg-gradient-to-r from-primary-600 to-primary-800 bg-clip-text text-transparent">
              {params.ticker}
            </h1>
            <div className="flex items-center gap-3 flex-wrap">
              <Badge className="text-sm px-3 py-1">{exchange}</Badge>
              {primaryRec.price_source && getPriceSourceBadge(primaryRec.price_source)}
              {primaryRec.price_is_stale && (
                <Badge variant="outline" className="text-xs bg-yellow-100 text-yellow-700 border-yellow-300">
                  <Clock className="h-3 w-3 mr-1" />
                  Stale Price
                </Badge>
              )}
              {!primaryRec.price_is_stale && primaryRec.price_source && (
                <Badge variant="outline" className="text-xs bg-green-100 text-green-700 border-green-300">
                  <CheckCircle2 className="h-3 w-3 mr-1" />
                  Live Price
                </Badge>
              )}
            </div>
          </div>
        </div>
      </motion.div>

      {/* Primary Recommendation Card */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="mb-6"
      >
        <Card className="border-2 shadow-xl bg-gradient-to-br from-white to-primary-50/30 dark:from-gray-900 dark:to-primary-950/30">
          <CardHeader className="bg-gradient-to-r from-primary-50 to-primary-100 dark:from-primary-900/20 dark:to-primary-800/20 border-b">
            <div className="flex items-center justify-between">
              <CardTitle className="text-2xl flex items-center gap-3">
                <Badge className={cn('text-sm px-4 py-1.5', getRecommendationColor(primaryRec.recommendation_type))}>
                  {primaryRec.recommendation_type.replace('_', ' ').toUpperCase()}
                </Badge>
                {primaryRec.source.name === 'AI Market Analyst' && (
                  <Badge variant="outline" className="border-blue-500 text-blue-700 dark:text-blue-400">
                    <Sparkles className="h-3 w-3 mr-1" />
                    AI Generated
                  </Badge>
                )}
              </CardTitle>
              {primaryRec.source.is_verified === 'true' && (
                <Badge variant="outline" className="bg-green-50 text-green-700 border-green-300">
                  <CheckCircle2 className="h-3 w-3 mr-1" />
                  Verified Source
                </Badge>
              )}
            </div>
          </CardHeader>
          <CardContent className="pt-6">
            <div className="grid md:grid-cols-2 gap-6 mb-6">
              <div>
                <div className="text-sm text-gray-500 dark:text-gray-400 mb-1">Current Price</div>
                <div className="text-4xl font-extrabold bg-gradient-to-r from-primary-600 to-primary-800 bg-clip-text text-transparent">
                  {primaryRec.current_price ? formatCurrency(primaryRec.current_price) : 'N/A'}
                </div>
                {primaryRec.price_last_updated && (
                  <div className="text-xs text-gray-500 dark:text-gray-400 mt-1 flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    Updated {formatDate(primaryRec.price_last_updated, 'relative')}
                  </div>
                )}
              </div>
              <div>
                <div className="text-sm text-gray-500 dark:text-gray-400 mb-1">Target Price</div>
                <div className="text-4xl font-extrabold bg-gradient-to-r from-primary-600 to-primary-800 bg-clip-text text-transparent">
                  {primaryRec.target_price ? formatCurrency(primaryRec.target_price) : 'N/A'}
                </div>
                {potentialReturn !== null && (
                  <div className={`text-lg font-semibold mt-2 flex items-center gap-2 ${potentialReturn > 0 ? 'text-green-600' : 'text-red-600'
                    }`}>
                    {potentialReturn > 0 ? <TrendingUp className="h-5 w-5" /> : <TrendingDown className="h-5 w-5" />}
                    {potentialReturn > 0 ? '+' : ''}{potentialReturn.toFixed(1)}% potential
                  </div>
                )}
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4 mb-6">
              <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                <div className="text-sm text-gray-500 dark:text-gray-400 mb-1">Confidence</div>
                <div className="text-2xl font-bold">{Math.round(primaryRec.confidence_score * 100)}%</div>
              </div>
              <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                <div className="text-sm text-gray-500 dark:text-gray-400 mb-1">Risk Level</div>
                <Badge className={cn('text-sm', getRiskColor(primaryRec.risk_level))}>
                  {primaryRec.risk_level.toUpperCase()}
                </Badge>
              </div>
              <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                <div className="text-sm text-gray-500 dark:text-gray-400 mb-1">Source</div>
                <div className="text-sm font-medium">{primaryRec.source.name}</div>
              </div>
            </div>

            <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
              <div className="text-sm font-semibold text-blue-900 dark:text-blue-200 mb-2">Reasoning</div>
              <p className="text-sm text-blue-800 dark:text-blue-300 leading-relaxed">
                {primaryRec.reasoning}
              </p>
            </div>

            {/* Sources Section */}
            <div className="mt-4 space-y-2">
              <div className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">Sources & References</div>
              <div className="flex flex-wrap gap-2">
                <Badge variant="outline" className="bg-white dark:bg-gray-800">
                  <Globe className="h-3 w-3 mr-1" />
                  {primaryRec.source.name}
                  {primaryRec.source.is_verified === 'true' && (
                    <CheckCircle2 className="h-3 w-3 ml-1 text-green-500" />
                  )}
                </Badge>
                {primaryRec.source_url && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => window.open(primaryRec.source_url!, '_blank')}
                    className="text-xs"
                  >
                    <ExternalLink className="h-3 w-3 mr-1" />
                    View Source Article
                  </Button>
                )}
                {primaryRec.source_date && (
                  <Badge variant="outline" className="bg-white dark:bg-gray-800">
                    <Calendar className="h-3 w-3 mr-1" />
                    {formatDate(primaryRec.source_date, 'short')}
                  </Badge>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Stock Fundamentals */}
      {fundamentals && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.25 }}
          className="mb-6"
        >
          <Card className="border-2 shadow-xl">
            <CardHeader className="bg-gradient-to-r from-indigo-50 to-purple-50 dark:from-indigo-900/20 dark:to-purple-900/20 border-b-2">
              <CardTitle className="text-xl">Stock Fundamentals</CardTitle>
            </CardHeader>
            <CardContent className="pt-6">
              <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4">
                {fundamentals.market_cap && (
                  <div className="p-4 bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
                    <div className="text-xs text-gray-600 dark:text-gray-400 mb-1 font-medium">Market Cap</div>
                    <div className="text-lg font-bold text-blue-700 dark:text-blue-400">
                      {fundamentals.market_cap.toFixed(2)} Cr
                    </div>
                  </div>
                )}
                {fundamentals.pe_ratio && (
                  <div className="p-4 bg-gradient-to-br from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20 rounded-lg border border-green-200 dark:border-green-800">
                    <div className="text-xs text-gray-600 dark:text-gray-400 mb-1 font-medium">P/E Ratio</div>
                    <div className="text-lg font-bold text-green-700 dark:text-green-400">
                      {fundamentals.pe_ratio.toFixed(2)}
                    </div>
                  </div>
                )}
                {fundamentals.dividend_yield && (
                  <div className="p-4 bg-gradient-to-br from-yellow-50 to-amber-50 dark:from-yellow-900/20 dark:to-amber-900/20 rounded-lg border border-yellow-200 dark:border-yellow-800">
                    <div className="text-xs text-gray-600 dark:text-gray-400 mb-1 font-medium">Div Yield</div>
                    <div className="text-lg font-bold text-yellow-700 dark:text-yellow-400">
                      {fundamentals.dividend_yield.toFixed(2)}%
                    </div>
                  </div>
                )}
                {fundamentals.dividend_amount && (
                  <div className="p-4 bg-gradient-to-br from-purple-50 to-violet-50 dark:from-purple-900/20 dark:to-violet-900/20 rounded-lg border border-purple-200 dark:border-purple-800">
                    <div className="text-xs text-gray-600 dark:text-gray-400 mb-1 font-medium">Qtrly Div</div>
                    <div className="text-lg font-bold text-purple-700 dark:text-purple-400">
                      ₹{fundamentals.dividend_amount.toFixed(2)}
                    </div>
                  </div>
                )}
                {fundamentals.week_52_high && (
                  <div className="p-4 bg-gradient-to-br from-green-50 to-teal-50 dark:from-green-900/20 dark:to-teal-900/20 rounded-lg border border-green-200 dark:border-green-800">
                    <div className="text-xs text-gray-600 dark:text-gray-400 mb-1 font-medium">52W High</div>
                    <div className="text-lg font-bold text-green-700 dark:text-green-400">
                      {formatCurrency(fundamentals.week_52_high)}
                    </div>
                  </div>
                )}
                {fundamentals.week_52_low && (
                  <div className="p-4 bg-gradient-to-br from-red-50 to-rose-50 dark:from-red-900/20 dark:to-rose-900/20 rounded-lg border border-red-200 dark:border-red-800">
                    <div className="text-xs text-gray-600 dark:text-gray-400 mb-1 font-medium">52W Low</div>
                    <div className="text-lg font-bold text-red-700 dark:text-red-400">
                      {formatCurrency(fundamentals.week_52_low)}
                    </div>
                  </div>
                )}
                {fundamentals.beta && (
                  <div className="p-4 bg-gradient-to-br from-gray-50 to-slate-50 dark:from-gray-800 dark:to-slate-800 rounded-lg border border-gray-200 dark:border-gray-700">
                    <div className="text-xs text-gray-600 dark:text-gray-400 mb-1 font-medium">Beta</div>
                    <div className="text-lg font-bold text-gray-700 dark:text-gray-300">
                      {fundamentals.beta.toFixed(2)}
                    </div>
                  </div>
                )}
                {fundamentals.eps && (
                  <div className="p-4 bg-gradient-to-br from-cyan-50 to-blue-50 dark:from-cyan-900/20 dark:to-blue-900/20 rounded-lg border border-cyan-200 dark:border-cyan-800">
                    <div className="text-xs text-gray-600 dark:text-gray-400 mb-1 font-medium">EPS</div>
                    <div className="text-lg font-bold text-cyan-700 dark:text-cyan-400">
                      ₹{fundamentals.eps.toFixed(2)}
                    </div>
                  </div>
                )}
                {fundamentals.book_value && (
                  <div className="p-4 bg-gradient-to-br from-orange-50 to-amber-50 dark:from-orange-900/20 dark:to-amber-900/20 rounded-lg border border-orange-200 dark:border-orange-800">
                    <div className="text-xs text-gray-600 dark:text-gray-400 mb-1 font-medium">Book Value</div>
                    <div className="text-lg font-bold text-orange-700 dark:text-orange-400">
                      ₹{fundamentals.book_value.toFixed(2)}
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* News Section - Modern Design */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="mb-6"
      >
        <Card className="border-2 border-gray-200 dark:border-gray-800 shadow-2xl bg-gradient-to-br from-white via-gray-50/50 to-white dark:from-gray-900 dark:via-gray-900/50 dark:to-gray-900 overflow-hidden">
          <CardHeader className="bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 text-white p-6">
            <div className="flex items-center justify-between">
              <CardTitle className="text-2xl font-bold flex items-center gap-3">
                <div className="p-2 bg-white/20 rounded-lg backdrop-blur-sm">
                  <Newspaper className="h-6 w-6" />
                </div>
                Latest News & Updates
              </CardTitle>
              {news && news.count > 0 && (
                <Badge variant="secondary" className="bg-white/20 text-white border-white/30 backdrop-blur-sm">
                  {news.count} articles
                </Badge>
              )}
            </div>
          </CardHeader>
          <CardContent className="p-6">
            {newsLoading ? (
              <div className="space-y-4">
                {[1, 2, 3, 4].map((i) => (
                  <div key={i} className="flex gap-4">
                    <Skeleton className="h-20 w-20 rounded-lg flex-shrink-0" />
                    <div className="flex-1 space-y-2">
                      <Skeleton className="h-5 w-full" />
                      <Skeleton className="h-4 w-3/4" />
                      <Skeleton className="h-3 w-1/2" />
                    </div>
                  </div>
                ))}
              </div>
            ) : news && Array.isArray(news.articles) && news.articles.length > 0 ? (
              <div className="space-y-3">
                {news.articles
                  .filter((article: NewsArticle) => article.title && article.title.trim() && article.url && article.url.trim())
                  .map((article: NewsArticle, index: number) => (
                    <motion.a
                      key={index}
                      href={article.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.05 * index }}
                      className="group block p-5 bg-white dark:bg-gray-800/50 border-2 border-gray-200 dark:border-gray-700 rounded-xl hover:border-indigo-400 dark:hover:border-indigo-600 hover:shadow-lg transition-all duration-300 cursor-pointer"
                    >
                      <div className="flex gap-4">
                        {/* Icon/Image Placeholder */}
                        <div className="flex-shrink-0 w-16 h-16 rounded-lg bg-gradient-to-br from-indigo-100 to-purple-100 dark:from-indigo-900/30 dark:to-purple-900/30 flex items-center justify-center group-hover:scale-110 transition-transform">
                          <Newspaper className="h-8 w-8 text-indigo-600 dark:text-indigo-400" />
                        </div>

                        {/* Content */}
                        <div className="flex-1 min-w-0">
                          <h3 className="text-lg font-bold text-gray-900 dark:text-white group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors line-clamp-2 mb-2">
                            {article.title}
                          </h3>

                          {article.snippet && article.snippet.trim() && (
                            <p className="text-sm text-gray-600 dark:text-gray-400 line-clamp-2 mb-3">
                              {article.snippet}
                            </p>
                          )}

                          {/* Metadata */}
                          <div className="flex items-center gap-4 flex-wrap">
                            <div className="flex items-center gap-1.5 text-xs text-gray-500 dark:text-gray-400">
                              <div className="p-1 bg-gray-100 dark:bg-gray-700 rounded">
                                <Globe className="h-3 w-3" />
                              </div>
                              <span className="font-medium">{article.source}</span>
                            </div>
                            <div className="flex items-center gap-1.5 text-xs text-gray-500 dark:text-gray-400">
                              <div className="p-1 bg-gray-100 dark:bg-gray-700 rounded">
                                <Calendar className="h-3 w-3" />
                              </div>
                              <span>{formatDate(article.published_at, 'relative')}</span>
                            </div>
                            <div className="ml-auto flex items-center gap-1 text-xs text-indigo-600 dark:text-indigo-400 font-semibold group-hover:gap-2 transition-all">
                              <span>Read more</span>
                              <ExternalLink className="h-3.5 w-3.5 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
                            </div>
                          </div>
                        </div>
                      </div>
                    </motion.a>
                  ))}

                {news.articles.filter((a: NewsArticle) => a.title && a.title.trim() && a.url && a.url.trim()).length === 0 && (
                  <div className="text-center py-12">
                    <div className="p-4 bg-yellow-50 dark:bg-yellow-900/20 rounded-full w-20 h-20 mx-auto mb-4 flex items-center justify-center">
                      <AlertCircle className="h-10 w-10 text-yellow-600 dark:text-yellow-400" />
                    </div>
                    <p className="text-gray-600 dark:text-gray-400 font-medium">No valid news articles found</p>
                    <p className="text-sm text-gray-500 dark:text-gray-500 mt-1">All articles are missing titles or URLs</p>
                  </div>
                )}
              </div>
            ) : news && news.error ? (
              <div className="text-center py-8">
                <div className="text-red-500 dark:text-red-400 mb-2">
                  <Newspaper className="h-12 w-12 mx-auto mb-2 opacity-50" />
                </div>
                <p className="text-red-600 dark:text-red-400 font-semibold mb-1">Failed to load news</p>
                <p className="text-sm text-gray-500 dark:text-gray-400">{news.error}</p>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    const fetchNews = async () => {
                      setNewsLoading(true)
                      try {
                        const data = await apiClient.getStockNews(params.ticker, exchange, 10)
                        setNews(data)
                      } catch (error: any) {
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
                  }}
                  className="mt-4"
                >
                  Retry
                </Button>
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                <Newspaper className="h-12 w-12 mx-auto mb-2 opacity-50" />
                <p>No news articles available at this time</p>
                {news && news.count === 0 && (
                  <p className="text-xs mt-2">No articles found for {news.ticker} on {news.exchange}</p>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      </motion.div>

      {/* Price Trend Chart */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="mb-6"
      >
        <Card className="border-2 shadow-xl">
          <CardHeader className="bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 border-b-2">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
              <CardTitle className="text-xl flex items-center gap-2">
                <BarChart3 className="h-5 w-5 text-primary-600" />
                Price Trend
              </CardTitle>
              <div className="flex items-center gap-2 flex-wrap">
                {/* Chart Type Toggle */}
                <div className="flex items-center gap-1 bg-gray-100 dark:bg-gray-800 rounded-lg p-1">
                  <Button
                    variant={chartType === 'candlestick' ? 'default' : 'ghost'}
                    size="sm"
                    onClick={() => setChartType('candlestick')}
                    className="text-xs h-7"
                  >
                    Candlestick
                  </Button>
                  <Button
                    variant={chartType === 'area' ? 'default' : 'ghost'}
                    size="sm"
                    onClick={() => setChartType('area')}
                    className="text-xs h-7"
                  >
                    Area
                  </Button>
                  <Button
                    variant={chartType === 'line' ? 'default' : 'ghost'}
                    size="sm"
                    onClick={() => setChartType('line')}
                    className="text-xs h-7"
                  >
                    Line
                  </Button>
                </div>
                {/* Period Selector */}
                <div className="flex items-center gap-1 bg-gray-100 dark:bg-gray-800 rounded-lg p-1">
                  {(['1d', '1w', '1m', '3m', '6m', '1y'] as const).map((period) => (
                    <Button
                      key={period}
                      variant={selectedPeriod === period ? 'default' : 'ghost'}
                      size="sm"
                      onClick={() => setSelectedPeriod(period)}
                      className="text-xs h-7 min-w-[40px]"
                    >
                      {period.toUpperCase()}
                    </Button>
                  ))}
                </div>
              </div>
            </div>
          </CardHeader>
          <CardContent className="pt-6">
            {timeseriesLoading ? (
              <Skeleton className="h-96 w-full" />
            ) : timeseries && timeseries.data && timeseries.data.length > 0 ? (
              <div>
                {chartType === 'candlestick' ? (
                  <div className="space-y-4">
                    <CandlestickChart
                      data={timeseries.data}
                      showVolume={true}
                      showIndicators={true}
                      periodHigh={fundamentals?.week_52_high || Math.max(...timeseries.data.map(d => d.high))}
                      periodLow={fundamentals?.week_52_low || Math.min(...timeseries.data.map(d => d.low))}
                    />
                    {/* Technical Indicators below candlestick chart */}
                    {chartType === 'candlestick' && (
                      <div className="text-xs text-gray-500 dark:text-gray-400 p-2 bg-gray-50 dark:bg-gray-800 rounded">
                        <strong>Technical Analysis:</strong> Hover over the chart to see OHLC data, volume, and technical indicators (SMA, RSI). Green indicates price increase, red indicates decrease.
                      </div>
                    )}
                  </div>
                ) : (
                  <PriceChart data={timeseries.data} type={chartType} showVolume={false} />
                )}
                {timeseries.data.length > 0 && (() => {
                  const periodStart = timeseries.data[0]?.close || 0
                  const periodEnd = timeseries.data[timeseries.data.length - 1]?.close || 0
                  const calculatedPeriodHigh = Math.max(...timeseries.data.map(d => d.high))
                  const calculatedPeriodLow = Math.min(...timeseries.data.map(d => d.low))
                  const periodChange = periodEnd - periodStart
                  const periodChangePercent = periodStart > 0 ? (periodChange / periodStart) * 100 : 0

                  // Use fundamentals 52-week high/low if available, otherwise use period high/low
                  const displayHigh = fundamentals?.week_52_high || calculatedPeriodHigh
                  const displayLow = fundamentals?.week_52_low || calculatedPeriodLow

                  return (
                    <div className="mt-6 space-y-4">
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                        <div className="p-4 bg-gradient-to-br from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20 rounded-lg border border-green-200 dark:border-green-800">
                          <div className="text-gray-600 dark:text-gray-400 mb-1 text-xs font-medium">
                            {fundamentals?.week_52_high ? '52W High' : 'Period High'}
                          </div>
                          <div className="text-xl font-bold text-green-700 dark:text-green-400">
                            {formatCurrency(displayHigh)}
                          </div>
                        </div>
                        <div className="p-4 bg-gradient-to-br from-red-50 to-rose-50 dark:from-red-900/20 dark:to-rose-900/20 rounded-lg border border-red-200 dark:border-red-800">
                          <div className="text-gray-600 dark:text-gray-400 mb-1 text-xs font-medium">
                            {fundamentals?.week_52_low ? '52W Low' : 'Period Low'}
                          </div>
                          <div className="text-xl font-bold text-red-700 dark:text-red-400">
                            {formatCurrency(displayLow)}
                          </div>
                        </div>
                        <div className="p-4 bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
                          <div className="text-gray-600 dark:text-gray-400 mb-1 text-xs font-medium">Period Start</div>
                          <div className="text-xl font-bold text-blue-700 dark:text-blue-400">
                            {formatCurrency(periodStart)}
                          </div>
                        </div>
                        <div className="p-4 bg-gradient-to-br from-purple-50 to-violet-50 dark:from-purple-900/20 dark:to-violet-900/20 rounded-lg border border-purple-200 dark:border-purple-800">
                          <div className="text-gray-600 dark:text-gray-400 mb-1 text-xs font-medium">Period End</div>
                          <div className="text-xl font-bold text-purple-700 dark:text-purple-400">
                            {formatCurrency(periodEnd)}
                          </div>
                        </div>
                      </div>
                      <div className="p-4 bg-gradient-to-r from-gray-50 to-gray-100 dark:from-gray-800 dark:to-gray-900 rounded-lg border border-gray-200 dark:border-gray-700">
                        <div className="flex items-center justify-between">
                          <div>
                            <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">Period Change ({selectedPeriod.toUpperCase()})</div>
                            <div className={`text-2xl font-bold flex items-center gap-2 ${periodChange >= 0 ? 'text-green-600' : 'text-red-600'
                              }`}>
                              {periodChange >= 0 ? <TrendingUp className="h-6 w-6" /> : <TrendingDown className="h-6 w-6" />}
                              {periodChange >= 0 ? '+' : ''}{formatCurrency(periodChange)} ({periodChangePercent >= 0 ? '+' : ''}{periodChangePercent.toFixed(2)}%)
                            </div>
                          </div>
                          <div className="text-right">
                            <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">Price Range</div>
                            <div className="text-lg font-semibold text-gray-900 dark:text-white">
                              {formatCurrency(displayHigh - displayLow)}
                            </div>
                            <div className="text-xs text-gray-500 dark:text-gray-400">
                              {((displayHigh - displayLow) / periodStart * 100).toFixed(1)}% volatility
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  )
                })()}
              </div>
            ) : (
              <div className="text-center py-12 text-gray-500">
                <BarChart3 className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p>No historical price data available for this period</p>
              </div>
            )}
          </CardContent>
        </Card>
      </motion.div>

      {/* Additional Recommendations */}
      {recommendations.length > 1 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <Card className="border-2 shadow-lg">
            <CardHeader>
              <CardTitle className="text-xl">Other Recommendations</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {recommendations.slice(1).map((rec) => (
                  <div key={rec.id} className="p-4 border rounded-lg hover:shadow-md transition-shadow">
                    <div className="flex items-center justify-between mb-2">
                      <Badge className={cn('text-xs', getRecommendationColor(rec.recommendation_type))}>
                        {rec.recommendation_type.replace('_', ' ').toUpperCase()}
                      </Badge>
                      <div className="text-sm text-gray-500">
                        Confidence: {Math.round(rec.confidence_score * 100)}%
                      </div>
                    </div>
                    <p className="text-sm text-gray-700 dark:text-gray-300">{rec.reasoning}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}
    </div>
  )
}

function cn(...classes: (string | undefined | null | false)[]): string {
  return classes.filter(Boolean).join(' ')
}
