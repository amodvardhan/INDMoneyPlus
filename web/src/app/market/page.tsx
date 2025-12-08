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
import { motion } from 'framer-motion'
import { Search, TrendingUp, BookOpen, Info, Sparkles } from 'lucide-react'
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
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-gradient-to-br from-primary-500 to-primary-600 rounded-xl shadow-lg">
              <TrendingUp className="h-8 w-8 text-white" />
            </div>
            <div>
              <h1 className="text-4xl font-bold bg-gradient-to-r from-gray-900 to-gray-700 dark:from-white dark:to-gray-300 bg-clip-text text-transparent">
                Market Overview
              </h1>
              <p className="text-lg text-gray-600 dark:text-gray-400 mt-1">
                Real-time market health, stock recommendations, and price comparisons
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <NotificationBell />
          </div>
        </div>
      </motion.div>

      {/* Educational Banner for Beginners */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="mb-6"
      >
        <Card className="border-2 border-blue-200 bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20">
          <CardContent className="pt-6">
            <div className="flex items-start gap-4">
              <div className="p-2 bg-blue-100 dark:bg-blue-900/50 rounded-lg">
                <Sparkles className="h-6 w-6 text-blue-600" />
              </div>
              <div className="flex-1">
                <h3 className="font-semibold text-lg mb-2 text-gray-900 dark:text-white">
                  New to Stock Market?
                </h3>
                <p className="text-sm text-gray-700 dark:text-gray-300 mb-3">
                  This page shows you the overall market condition, top stock recommendations from
                  expert sources, and price comparisons across exchanges. Use this information to
                  make informed investment decisions.
                </p>
                <div className="flex items-center gap-4">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => router.push('/handbook')}
                    className="text-xs"
                  >
                    <BookOpen className="h-3 w-3 mr-2" />
                    Learn More
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      // Open chat assistant
                      const event = new CustomEvent('open-chat')
                      window.dispatchEvent(event)
                    }}
                    className="text-xs"
                  >
                    <Info className="h-3 w-3 mr-2" />
                    Ask Questions
                  </Button>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Market Health */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="mb-6"
      >
        <MarketHealthCard data={marketHealth} isLoading={isLoadingHealth} />
      </motion.div>

      {/* Price Comparison Search */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="mb-6"
      >
        <Card className="border-2 shadow-lg">
          <CardHeader>
            <CardTitle className="text-xl">Compare Prices (NSE vs BSE)</CardTitle>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
              Many stocks trade on both NSE and BSE. Compare prices to find the best deal.
            </p>
          </CardHeader>
          <CardContent>
            <div className="flex gap-2">
              <Input
                placeholder="Enter ticker symbol (e.g., RELIANCE, TCS)"
                value={tickerSearch}
                onChange={(e) => setTickerSearch(e.target.value)}
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    handleTickerSearch()
                  }
                }}
                className="flex-1"
              />
              <Button onClick={handleTickerSearch} disabled={isLoadingComparison}>
                <Search className="h-4 w-4 mr-2" />
                Compare
              </Button>
            </div>
            {priceComparison && (
              <div className="mt-4">
                <PriceComparison data={priceComparison} />
              </div>
            )}
          </CardContent>
        </Card>
      </motion.div>

      {/* Recommendations */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
      >
        {recommendations ? (
          <RecommendationsList
            buyRecommendations={recommendations.buy_recommendations}
            sellRecommendations={recommendations.sell_recommendations}
            lastUpdated={recommendations.last_updated}
            isLoading={isLoadingRecommendations}
            onRefresh={handleRefreshRecommendations}
          />
        ) : (
          <Card className="border-2 shadow-lg">
            <CardContent className="pt-6">
              <Skeleton className="h-64 w-full" />
            </CardContent>
          </Card>
        )}
      </motion.div>
    </div>
  )
}

