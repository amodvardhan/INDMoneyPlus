'use client'

import { useState } from 'react'
import { Bell, X, CheckCircle2, AlertCircle, TrendingUp, TrendingDown, Info } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { useUnreadNotificationCount, useDashboardNotifications } from '@/hooks/useNotifications'
import { formatDate } from '@/lib/utils'
import { useRouter } from 'next/navigation'
import { motion, AnimatePresence } from 'framer-motion'
import type { DashboardNotification } from '@/lib/api/types'

export function NotificationBell() {
  const [isOpen, setIsOpen] = useState(false)
  const router = useRouter()
  const { data: unreadCount, isLoading: countLoading } = useUnreadNotificationCount()
  const { data: notifications, isLoading: notificationsLoading, error: notificationsError } = useDashboardNotifications(10, false)

  const getNotificationIcon = (type: string, priority: string) => {
    if (type === 'new_recommendation') {
      return priority === 'high' ? <TrendingUp className="h-4 w-4" /> : <Info className="h-4 w-4" />
    }
    if (type === 'price_alert') {
      return <AlertCircle className="h-4 w-4" />
    }
    return <Info className="h-4 w-4" />
  }

  const getNotificationColor = (priority: string) => {
    switch (priority) {
      case 'urgent':
        return 'border-red-500 bg-red-50 dark:bg-red-900/20'
      case 'high':
        return 'border-orange-500 bg-orange-50 dark:bg-orange-900/20'
      case 'normal':
        return 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
      default:
        return 'border-gray-500 bg-gray-50 dark:bg-gray-900/20'
    }
  }

  const handleNotificationClick = (notification: DashboardNotification) => {
    if (notification.action_url) {
      router.push(notification.action_url)
      setIsOpen(false)
    }
  }

  return (
    <div className="relative">
      <Button
        variant="ghost"
        size="icon"
        onClick={() => setIsOpen(!isOpen)}
        className="relative"
      >
        <Bell className="h-5 w-5" />
        {unreadCount && unreadCount.unread_count > 0 && (
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            className="absolute -top-1 -right-1 min-w-[20px] h-5 px-1 rounded-full bg-red-500 flex items-center justify-center"
          >
            <span className="text-xs font-bold text-white">
              {unreadCount.unread_count > 99 ? '99+' : unreadCount.unread_count}
            </span>
          </motion.div>
        )}
      </Button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: -10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -10, scale: 0.95 }}
            className="absolute right-0 top-12 z-50 w-96"
          >
            <Card className="shadow-2xl border-2">
              <CardHeader className="flex flex-row items-center justify-between pb-3">
                <CardTitle className="text-lg">Notifications</CardTitle>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => setIsOpen(false)}
                  className="h-6 w-6"
                >
                  <X className="h-4 w-4" />
                </Button>
              </CardHeader>
              <CardContent className="p-0">
                <div className="h-[500px] overflow-y-auto">
                  {notificationsLoading ? (
                    <div className="flex flex-col items-center justify-center h-full p-8 text-center">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mb-4"></div>
                      <p className="text-sm text-gray-500 dark:text-gray-400">Loading notifications...</p>
                    </div>
                  ) : notificationsError ? (
                    <div className="flex flex-col items-center justify-center h-full p-8 text-center">
                      <AlertCircle className="h-12 w-12 text-red-400 mb-4 opacity-50" />
                      <p className="text-sm text-red-500 dark:text-red-400">Failed to load notifications</p>
                      <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                        {notificationsError instanceof Error ? notificationsError.message : 'Unknown error'}
                      </p>
                    </div>
                  ) : notifications && Array.isArray(notifications) && notifications.length > 0 ? (
                    <div className="space-y-2 p-2">
                      {notifications.map((notification) => (
                        <motion.div
                          key={notification.id}
                          initial={{ opacity: 0, x: -20 }}
                          animate={{ opacity: 1, x: 0 }}
                          className={`p-3 rounded-lg border-2 cursor-pointer hover:shadow-md transition-all ${getNotificationColor(notification.priority)}`}
                          onClick={() => handleNotificationClick(notification)}
                        >
                          <div className="flex items-start gap-3">
                            <div className="mt-0.5">
                              {getNotificationIcon(notification.type, notification.priority)}
                            </div>
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center justify-between mb-1">
                                <h4 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                                  {notification.title}
                                </h4>
                                {!notification.read && (
                                  <div className="h-2 w-2 rounded-full bg-blue-500 flex-shrink-0" />
                                )}
                              </div>
                              <p className="text-xs text-gray-600 dark:text-gray-400 line-clamp-2">
                                {notification.message}
                              </p>
                              <div className="flex items-center gap-2 mt-2">
                                {notification.ticker && (
                                  <Badge variant="outline" className="text-xs">
                                    {notification.ticker}
                                  </Badge>
                                )}
                                <span className="text-xs text-gray-500">
                                  {formatDate(notification.created_at, 'relative')}
                                </span>
                              </div>
                            </div>
                          </div>
                        </motion.div>
                      ))}
                    </div>
                  ) : (
                    <div className="flex flex-col items-center justify-center h-full p-8 text-center">
                      <Bell className="h-12 w-12 text-gray-400 mb-4 opacity-50" />
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        {notifications && Array.isArray(notifications) && notifications.length === 0
                          ? 'No notifications yet'
                          : 'No notifications available'}
                      </p>
                      {notificationsError && (
                        <p className="text-xs text-red-500 mt-2">
                          Error: {notificationsError instanceof Error ? notificationsError.message : String(notificationsError)}
                        </p>
                      )}
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
