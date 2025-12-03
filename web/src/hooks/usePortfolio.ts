import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '@/lib/api/client'
import type { HoldingsResponse, RebalanceRequest, RebalanceResponse } from '@/lib/api/types'

export function useHoldings(userId: number | null) {
  return useQuery({
    queryKey: ['holdings', userId],
    queryFn: () => apiClient.getHoldings(userId!),
    enabled: !!userId,
    refetchInterval: 30000, // Refetch every 30 seconds
    staleTime: 10000, // Consider data stale after 10 seconds
  })
}

export function useRebalance() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: RebalanceRequest) => apiClient.rebalancePortfolio(data),
    onSuccess: () => {
      // Invalidate holdings to refetch after rebalance
      queryClient.invalidateQueries({ queryKey: ['holdings'] })
    },
  })
}

