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
        <h1 className="text-3xl font-bold mb-2">Dashboard</h1>
        <p className="text-gray-600 dark:text-gray-400">
          Welcome back, {user?.email}
        </p>
      </motion.div>

      {/* Net Worth Card */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="mb-6"
      >
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>Net Worth</span>
              <Button variant="ghost" size="sm" onClick={() => router.push('/portfolio')}>
                View Portfolio
              </Button>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="mb-4">
              <div className="text-4xl font-bold mb-2">
                {holdingsLoading ? (
                  <Skeleton className="h-10 w-48" />
                ) : (
                  formatCurrency(totalValue)
                )}
              </div>
              <div className="flex items-center gap-2">
                {todayChange >= 0 ? (
                  <TrendingUp className="h-5 w-5 text-success-600" />
                ) : (
                  <TrendingDown className="h-5 w-5 text-error-600" />
                )}
                <span
                  className={
                    todayChange >= 0 ? 'text-success-600' : 'text-error-600'
                  }
                >
                  {formatCurrency(Math.abs(todayChange))} ({formatPercentage(todayChangePercent)})
                </span>
                <span className="text-gray-500 text-sm">Today</span>
              </div>
            </div>
            <NetWorthChart data={netWorthData} />
          </CardContent>
        </Card>
      </motion.div>

      {/* Stats Grid */}
      <div className="grid md:grid-cols-3 gap-6 mb-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Holdings</CardTitle>
              <DollarSign className="h-4 w-4 text-gray-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {holdingsLoading ? (
                  <Skeleton className="h-8 w-24" />
                ) : (
                  holdings?.holdings.length || 0
                )}
              </div>
              <p className="text-xs text-gray-500">Active positions</p>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Portfolio Value</CardTitle>
              <PieChartIcon className="h-4 w-4 text-gray-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {holdingsLoading ? (
                  <Skeleton className="h-8 w-24" />
                ) : (
                  formatCurrency(totalValue)
                )}
              </div>
              <p className="text-xs text-gray-500">Current valuation</p>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
        >
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Today's Change</CardTitle>
              <TrendingUp className="h-4 w-4 text-gray-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-success-600">
                {formatPercentage(todayChangePercent)}
              </div>
              <p className="text-xs text-gray-500">+{formatCurrency(todayChange)}</p>
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
          <Card>
            <CardHeader>
              <CardTitle>Portfolio Allocation</CardTitle>
            </CardHeader>
            <CardContent>
              <PortfolioChart data={portfolioData} totalValue={totalValue} />
            </CardContent>
          </Card>
        </motion.div>
      )}
    </div>
  )
}
