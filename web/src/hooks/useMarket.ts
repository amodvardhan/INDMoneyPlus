import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/lib/api/client'
import type {
  MarketHealthData,
  PriceComparisonData,
  TopRecommendationsResponse,
  Recommendation,
} from '@/lib/api/types'

export function useMarketHealth() {
  return useQuery({
    queryKey: ['market-health'],
    queryFn: () => apiClient.getMarketHealth(),
    refetchInterval: 60000, // Refetch every minute
    staleTime: 30000, // Consider data stale after 30 seconds
  })
}

export function usePriceComparison(ticker: string | null) {
  return useQuery({
    queryKey: ['price-comparison', ticker],
    queryFn: () => apiClient.getPriceComparison(ticker!),
    enabled: !!ticker,
    refetchInterval: 30000, // Refetch every 30 seconds
  })
}

export function useTopRecommendations(limit?: number, type?: string) {
  return useQuery({
    queryKey: ['top-recommendations', limit, type],
    queryFn: () => apiClient.getTopRecommendations(limit, type),
    refetchInterval: 300000, // Refetch every 5 minutes
    staleTime: 60000, // Consider data stale after 1 minute
  })
}

export function useRecommendationsForTicker(ticker: string | null, exchange?: string) {
  return useQuery({
    queryKey: ['recommendations', ticker, exchange],
    queryFn: () => apiClient.getRecommendationsForTicker(ticker!, exchange),
    enabled: !!ticker,
  })
}

