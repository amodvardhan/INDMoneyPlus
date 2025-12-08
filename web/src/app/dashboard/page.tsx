'use client'

import { useAuth } from '@/hooks/useAuth'
import { useHoldings } from '@/hooks/usePortfolio'
import { useMarketHealth } from '@/hooks/useMarket'
import { useRouter } from 'next/navigation'
import { useEffect, useState, useMemo } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { Badge } from '@/components/ui/badge'
import { NetWorthChart } from '@/components/charts/net-worth-chart'
import { PortfolioChart } from '@/components/charts/portfolio-chart'
import { formatCurrency, formatPercentage } from '@/lib/utils'
import { TrendingUp, TrendingDown, Wallet, PieChart as PieChartIcon, ArrowUpRight, ArrowDownRight, Activity, Sparkles } from 'lucide-react'
import { motion } from 'framer-motion'

export default function DashboardPage() {
  const router = useRouter()
  const { user, isAuthenticated, isLoading } = useAuth()
  const { data: holdings, isLoading: holdingsLoading } = useHoldings(user?.id || null)
  const { data: marketHealth } = useMarketHealth()
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  useEffect(() => {
    if (mounted && !isLoading && !isAuthenticated) {
      router.push('/login')
    }
  }, [mounted, isAuthenticated, isLoading, router])

  // Calculate today's change from portfolio holdings
  const portfolioChange = useMemo(() => {
    if (!holdings?.holdings || holdings.holdings.length === 0) {
      return { change: 0, changePercent: 0 }
    }

    // Calculate current total value
    const currentValue = holdings.total_valuation || 0

    // For now, we'll estimate change based on market health overall change
    // In a real implementation, we'd fetch yesterday's portfolio value
    const marketChangePercent = marketHealth?.overall_change_percent || 0
    const estimatedChange = (currentValue * marketChangePercent) / 100
    const changePercent = marketChangePercent

    return {
      change: estimatedChange,
      changePercent: changePercent
    }
  }, [holdings, marketHealth])

  // Generate net worth chart data from holdings (last 30 days approximation)
  const netWorthData = useMemo(() => {
    if (!holdings?.total_valuation) return []

    const currentValue = holdings.total_valuation
    const days = 30
    const data = []
    const today = new Date()

    // Generate historical data points (approximation based on current value and market trends)
    for (let i = days; i >= 0; i--) {
      const date = new Date(today)
      date.setDate(date.getDate() - i)

      // Approximate value based on current value and days back
      // This is a simplified approach - in production, you'd store historical portfolio values
      const marketTrend = marketHealth?.overall_change_percent || 0
      const daysBack = i
      const trendFactor = 1 - (marketTrend / 100) * (daysBack / days)
      const estimatedValue = currentValue * trendFactor

      data.push({
        date: date.toISOString().split('T')[0],
        value: Math.max(0, estimatedValue)
      })
    }

    return data
  }, [holdings?.total_valuation, marketHealth])

  // Portfolio allocation data from real holdings
  const portfolioData = useMemo(() => {
    if (!holdings?.holdings || holdings.holdings.length === 0) return []

    const colors = [
      '#0ea5e9', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6',
      '#ec4899', '#14b8a6', '#f97316', '#6366f1', '#a855f7'
    ]

    return holdings.holdings
      .filter(h => h.total_valuation && h.total_valuation > 0)
      .sort((a, b) => (b.total_valuation || 0) - (a.total_valuation || 0))
      .slice(0, 10)
      .map((holding, index) => ({
        name: holding.ticker || 'Unknown',
        value: holding.total_valuation || 0,
        color: colors[index % colors.length],
      }))
  }, [holdings?.holdings])

  // Show loading state during SSR and initial hydration
  if (!mounted || isLoading || !isAuthenticated) {
    return (
      <div className="container mx-auto px-4 py-8 max-w-7xl">
        <Skeleton className="h-64 w-full mb-6" />
        <div className="grid md:grid-cols-3 gap-6">
          <Skeleton className="h-32" />
          <Skeleton className="h-32" />
          <Skeleton className="h-32" />
        </div>
      </div>
    )
  }

  const totalValue = holdings?.total_valuation || 0
  const todayChange = portfolioChange.change
  const todayChangePercent = portfolioChange.changePercent
  const isPositive = todayChange >= 0

  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-4xl md:text-5xl font-bold mb-2 bg-gradient-to-r from-primary-600 via-primary-700 to-primary-800 bg-clip-text text-transparent">
              Dashboard
            </h1>
            <p className="text-gray-600 dark:text-gray-400 text-lg">
              Welcome back, <span className="font-semibold text-gray-900 dark:text-white">{user?.email?.split('@')[0]}</span>
            </p>
          </div>
          {marketHealth && (
            <Badge
              variant="outline"
              className={`text-sm px-4 py-2 ${marketHealth.condition === 'strong_bull' || marketHealth.condition === 'bull'
                  ? 'bg-green-50 text-green-700 border-green-300 dark:bg-green-900/30 dark:text-green-400'
                  : marketHealth.condition === 'strong_bear' || marketHealth.condition === 'bear'
                    ? 'bg-red-50 text-red-700 border-red-300 dark:bg-red-900/30 dark:text-red-400'
                    : 'bg-gray-50 text-gray-700 border-gray-300 dark:bg-gray-800 dark:text-gray-400'
                }`}
            >
              <Activity className="h-4 w-4 mr-2 inline" />
              {marketHealth.condition.replace('_', ' ').toUpperCase()} Market
            </Badge>
          )}
        </div>
      </motion.div>

      {/* Net Worth Card - Modern Design */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="mb-8"
      >
        <Card className="border-2 border-primary-200 dark:border-primary-800 shadow-2xl bg-gradient-to-br from-white via-primary-50/20 to-primary-100/30 dark:from-gray-900 dark:via-primary-950/20 dark:to-primary-900/30 overflow-hidden">
          <div className="absolute top-0 right-0 w-64 h-64 bg-primary-200/20 dark:bg-primary-800/20 rounded-full blur-3xl -mr-32 -mt-32"></div>
          <CardHeader className="relative">
            <div className="flex items-center justify-between">
              <CardTitle className="text-2xl flex items-center gap-2">
                <div className="p-2 bg-primary-100 dark:bg-primary-900/50 rounded-lg">
                  <Wallet className="h-6 w-6 text-primary-600 dark:text-primary-400" />
                </div>
                <span>Portfolio Value</span>
              </CardTitle>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => router.push('/portfolio')}
                className="hover:bg-primary-100 dark:hover:bg-primary-900/30"
              >
                View Details
                <ArrowUpRight className="h-4 w-4 ml-1" />
              </Button>
            </div>
          </CardHeader>
          <CardContent className="relative">
            <div className="mb-6">
              <div className="text-5xl md:text-7xl font-extrabold mb-4 bg-gradient-to-r from-primary-600 via-primary-700 to-primary-800 bg-clip-text text-transparent">
                {holdingsLoading ? (
                  <Skeleton className="h-20 w-80" />
                ) : (
                  formatCurrency(totalValue)
                )}
              </div>
              <div className="flex items-center gap-4">
                <motion.div
                  initial={{ scale: 0.9 }}
                  animate={{ scale: 1 }}
                  className={`flex items-center gap-2 px-4 py-2 rounded-xl font-semibold ${isPositive
                      ? 'bg-green-50 text-green-700 dark:bg-green-900/30 dark:text-green-400 border-2 border-green-200 dark:border-green-800'
                      : 'bg-red-50 text-red-700 dark:bg-red-900/30 dark:text-red-400 border-2 border-red-200 dark:border-red-800'
                    }`}
                >
                  {isPositive ? (
                    <ArrowUpRight className="h-5 w-5" />
                  ) : (
                    <ArrowDownRight className="h-5 w-5" />
                  )}
                  <span>
                    {formatCurrency(Math.abs(todayChange))} ({formatPercentage(todayChangePercent)})
                  </span>
                </motion.div>
                <span className="text-gray-500 dark:text-gray-400 text-sm font-medium">Today</span>
              </div>
            </div>
            {netWorthData.length > 0 && (
              <div className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-xl p-4 border border-gray-200 dark:border-gray-700">
                <NetWorthChart data={netWorthData} />
              </div>
            )}
          </CardContent>
        </Card>
      </motion.div>

      {/* Stats Grid - Modern Cards */}
      <div className="grid md:grid-cols-3 gap-6 mb-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          whileHover={{ y: -4, scale: 1.02 }}
          className="transition-transform"
        >
          <Card className="border-2 hover:border-primary-300 dark:hover:border-primary-700 hover:shadow-xl transition-all bg-gradient-to-br from-white to-blue-50/30 dark:from-gray-900 dark:to-blue-950/30">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3">
              <CardTitle className="text-sm font-semibold text-gray-700 dark:text-gray-300">Total Holdings</CardTitle>
              <div className="p-2.5 rounded-xl bg-blue-100 dark:bg-blue-900/50 shadow-sm">
                <Wallet className="h-5 w-5 text-blue-600 dark:text-blue-400" />
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-4xl font-bold mb-1 text-gray-900 dark:text-white">
                {holdingsLoading ? (
                  <Skeleton className="h-10 w-16" />
                ) : (
                  holdings?.holdings.length || 0
                )}
              </div>
              <p className="text-xs text-gray-500 dark:text-gray-400 font-medium">Active positions</p>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          whileHover={{ y: -4, scale: 1.02 }}
          className="transition-transform"
        >
          <Card className="border-2 hover:border-primary-300 dark:hover:border-primary-700 hover:shadow-xl transition-all bg-gradient-to-br from-white to-purple-50/30 dark:from-gray-900 dark:to-purple-950/30">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3">
              <CardTitle className="text-sm font-semibold text-gray-700 dark:text-gray-300">Portfolio Value</CardTitle>
              <div className="p-2.5 rounded-xl bg-purple-100 dark:bg-purple-900/50 shadow-sm">
                <PieChartIcon className="h-5 w-5 text-purple-600 dark:text-purple-400" />
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-4xl font-bold mb-1 text-gray-900 dark:text-white">
                {holdingsLoading ? (
                  <Skeleton className="h-10 w-40" />
                ) : (
                  formatCurrency(totalValue)
                )}
              </div>
              <p className="text-xs text-gray-500 dark:text-gray-400 font-medium">Current valuation</p>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          whileHover={{ y: -4, scale: 1.02 }}
          className="transition-transform"
        >
          <Card className={`border-2 hover:shadow-xl transition-all bg-gradient-to-br ${isPositive
              ? 'from-white to-green-50/30 dark:from-gray-900 dark:to-green-950/30 hover:border-green-300 dark:hover:border-green-700'
              : 'from-white to-red-50/30 dark:from-gray-900 dark:to-red-950/30 hover:border-red-300 dark:hover:border-red-700'
            }`}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3">
              <CardTitle className="text-sm font-semibold text-gray-700 dark:text-gray-300">Today's Change</CardTitle>
              <div className={`p-2.5 rounded-xl shadow-sm ${isPositive
                  ? 'bg-green-100 dark:bg-green-900/50'
                  : 'bg-red-100 dark:bg-red-900/50'
                }`}>
                {isPositive ? (
                  <TrendingUp className="h-5 w-5 text-green-600 dark:text-green-400" />
                ) : (
                  <TrendingDown className="h-5 w-5 text-red-600 dark:text-red-400" />
                )}
              </div>
            </CardHeader>
            <CardContent>
              <div className={`text-4xl font-bold mb-1 ${isPositive
                  ? 'text-green-600 dark:text-green-400'
                  : 'text-red-600 dark:text-red-400'
                }`}>
                {formatPercentage(todayChangePercent)}
              </div>
              <p className={`text-xs font-medium ${isPositive
                  ? 'text-green-600 dark:text-green-400'
                  : 'text-red-600 dark:text-red-400'
                }`}>
                {isPositive ? '+' : ''}{formatCurrency(todayChange)}
              </p>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Portfolio Allocation - Modern Design */}
      {portfolioData.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
        >
          <Card className="border-2 shadow-xl bg-gradient-to-br from-white to-gray-50/50 dark:from-gray-900 dark:to-gray-800/50">
            <CardHeader className="border-b border-gray-200 dark:border-gray-700">
              <div className="flex items-center justify-between">
                <CardTitle className="text-xl flex items-center gap-2">
                  <div className="p-2 bg-primary-100 dark:bg-primary-900/50 rounded-lg">
                    <PieChartIcon className="h-5 w-5 text-primary-600 dark:text-primary-400" />
                  </div>
                  Portfolio Allocation
                </CardTitle>
                <Badge variant="outline" className="text-xs">
                  Top {portfolioData.length} Holdings
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="pt-6">
              <div className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-xl p-6 border border-gray-200 dark:border-gray-700">
                <PortfolioChart data={portfolioData} totalValue={totalValue} />
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Empty State */}
      {!holdingsLoading && (!holdings || holdings.holdings.length === 0) && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
        >
          <Card className="border-2 border-dashed border-gray-300 dark:border-gray-700">
            <CardContent className="pt-12 pb-12 text-center">
              <div className="p-4 bg-gray-100 dark:bg-gray-800 rounded-full w-20 h-20 mx-auto mb-4 flex items-center justify-center">
                <Wallet className="h-10 w-10 text-gray-400" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                No Holdings Yet
              </h3>
              <p className="text-gray-600 dark:text-gray-400 mb-6 max-w-md mx-auto">
                Start building your portfolio by adding your first holding or importing from your broker.
              </p>
              <div className="flex gap-3 justify-center">
                <Button onClick={() => router.push('/portfolio')}>
                  <Sparkles className="h-4 w-4 mr-2" />
                  View Portfolio
                </Button>
                <Button variant="outline" onClick={() => router.push('/market')}>
                  Explore Market
                </Button>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}
    </div>
  )
}
