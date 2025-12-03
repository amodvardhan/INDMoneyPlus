'use client'

import { useAuth } from '@/hooks/useAuth'
import { useHoldings } from '@/hooks/usePortfolio'
import { useRouter } from 'next/navigation'
import { useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { Badge } from '@/components/ui/badge'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { formatCurrency, formatPercentage, formatNumber } from '@/lib/utils'
import { TrendingUp, TrendingDown, Search } from 'lucide-react'
import { motion } from 'framer-motion'
import { useState } from 'react'
import { Input } from '@/components/ui/input'

export default function PortfolioPage() {
  const router = useRouter()
  const { user, isAuthenticated, isLoading } = useAuth()
  const { data: holdings, isLoading: holdingsLoading } = useHoldings(user?.id || null)
  const [searchQuery, setSearchQuery] = useState('')

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/login')
    }
  }, [isAuthenticated, isLoading, router])

  if (isLoading || !isAuthenticated) {
    return (
      <div className="container mx-auto px-4 py-8">
        <Skeleton className="h-64 w-full" />
      </div>
    )
  }

  const filteredHoldings = holdings?.holdings.filter((holding) => {
    if (!searchQuery) return true
    const query = searchQuery.toLowerCase()
    return (
      holding.ticker?.toLowerCase().includes(query) ||
      holding.isin?.toLowerCase().includes(query) ||
      holding.exchange?.toLowerCase().includes(query)
    )
  }) || []

  const totalValue = holdings?.total_valuation || 0

  return (
    <div className="container mx-auto px-4 py-8">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-3xl font-bold mb-2">Portfolio</h1>
            <p className="text-gray-600 dark:text-gray-400">
              {holdingsLoading ? (
                <Skeleton className="h-4 w-48 inline-block" />
              ) : (
                `Total Value: ${formatCurrency(totalValue)}`
              )}
            </p>
          </div>
          <Button onClick={() => router.push('/rebalance')}>
            Rebalance Portfolio
          </Button>
        </div>

        <div className="relative mb-6">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          <Input
            placeholder="Search holdings..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
      >
        <Card>
          <CardHeader>
            <CardTitle>Holdings</CardTitle>
          </CardHeader>
          <CardContent>
            {holdingsLoading ? (
              <div className="space-y-4">
                {[1, 2, 3, 4, 5].map((i) => (
                  <Skeleton key={i} className="h-16 w-full" />
                ))}
              </div>
            ) : filteredHoldings.length === 0 ? (
              <div className="text-center py-12">
                <p className="text-gray-500">No holdings found</p>
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Instrument</TableHead>
                    <TableHead>Exchange</TableHead>
                    <TableHead className="text-right">Quantity</TableHead>
                    <TableHead className="text-right">Avg Price</TableHead>
                    <TableHead className="text-right">Current Value</TableHead>
                    <TableHead className="text-right">P&L</TableHead>
                    <TableHead className="text-right">Allocation</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredHoldings.map((holding) => {
                    const currentValue = holding.total_valuation || 0
                    const avgPrice = holding.avg_price || 0
                    const quantity = holding.total_qty
                    const costBasis = avgPrice * quantity
                    const pnl = currentValue - costBasis
                    const pnlPercent = costBasis > 0 ? (pnl / costBasis) * 100 : 0
                    const allocation = totalValue > 0 ? (currentValue / totalValue) * 100 : 0

                    return (
                      <TableRow
                        key={`${holding.ticker}-${holding.exchange}`}
                        className="cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800"
                        onClick={() =>
                          router.push(
                            `/instruments/${holding.ticker}?exchange=${holding.exchange}`
                          )
                        }
                      >
                        <TableCell className="font-medium">
                          <div>
                            <div>{holding.ticker || 'N/A'}</div>
                            {holding.isin && (
                              <div className="text-xs text-gray-500">{holding.isin}</div>
                            )}
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge variant="outline">{holding.exchange || 'N/A'}</Badge>
                        </TableCell>
                        <TableCell className="text-right">
                          {formatNumber(quantity)}
                        </TableCell>
                        <TableCell className="text-right">
                          {avgPrice > 0 ? formatCurrency(avgPrice) : 'N/A'}
                        </TableCell>
                        <TableCell className="text-right font-medium">
                          {formatCurrency(currentValue)}
                        </TableCell>
                        <TableCell className="text-right">
                          <div
                            className={`flex items-center justify-end gap-1 ${
                              pnl >= 0 ? 'text-success-600' : 'text-error-600'
                            }`}
                          >
                            {pnl >= 0 ? (
                              <TrendingUp className="h-4 w-4" />
                            ) : (
                              <TrendingDown className="h-4 w-4" />
                            )}
                            <span>{formatCurrency(pnl)}</span>
                            <span className="text-xs">
                              ({formatPercentage(pnlPercent)})
                            </span>
                          </div>
                        </TableCell>
                        <TableCell className="text-right">
                          {formatPercentage(allocation)}
                        </TableCell>
                      </TableRow>
                    )
                  })}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </motion.div>
    </div>
  )
}

