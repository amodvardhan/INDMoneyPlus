'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { TrendingUp, TrendingDown, ExternalLink, AlertCircle, Info, Star, RefreshCw, Sparkles, Clock, CheckCircle2 } from 'lucide-react'
import { formatCurrency } from '@/lib/utils'
import { motion } from 'framer-motion'
import { cn } from '@/lib/utils'
import { useRouter } from 'next/navigation'
import { useState } from 'react'

export interface Recommendation {
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

interface RecommendationsListProps {
  buyRecommendations: Recommendation[]
  sellRecommendations: Recommendation[]
  lastUpdated?: string
  isLoading?: boolean
  onRefresh?: () => void
  onRecommendationClick?: (recommendation: Recommendation) => void
}

export function RecommendationsList({
  buyRecommendations,
  sellRecommendations,
  lastUpdated,
  isLoading = false,
  onRefresh,
  onRecommendationClick,
}: RecommendationsListProps) {
  const [isRefreshing, setIsRefreshing] = useState(false)

  const handleRefresh = async () => {
    if (onRefresh && !isRefreshing) {
      setIsRefreshing(true)
      try {
        await onRefresh()
      } finally {
        setIsRefreshing(false)
      }
    }
  }

  const formatLastUpdated = (dateString?: string) => {
    if (!dateString) return 'Just now'
    try {
      const date = new Date(dateString)
      const now = new Date()
      const diffMs = now.getTime() - date.getTime()
      const diffMins = Math.floor(diffMs / 60000)
      const diffHours = Math.floor(diffMs / 3600000)

      if (diffMins < 1) return 'Just now'
      if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`
      if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`
      return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    } catch {
      return 'Unknown'
    }
  }

  const isAIGenerated = (source: Recommendation['source']) => {
    return source.name === 'AI Market Analyst' || source.source_type === 'ai_analysis'
  }
  const router = useRouter()

  if (isLoading) {
    return (
      <Card className="border-2 shadow-lg">
        <CardHeader>
          <CardTitle className="text-xl">Top Recommendations</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="animate-pulse space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-24 bg-gray-200 rounded"></div>
            ))}
          </div>
        </CardContent>
      </Card>
    )
  }

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
        return 'bg-green-100 text-green-700 border-green-200'
      case 'medium':
        return 'bg-yellow-100 text-yellow-700 border-yellow-200'
      case 'high':
        return 'bg-red-100 text-red-700 border-red-200'
      default:
        return 'bg-gray-100 text-gray-700 border-gray-200'
    }
  }

  const RecommendationCard = ({ rec, index }: { rec: Recommendation; index: number }) => {
    const potentialReturn = rec.target_price && rec.current_price
      ? ((rec.target_price - rec.current_price) / rec.current_price * 100)
      : null

    return (
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: index * 0.1 }}
        whileHover={{ scale: 1.02, y: -2 }}
        className="p-5 border-2 rounded-xl hover:shadow-xl transition-all cursor-pointer bg-white dark:bg-gray-900 hover:border-primary-300 dark:hover:border-primary-700"
        onClick={() => {
          if (onRecommendationClick) {
            onRecommendationClick(rec)
          } else {
            router.push(`/recommendations/${rec.ticker}?exchange=${rec.exchange}`)
          }
        }}
      >
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-3 flex-wrap">
              <h3 className="text-xl font-bold bg-gradient-to-r from-gray-900 to-gray-700 dark:from-white dark:to-gray-300 bg-clip-text text-transparent">
                {rec.ticker}
              </h3>
              <Badge variant="outline" className="text-xs font-medium border-gray-300 dark:border-gray-600">
                {rec.exchange}
              </Badge>
              <Badge className={cn('text-xs font-semibold px-3 py-1 shadow-sm', getRecommendationColor(rec.recommendation_type))}>
                {rec.recommendation_type.replace('_', ' ').toUpperCase()}
              </Badge>
              {rec.source.is_verified === 'true' && (
                <Star className="h-4 w-4 text-yellow-500 fill-yellow-500 animate-pulse" />
              )}
            </div>
            <div className="flex items-center gap-4 text-sm text-gray-600 dark:text-gray-400 flex-wrap">
              {rec.current_price && (
                <span className="font-medium">Current: ₹{rec.current_price.toFixed(2)}</span>
              )}
              {rec.target_price && (
                <span className="font-medium">
                  Target: ₹{rec.target_price.toFixed(2)}
                </span>
              )}
              {potentialReturn && (
                <span className={cn(
                  'font-semibold',
                  potentialReturn > 0 ? 'text-green-600' : 'text-red-600'
                )}>
                  {potentialReturn > 0 ? '+' : ''}{potentialReturn.toFixed(1)}% potential
                </span>
              )}
              {rec.price_source && (
                <Badge variant="outline" className={cn(
                  'text-xs',
                  rec.price_source === 'yahoo_finance' && 'bg-purple-100 text-purple-700 border-purple-300 dark:bg-purple-900/30 dark:text-purple-400',
                  rec.price_source === 'tiingo' && 'bg-blue-100 text-blue-700 border-blue-300 dark:bg-blue-900/30 dark:text-blue-400',
                  rec.price_source === 'stored' && 'bg-gray-100 text-gray-700 border-gray-300',
                  !['yahoo_finance', 'tiingo', 'stored'].includes(rec.price_source) && 'bg-indigo-100 text-indigo-700 border-indigo-300'
                )}>
                  {rec.price_source === 'yahoo_finance' ? 'Yahoo Finance' :
                    rec.price_source === 'tiingo' ? 'Tiingo' :
                      rec.price_source === 'stored' ? 'Stored' : rec.price_source}
                </Badge>
              )}
              {rec.price_is_stale && (
                <Badge variant="outline" className="text-xs bg-yellow-100 text-yellow-700 border-yellow-300">
                  <Clock className="h-3 w-3 mr-1" />
                  Stale
                </Badge>
              )}
              {!rec.price_is_stale && rec.price_source && (
                <Badge variant="outline" className="text-xs bg-green-100 text-green-700 border-green-300">
                  <CheckCircle2 className="h-3 w-3 mr-1" />
                  Live
                </Badge>
              )}
            </div>
          </div>
          <div className="text-right">
            <div className="text-sm text-gray-500 dark:text-gray-400 mb-1">Confidence</div>
            <div className="text-lg font-bold text-gray-900 dark:text-white">
              {Math.round(rec.confidence_score * 100)}%
            </div>
          </div>
        </div>

        <p className="text-sm text-gray-700 dark:text-gray-300 mb-4 line-clamp-2 leading-relaxed">
          {rec.reasoning}
        </p>

        <div className="flex items-center justify-between flex-wrap gap-3">
          <div className="flex items-center gap-2 flex-wrap">
            <Badge variant="outline" className={cn('text-xs font-medium px-2.5 py-1', getRiskColor(rec.risk_level))}>
              {rec.risk_level.toUpperCase()} Risk
            </Badge>
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-xs text-gray-600 dark:text-gray-400 font-medium">
                Source: {rec.source.name}
              </span>
              {isAIGenerated(rec.source) && (
                <Badge variant="outline" className="text-xs px-2 py-0.5 border-blue-500 text-blue-700 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/30">
                  <Sparkles className="h-2.5 w-2.5 mr-1" />
                  AI
                </Badge>
              )}
              {rec.source.is_verified === 'true' && !isAIGenerated(rec.source) && (
                <Badge variant="outline" className="text-xs px-2 py-0.5 bg-green-50 text-green-700 border-green-300 dark:bg-green-900/30 dark:text-green-400">
                  <CheckCircle2 className="h-2.5 w-2.5 mr-1" />
                  Verified
                </Badge>
              )}
            </div>
          </div>
          {rec.source_url && (
            <Button
              variant="ghost"
              size="sm"
              onClick={(e) => {
                e.stopPropagation()
                window.open(rec.source_url!, '_blank')
              }}
              className="text-xs hover:bg-gray-100 dark:hover:bg-gray-800"
            >
              <ExternalLink className="h-3 w-3 mr-1" />
              Source
            </Button>
          )}
        </div>
      </motion.div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Buy Recommendations */}
      {buyRecommendations.length > 0 && (
        <Card className="border-2 shadow-xl bg-gradient-to-br from-white to-green-50/30 dark:from-gray-900 dark:to-green-950/30">
          <CardHeader className="bg-gradient-to-r from-green-50 via-emerald-50 to-teal-50 dark:from-green-900/30 dark:via-emerald-900/20 dark:to-teal-900/20 border-b-2 border-green-200 dark:border-green-800">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <CardTitle className="text-xl flex items-center gap-2">
                  <TrendingUp className="h-5 w-5 text-green-600" />
                  Buy Recommendations
                  {buyRecommendations.some(r => isAIGenerated(r.source)) && (
                    <Badge variant="outline" className="ml-2 border-blue-500 text-blue-700 dark:text-blue-400">
                      <Sparkles className="h-3 w-3 mr-1" />
                      AI Generated
                    </Badge>
                  )}
                </CardTitle>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                  Top stocks recommended for purchase based on AI-powered market analysis
                </p>
                {lastUpdated && (
                  <div className="flex items-center gap-2 mt-2 text-xs text-gray-500 dark:text-gray-400">
                    <Clock className="h-3 w-3" />
                    <span>Updated {formatLastUpdated(lastUpdated)}</span>
                  </div>
                )}
              </div>
              {onRefresh && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleRefresh}
                  disabled={isRefreshing || isLoading}
                  className="ml-4"
                >
                  <RefreshCw className={cn("h-4 w-4", (isRefreshing || isLoading) && "animate-spin")} />
                </Button>
              )}
            </div>
          </CardHeader>
          <CardContent className="pt-6">
            <div className="space-y-4">
              {buyRecommendations.map((rec, idx) => (
                <RecommendationCard key={rec.id} rec={rec} index={idx} />
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Sell Recommendations */}
      {sellRecommendations.length > 0 && (
        <Card className="border-2 shadow-xl bg-gradient-to-br from-white to-red-50/30 dark:from-gray-900 dark:to-red-950/30">
          <CardHeader className="bg-gradient-to-r from-red-50 via-orange-50 to-amber-50 dark:from-red-900/30 dark:via-orange-900/20 dark:to-amber-900/20 border-b-2 border-red-200 dark:border-red-800">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <CardTitle className="text-xl flex items-center gap-2">
                  <TrendingDown className="h-5 w-5 text-red-600" />
                  Sell Recommendations
                  {sellRecommendations.some(r => isAIGenerated(r.source)) && (
                    <Badge variant="outline" className="ml-2 border-blue-500 text-blue-700 dark:text-blue-400">
                      <Sparkles className="h-3 w-3 mr-1" />
                      AI Generated
                    </Badge>
                  )}
                </CardTitle>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                  Stocks you may want to consider selling based on AI-powered market analysis
                </p>
                {lastUpdated && (
                  <div className="flex items-center gap-2 mt-2 text-xs text-gray-500 dark:text-gray-400">
                    <Clock className="h-3 w-3" />
                    <span>Updated {formatLastUpdated(lastUpdated)}</span>
                  </div>
                )}
              </div>
              {onRefresh && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleRefresh}
                  disabled={isRefreshing || isLoading}
                  className="ml-4"
                >
                  <RefreshCw className={cn("h-4 w-4", (isRefreshing || isLoading) && "animate-spin")} />
                </Button>
              )}
            </div>
          </CardHeader>
          <CardContent className="pt-6">
            <div className="space-y-4">
              {sellRecommendations.map((rec, idx) => (
                <RecommendationCard key={rec.id} rec={rec} index={idx} />
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Empty State */}
      {buyRecommendations.length === 0 && sellRecommendations.length === 0 && (
        <Card className="border-2 shadow-lg">
          <CardContent className="pt-6">
            <div className="text-center py-8">
              <Info className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600 dark:text-gray-400">
                No recommendations available at the moment.
              </p>
              <p className="text-sm text-gray-500 dark:text-gray-500 mt-2">
                Check back later for updated recommendations based on market research.
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Educational Note */}
      <div className="p-4 bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
        <div className="flex items-start gap-3">
          <div className="p-1.5 bg-blue-100 dark:bg-blue-900/50 rounded-lg">
            <Sparkles className="h-4 w-4 text-blue-600" />
          </div>
          <div className="flex-1">
            <div className="text-sm text-blue-800 dark:text-blue-200 mb-2">
              <strong>AI-Powered Recommendations:</strong> These recommendations are generated dynamically using
              advanced AI analysis of real-time market data, trends, and market conditions. They are updated
              regularly to reflect the latest market insights.
            </div>
            <div className="text-xs text-blue-700 dark:text-blue-300">
              <strong>Disclaimer:</strong> Recommendations are for informational purposes only. Always do your own research
              and consult with a financial advisor before making investment decisions. Past performance
              does not guarantee future results.
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

