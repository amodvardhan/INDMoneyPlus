'use client'

import { useAuth } from '@/hooks/useAuth'
import { useHoldings, useRebalance } from '@/hooks/usePortfolio'
import { useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { Modal } from '@/components/ui/modal'
import { formatCurrency } from '@/lib/utils'
import { AlertTriangle, CheckCircle2 } from 'lucide-react'
import { motion } from 'framer-motion'
import { toast } from 'sonner'

export default function RebalancePage() {
  const router = useRouter()
  const { user, isAuthenticated, isLoading } = useAuth()
  const { data: holdings } = useHoldings(user?.id || null)
  const rebalanceMutation = useRebalance()
  const [showConfirmModal, setShowConfirmModal] = useState(false)
  const [targetAllocation, setTargetAllocation] = useState<Record<string, number>>({})

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/login')
    }
  }, [isAuthenticated, isLoading, router])

  const handleRebalance = async () => {
    if (!user || !holdings) return

    try {
      const result = await rebalanceMutation.mutateAsync({
        user_id: user.id,
        portfolio_id: 1, // Mock portfolio ID
        target_alloc: targetAllocation,
      })

      toast.success('Rebalance proposal generated', {
        description: `Estimated cost: ${formatCurrency(result.total_estimated_cost)}`,
      })

      setShowConfirmModal(true)
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Rebalance failed')
    }
  }

  const handleConfirm = async () => {
    // In production, this would call the execution prep endpoint
    toast.success('Rebalance proposal confirmed. Awaiting approval.')
    setShowConfirmModal(false)
    router.push('/portfolio')
  }

  if (isLoading || !isAuthenticated) {
    return (
      <div className="container mx-auto px-4 py-8">
        <Skeleton className="h-64 w-full" />
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <h1 className="text-4xl font-bold mb-2 bg-gradient-to-r from-gray-900 to-gray-700 dark:from-white dark:to-gray-300 bg-clip-text text-transparent">
          Rebalance Portfolio
        </h1>
        <p className="text-lg text-gray-600 dark:text-gray-400">
          Generate a rebalancing proposal based on your target allocation
        </p>
      </motion.div>

      <Card className="mb-6 border-2 shadow-lg">
        <CardHeader>
          <CardTitle className="text-xl">Current Holdings</CardTitle>
        </CardHeader>
        <CardContent>
          {holdings ? (
            <div className="space-y-4">
              {holdings.holdings.slice(0, 5).map((holding) => (
                <div
                  key={`${holding.ticker}-${holding.exchange}`}
                  className="flex items-center justify-between p-4 border rounded-lg"
                >
                  <div>
                    <div className="font-medium">{holding.ticker}</div>
                    <div className="text-sm text-gray-500">{holding.exchange}</div>
                  </div>
                  <div className="text-right">
                    <div className="font-medium">
                      {formatCurrency(holding.total_valuation || 0)}
                    </div>
                    <div className="text-sm text-gray-500">
                      {holding.total_qty} shares
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <Skeleton className="h-64 w-full" />
          )}
        </CardContent>
      </Card>

      <Card className="border-2 shadow-lg">
        <CardHeader>
          <CardTitle className="text-xl">Target Allocation</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4 mb-6">
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Set your target allocation percentages. The AI will generate a rebalancing proposal.
            </p>
            {/* In production, this would be a more sophisticated allocation input */}
            <div className="p-4 border rounded-lg bg-gray-50 dark:bg-gray-800">
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Target allocation editor would go here. For MVP, using default allocation.
              </p>
            </div>
          </div>
          <Button
            onClick={handleRebalance}
            disabled={rebalanceMutation.isPending}
            className="w-full shadow-lg hover:shadow-xl transition-all"
            size="lg"
          >
            {rebalanceMutation.isPending
              ? 'Generating proposal...'
              : 'Generate Rebalance Proposal'}
          </Button>
        </CardContent>
      </Card>

      <Modal
        isOpen={showConfirmModal}
        onClose={() => setShowConfirmModal(false)}
        title="Confirm Rebalance"
        size="md"
      >
        <div className="space-y-4">
          <div className="flex items-start gap-4 p-4 bg-warning-50 dark:bg-warning-900/20 rounded-lg">
            <AlertTriangle className="h-5 w-5 text-warning-600 mt-0.5" />
            <div>
              <h3 className="font-semibold mb-2">Review Before Proceeding</h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                This action will generate orders that require your explicit approval before execution.
                Please review the proposal carefully.
              </p>
            </div>
          </div>
          <div className="flex gap-4">
            <Button
              variant="outline"
              onClick={() => setShowConfirmModal(false)}
              className="flex-1"
            >
              Cancel
            </Button>
            <Button onClick={handleConfirm} className="flex-1">
              <CheckCircle2 className="h-4 w-4 mr-2" />
              Confirm & Proceed
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}

