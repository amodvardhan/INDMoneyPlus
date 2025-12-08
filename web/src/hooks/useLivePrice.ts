import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/lib/api/client'
import type { LatestPriceResponse, PriceTimeseriesResponse } from '@/lib/api/types'

export function useLatestPrice(ticker: string | null, exchange: string | null) {
  return useQuery({
    queryKey: ['price', ticker, exchange, 'latest'],
    queryFn: () => apiClient.getLatestPrice(ticker!, exchange!),
    enabled: !!ticker && !!exchange,
    refetchInterval: 5000, // Refetch every 5 seconds for live prices
    staleTime: 2000,
  })
}

export function usePriceTimeseries(
  ticker: string | null,
  exchange: string | null,
  fromDate: string,
  toDate: string
) {
  return useQuery({
    queryKey: ['price', ticker, exchange, 'timeseries', fromDate, toDate],
    queryFn: () => {
      console.log('🔄 Fetching price timeseries:', { ticker, exchange, fromDate, toDate })
      return apiClient.getPriceTimeseries(ticker!, exchange!, fromDate, toDate)
    },
    enabled: !!ticker && !!exchange && !!fromDate && !!toDate,
    staleTime: 0, // Always refetch when period changes
    gcTime: 300000, // Keep in cache for 5 minutes
    refetchOnMount: true,
    refetchOnWindowFocus: false,
  })
}

