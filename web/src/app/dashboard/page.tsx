'use client'

import { useAuth } from '@/hooks/useAuth'
import { useHoldings } from '@/hooks/usePortfolio'
import { useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { NetWorthChart } from '@/components/charts/net-worth-chart'
import { PortfolioChart } from '@/components/charts/portfolio-chart'
import { formatCurrency, formatPercentage } from '@/lib/utils'
import { TrendingUp, TrendingDown, DollarSign, PieChart as PieChartIcon } from 'lucide-react'
import { motion } from 'framer-motion'

export default function DashboardPage() {
  const router = useRouter()
  const { user, isAuthenticated, isLoading } = useAuth()
  const { data: holdings, isLoading: holdingsLoading } = useHoldings(user?.id || null)
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  useEffect(() => {
    if (mounted && !isLoading && !isAuthenticated) {
      router.push('/login')
    }
  }, [mounted, isAuthenticated, isLoading, router])

  // Show loading state during SSR and initial hydration
  if (!mounted || isLoading || !isAuthenticated) {
    return (
      <div className="container mx-auto px-4 py-8">
        <Skeleton className="h-64 w-full mb-6" />
        <div className="grid md:grid-cols-2 gap-6">
          <Skeleton className="h-64" />
          <Skeleton className="h-64" />
        </div>
      </div>
    )
  }

  const totalValue = holdings?.total_valuation || 0
  const todayChange = 12500 // Mock data - would come from backend
  const todayChangePercent = 1.25 // Mock data

  // Mock net worth data
  const netWorthData = [
    { date: '2024-01-01', value: 950000 },
    { date: '2024-02-01', value: 980000 },
    { date: '2024-03-01', value: 1020000 },
    { date: '2024-04-01', value: 1000000 },
    { date: '2024-05-01', value: 1012500 },
  ]

  // Mock portfolio allocation data
  const portfolioData = holdings?.holdings.slice(0, 5).map((holding, index) => ({
    name: holding.ticker || 'Unknown',
    value: holding.total_valuation || 0,
    color: ['#0ea5e9', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6'][index],
  })) || []

  return (
    <div className="container mx-auto px-4 py-8">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-4xl font-bold mb-2 bg-gradient-to-r from-gray-900 to-gray-700 dark:from-white dark:to-gray-300 bg-clip-text text-transparent">
              Dashboard
            </h1>
            <p className="text-gray-600 dark:text-gray-400 text-lg">
              Welcome back, <span className="font-semibold text-gray-900 dark:text-white">{user?.email?.split('@')[0]}</span>
            </p>
          </div>
        </div>
      </motion.div>

      {/* Net Worth Card */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="mb-6"
      >
        <Card className="border-2 border-primary-100 dark:border-primary-900/50 shadow-xl bg-gradient-to-br from-white to-primary-50/30 dark:from-gray-900 dark:to-primary-950/30">
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span className="text-2xl">Net Worth</span>
              <Button variant="ghost" size="sm" onClick={() => router.push('/portfolio')} className="hover:bg-primary-100 dark:hover:bg-primary-900/30">
                View Portfolio →
              </Button>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="mb-6">
              <div className="text-5xl md:text-6xl font-extrabold mb-3 bg-gradient-to-r from-primary-600 to-primary-800 bg-clip-text text-transparent">
                {holdingsLoading ? (
                  <Skeleton className="h-16 w-64" />
                ) : (
                  formatCurrency(totalValue)
                )}
              </div>
              <div className="flex items-center gap-3">
                <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full ${
                  todayChange >= 0 
                    ? 'bg-success-100 text-success-700 dark:bg-success-900/30 dark:text-success-400' 
                    : 'bg-error-100 text-error-700 dark:bg-error-900/30 dark:text-error-400'
                }`}>
                  {todayChange >= 0 ? (
                    <TrendingUp className="h-5 w-5" />
                  ) : (
                    <TrendingDown className="h-5 w-5" />
                  )}
                  <span className="font-semibold">
                    {formatCurrency(Math.abs(todayChange))} ({formatPercentage(todayChangePercent)})
                  </span>
                </div>
                <span className="text-gray-500 text-sm">Today</span>
              </div>
            </div>
            <div className="bg-white dark:bg-gray-800 rounded-xl p-4">
              <NetWorthChart data={netWorthData} />
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Stats Grid */}
      <div className="grid md:grid-cols-3 gap-6 mb-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          whileHover={{ y: -5 }}
        >
          <Card className="border-2 hover:border-primary-200 dark:hover:border-primary-800 hover:shadow-lg transition-all">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-gray-600 dark:text-gray-400">Total Holdings</CardTitle>
              <div className="p-2 rounded-lg bg-primary-100 dark:bg-primary-900/30">
                <DollarSign className="h-5 w-5 text-primary-600 dark:text-primary-400" />
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold mb-1">
                {holdingsLoading ? (
                  <Skeleton className="h-9 w-20" />
                ) : (
                  holdings?.holdings.length || 0
                )}
              </div>
              <p className="text-xs text-gray-500 dark:text-gray-400">Active positions</p>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          whileHover={{ y: -5 }}
        >
          <Card className="border-2 hover:border-primary-200 dark:hover:border-primary-800 hover:shadow-lg transition-all">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-gray-600 dark:text-gray-400">Portfolio Value</CardTitle>
              <div className="p-2 rounded-lg bg-primary-100 dark:bg-primary-900/30">
                <PieChartIcon className="h-5 w-5 text-primary-600 dark:text-primary-400" />
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold mb-1">
                {holdingsLoading ? (
                  <Skeleton className="h-9 w-32" />
                ) : (
                  formatCurrency(totalValue)
                )}
              </div>
              <p className="text-xs text-gray-500 dark:text-gray-400">Current valuation</p>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          whileHover={{ y: -5 }}
        >
          <Card className="border-2 hover:border-primary-200 dark:hover:border-primary-800 hover:shadow-lg transition-all">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-gray-600 dark:text-gray-400">Today's Change</CardTitle>
              <div className="p-2 rounded-lg bg-success-100 dark:bg-success-900/30">
                <TrendingUp className="h-5 w-5 text-success-600 dark:text-success-400" />
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-success-600 dark:text-success-400 mb-1">
                {formatPercentage(todayChangePercent)}
              </div>
              <p className="text-xs text-gray-500 dark:text-gray-400">+{formatCurrency(todayChange)}</p>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Portfolio Allocation */}
      {portfolioData.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
        >
          <Card className="border-2 shadow-lg">
            <CardHeader>
              <CardTitle className="text-xl">Portfolio Allocation</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="bg-white dark:bg-gray-800 rounded-xl p-4">
                <PortfolioChart data={portfolioData} totalValue={totalValue} />
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}
    </div>
  )
}
