'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { TrendingUp, TrendingDown, ExternalLink, AlertCircle, Info, Star, RefreshCw, Sparkles, Clock, CheckCircle2 } from 'lucide-react'
import { formatCurrency } from '@/lib/utils'
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
      <div
        className="p-4 border border-gray-200 dark:border-gray-800 rounded hover:bg-gray-50 dark:hover:bg-gray-900/50 transition-all cursor-pointer"
        onClick={() => {
          if (onRecommendationClick) {
            onRecommendationClick(rec)
          } else {
            router.push(`/recommendations/${rec.ticker}?exchange=${rec.exchange}`)
          }
        }}
      >
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2 flex-wrap">
              <h3 className="text-base font-semibold text-gray-900 dark:text-white">
                {rec.ticker}
              </h3>
              <Badge variant="outline" className="text-xs border-gray-300 dark:border-gray-700">
                {rec.exchange}
              </Badge>
              <Badge className={cn('text-xs font-medium px-2 py-0.5', getRecommendationColor(rec.recommendation_type))}>
                {rec.recommendation_type.replace('_', ' ').toUpperCase()}
              </Badge>
              {rec.source.is_verified === 'true' && (
                <Star className="h-4 w-4 text-yellow-500 fill-yellow-500 animate-pulse" />
              )}
            </div>
            <div className="flex items-center gap-3 text-xs text-gray-600 dark:text-gray-400 flex-wrap mb-3">
              {rec.current_price && (
                <span>Current: <span className="font-medium text-gray-900 dark:text-white">₹{rec.current_price.toFixed(2)}</span></span>
              )}
              {rec.target_price && (
                <span>
                  Target: <span className="font-medium text-gray-900 dark:text-white">₹{rec.target_price.toFixed(2)}</span>
                </span>
              )}
              {potentialReturn && (
                <span className={cn(
                  'font-medium',
                  potentialReturn > 0 ? 'text-green-600 dark:text-green-500' : 'text-red-600 dark:text-red-500'
                )}>
                  {potentialReturn > 0 ? '+' : ''}{potentialReturn.toFixed(1)}%
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
            <div className="text-xs text-gray-500 dark:text-gray-400 mb-0.5">Confidence</div>
            <div className="text-sm font-semibold text-gray-900 dark:text-white">
              {Math.round(rec.confidence_score * 100)}%
            </div>
          </div>
        </div>

        <p className="text-xs text-gray-600 dark:text-gray-400 mb-3 line-clamp-2 leading-relaxed">
          {rec.reasoning}
        </p>

        <div className="flex items-center justify-between flex-wrap gap-2">
          <div className="flex items-center gap-2 flex-wrap">
            <Badge variant="outline" className={cn('text-xs px-2 py-0.5', getRiskColor(rec.risk_level))}>
              {rec.risk_level.toUpperCase()} Risk
            </Badge>
            <span className="text-xs text-gray-500 dark:text-gray-400">
              Source: {rec.source.name}
            </span>
            {isAIGenerated(rec.source) && (
              <Badge variant="outline" className="text-xs px-1.5 py-0.5 border-blue-500 text-blue-600 dark:text-blue-400">
                <Sparkles className="h-2.5 w-2.5 mr-1" />
                AI
              </Badge>
            )}
            {rec.source.is_verified === 'true' && !isAIGenerated(rec.source) && (
              <Badge variant="outline" className="text-xs px-1.5 py-0.5 text-green-600 border-green-300 dark:text-green-500">
                <CheckCircle2 className="h-2.5 w-2.5 mr-1" />
                Verified
              </Badge>
            )}
          </div>
          {rec.source_url && (
            <Button
              variant="ghost"
              size="sm"
              onClick={(e) => {
                e.stopPropagation()
                window.open(rec.source_url!, '_blank')
              }}
              className="text-xs h-7 px-2"
            >
              <ExternalLink className="h-3 w-3 mr-1" />
              Source
            </Button>
          )}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {/* Buy Recommendations */}
      {buyRecommendations.length > 0 && (
        <Card className="border border-gray-200 dark:border-gray-800 shadow-sm">
          <CardHeader className="border-b border-gray-200 dark:border-gray-800 bg-gray-50 dark:bg-gray-900/50">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <CardTitle className="text-lg font-semibold flex items-center gap-2">
                  <TrendingUp className="h-4 w-4 text-green-600 dark:text-green-500" />
                  Buy Recommendations
                  {buyRecommendations.some(r => isAIGenerated(r.source)) && (
                    <Badge variant="outline" className="ml-2 text-xs border-blue-500 text-blue-600 dark:text-blue-400">
                      <Sparkles className="h-3 w-3 mr-1" />
                      AI
                    </Badge>
                  )}
                </CardTitle>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  Top stocks recommended for purchase
                </p>
                {lastUpdated && (
                  <div className="flex items-center gap-2 mt-2 text-xs text-gray-400 dark:text-gray-500">
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
                  className="h-8 w-8 p-0"
                >
                  <RefreshCw className={cn("h-4 w-4", (isRefreshing || isLoading) && "animate-spin")} />
                </Button>
              )}
            </div>
          </CardHeader>
          <CardContent className="p-0">
            <div className="divide-y divide-gray-200 dark:divide-gray-800">
              {buyRecommendations.map((rec, idx) => (
                <RecommendationCard key={rec.id} rec={rec} index={idx} />
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Sell Recommendations */}
      {sellRecommendations.length > 0 && (
        <Card className="border border-gray-200 dark:border-gray-800 shadow-sm">
          <CardHeader className="border-b border-gray-200 dark:border-gray-800 bg-gray-50 dark:bg-gray-900/50">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <CardTitle className="text-lg font-semibold flex items-center gap-2">
                  <TrendingDown className="h-4 w-4 text-red-600 dark:text-red-500" />
                  Sell Recommendations
                  {sellRecommendations.some(r => isAIGenerated(r.source)) && (
                    <Badge variant="outline" className="ml-2 text-xs border-blue-500 text-blue-600 dark:text-blue-400">
                      <Sparkles className="h-3 w-3 mr-1" />
                      AI
                    </Badge>
                  )}
                </CardTitle>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  Stocks you may want to consider selling
                </p>
                {lastUpdated && (
                  <div className="flex items-center gap-2 mt-2 text-xs text-gray-400 dark:text-gray-500">
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
                  className="h-8 w-8 p-0"
                >
                  <RefreshCw className={cn("h-4 w-4", (isRefreshing || isLoading) && "animate-spin")} />
                </Button>
              )}
            </div>
          </CardHeader>
          <CardContent className="p-0">
            <div className="divide-y divide-gray-200 dark:divide-gray-800">
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
      <div className="p-4 bg-gray-50 dark:bg-gray-900/50 rounded border border-gray-200 dark:border-gray-800">
        <div className="flex items-start gap-3">
          <Info className="h-4 w-4 text-gray-600 dark:text-gray-400 mt-0.5" />
          <div className="flex-1">
            <div className="text-xs text-gray-600 dark:text-gray-400 mb-1">
              <strong>AI-Powered Recommendations:</strong> Generated using advanced AI analysis of real-time market data. Updated regularly.
            </div>
            <div className="text-xs text-gray-500 dark:text-gray-500">
              <strong>Disclaimer:</strong> For informational purposes only. Always do your own research and consult with a financial advisor.
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

