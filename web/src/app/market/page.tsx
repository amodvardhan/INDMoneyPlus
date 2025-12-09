'use client'

import { useAuth } from '@/hooks/useAuth'
import { useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { Input } from '@/components/ui/input'
import { MarketHealthCard } from '@/components/market/market-health-card'
import { PriceComparison } from '@/components/market/price-comparison'
import { RecommendationsList } from '@/components/market/recommendations-list'
import { apiClient } from '@/lib/api/client'
import { Search } from 'lucide-react'
import { toast } from 'sonner'
import { NotificationBell } from '@/components/notifications/notification-bell'
import type {
  MarketHealthData,
  PriceComparisonData,
  TopRecommendationsResponse,
} from '@/lib/api/types'

export default function MarketPage() {
  const router = useRouter()
  const { user, isAuthenticated, isLoading: authLoading } = useAuth()
  const [marketHealth, setMarketHealth] = useState<MarketHealthData | null>(null)
  const [recommendations, setRecommendations] = useState<TopRecommendationsResponse | null>(null)
  const [priceComparison, setPriceComparison] = useState<PriceComparisonData | null>(null)
  const [tickerSearch, setTickerSearch] = useState('')
  const [isLoadingHealth, setIsLoadingHealth] = useState(true)
  const [isLoadingRecommendations, setIsLoadingRecommendations] = useState(true)
  const [isLoadingComparison, setIsLoadingComparison] = useState(false)

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login')
    }
  }, [isAuthenticated, authLoading, router])

  useEffect(() => {
    if (isAuthenticated) {
      loadMarketData()
    }
  }, [isAuthenticated])

  const loadMarketData = async (forceRefresh = false) => {
    try {
      // Load market health
      setIsLoadingHealth(true)
      const health = await apiClient.getMarketHealth()
      setMarketHealth(health)
    } catch (error: any) {
      toast.error('Failed to load market health', {
        description: error.response?.data?.detail || 'Please try again later',
      })
    } finally {
      setIsLoadingHealth(false)
    }

    try {
      // Load recommendations
      setIsLoadingRecommendations(true)
      const recs = await apiClient.getTopRecommendations(10, undefined, forceRefresh)
      setRecommendations(recs)
      if (forceRefresh) {
        toast.success('Recommendations refreshed!', {
          description: 'New AI-generated recommendations are now available',
        })
      }
    } catch (error: any) {
      toast.error('Failed to load recommendations', {
        description: error.response?.data?.detail || 'Please try again later',
      })
    } finally {
      setIsLoadingRecommendations(false)
    }
  }

  const handleRefreshRecommendations = async () => {
    await loadMarketData(true)
  }

  const handleTickerSearch = async () => {
    if (!tickerSearch.trim()) {
      toast.error('Please enter a ticker symbol')
      return
    }

    try {
      setIsLoadingComparison(true)
      const comparison = await apiClient.getPriceComparison(tickerSearch.trim().toUpperCase())
      setPriceComparison(comparison)
    } catch (error: any) {
      toast.error('Failed to fetch price comparison', {
        description: error.response?.data?.detail || 'Ticker not found or unavailable',
      })
      setPriceComparison(null)
    } finally {
      setIsLoadingComparison(false)
    }
  }

  if (authLoading || !isAuthenticated) {
    return (
      <div className="container mx-auto px-4 py-8">
        <Skeleton className="h-64 w-full" />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-white dark:bg-gray-950">
      <div className="container mx-auto px-4 py-8 max-w-7xl">
        {/* Clean Professional Header */}
        <div className="mb-8 border-b border-gray-200 dark:border-gray-800 pb-6">
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div>
              <h1 className="text-3xl font-semibold text-gray-900 dark:text-white mb-1">
                Market Overview
              </h1>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Real-time market health, recommendations, and price comparisons
              </p>
            </div>
            <div className="flex items-center gap-2">
              <NotificationBell />
            </div>
          </div>
        </div>

        {/* Market Health */}
        <div className="mb-8">
          <MarketHealthCard data={marketHealth} isLoading={isLoadingHealth} />
        </div>

        {/* Price Comparison Search */}
        <div className="mb-8">
          <Card className="border border-gray-200 dark:border-gray-800 shadow-sm">
            <CardHeader className="border-b border-gray-200 dark:border-gray-800 bg-gray-50 dark:bg-gray-900/50">
              <CardTitle className="text-lg font-semibold flex items-center gap-2">
                <Search className="h-4 w-4 text-gray-600 dark:text-gray-400" />
                Compare Prices (NSE vs BSE)
              </CardTitle>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Compare stock prices across exchanges
              </p>
            </CardHeader>
            <CardContent className="p-6">
              <div className="flex gap-3">
                <Input
                  placeholder="Enter ticker symbol (e.g., RELIANCE, TCS)"
                  value={tickerSearch}
                  onChange={(e) => setTickerSearch(e.target.value)}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      handleTickerSearch()
                    }
                  }}
                  className="flex-1 h-10 text-sm border-gray-300 dark:border-gray-700 focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                />
                <Button
                  onClick={handleTickerSearch}
                  disabled={isLoadingComparison}
                  className="h-10 px-6 bg-blue-600 hover:bg-blue-700 text-white"
                >
                  <Search className="h-4 w-4 mr-2" />
                  Compare
                </Button>
              </div>
              {priceComparison && (
                <div className="mt-6">
                  <PriceComparison data={priceComparison} />
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Recommendations */}
        <div>
          {recommendations ? (
            <RecommendationsList
              buyRecommendations={recommendations.buy_recommendations}
              sellRecommendations={recommendations.sell_recommendations}
              lastUpdated={recommendations.last_updated}
              isLoading={isLoadingRecommendations}
              onRefresh={handleRefreshRecommendations}
            />
          ) : (
            <Card className="border border-gray-200 dark:border-gray-800 shadow-sm">
              <CardContent className="p-6">
                <Skeleton className="h-64 w-full" />
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}

