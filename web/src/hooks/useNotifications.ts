import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/lib/api/client'
import type { DashboardNotification } from '@/lib/api/types'
import { useAuth } from './useAuth'

export function useDashboardNotifications(limit?: number, unreadOnly?: boolean) {
  const { user } = useAuth()

  return useQuery({
    queryKey: ['dashboard-notifications', user?.id, limit, unreadOnly],
    queryFn: async () => {
      try {
        const data = await apiClient.getDashboardNotifications(user!.id, limit, unreadOnly)
        console.log('📬 Fetched notifications:', data)
        return data
      } catch (error) {
        console.error('❌ Error fetching notifications:', error)
        throw error
      }
    },
    enabled: !!user?.id,
    refetchInterval: 15000, // Poll every 15 seconds for real-time updates
    staleTime: 5000, // Consider data stale after 5 seconds
    retry: 2, // Retry failed requests
  })
}

export function useUnreadNotificationCount() {
  const { user } = useAuth()

  return useQuery({
    queryKey: ['unread-notification-count', user?.id],
    queryFn: () => apiClient.getUnreadNotificationCount(user!.id),
    enabled: !!user?.id,
    refetchInterval: 10000, // Poll every 10 seconds for real-time count
    staleTime: 5000,
  })
}
