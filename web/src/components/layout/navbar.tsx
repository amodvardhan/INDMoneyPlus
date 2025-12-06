'use client'

import { useRouter, usePathname } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'
import { Button } from '@/components/ui/button'
import { 
  Home, 
  LayoutDashboard, 
  PieChart, 
  TrendingUp, 
  Settings, 
  LogOut,
  Menu,
  X,
  Sparkles,
  BookOpen,
  BarChart3
} from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { useState } from 'react'
import { cn } from '@/lib/utils'

const navigation = [
  { name: 'Home', href: '/', icon: Home },
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Market', href: '/market', icon: BarChart3 },
  { name: 'Portfolio', href: '/portfolio', icon: PieChart },
  { name: 'Rebalance', href: '/rebalance', icon: TrendingUp },
  { name: 'Handbook', href: '/handbook', icon: BookOpen },
]

export function Navbar() {
  const router = useRouter()
  const pathname = usePathname()
  const { user, isAuthenticated, logout } = useAuth()
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  const handleLogout = async () => {
    await logout()
    router.push('/')
  }

  const isActive = (href: string) => {
    if (href === '/') {
      return pathname === '/'
    }
    return pathname?.startsWith(href)
  }

  return (
    <nav className="sticky top-0 z-50 w-full border-b border-gray-200/80 bg-white/95 backdrop-blur-xl dark:border-gray-800/80 dark:bg-gray-900/95 shadow-sm">
      <div className="container mx-auto px-4">
        <div className="flex h-16 items-center justify-between">
          {/* Logo */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="flex items-center gap-2"
          >
            <div className="flex items-center gap-2 cursor-pointer" onClick={() => router.push('/')}>
              <div className="relative">
                <div className="absolute inset-0 bg-gradient-to-br from-primary-500 to-primary-700 rounded-lg blur-sm opacity-50"></div>
                <div className="relative bg-gradient-to-br from-primary-600 to-primary-800 p-2 rounded-lg">
                  <Sparkles className="h-5 w-5 text-white" />
                </div>
              </div>
              <span className="text-xl font-bold bg-gradient-to-r from-primary-600 to-primary-800 bg-clip-text text-transparent">
                Portfolio+
              </span>
            </div>
          </motion.div>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center gap-1">
            {navigation.map((item) => {
              const Icon = item.icon
              const active = isActive(item.href)
              return (
                <motion.button
                  key={item.name}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => router.push(item.href)}
                  className={cn(
                    'flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all',
                    active
                      ? 'bg-primary-50 text-primary-700 dark:bg-primary-900/30 dark:text-primary-400'
                      : 'text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800'
                  )}
                >
                  <Icon className="h-4 w-4" />
                  {item.name}
                </motion.button>
              )
            })}
          </div>

          {/* Right side - User menu */}
          <div className="flex items-center gap-4">
            {isAuthenticated ? (
              <>
                <div className="hidden md:flex items-center gap-3">
                  <div className="text-right">
                    <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                      {user?.email?.split('@')[0] || 'User'}
                    </div>
                    <div className="text-xs text-gray-500 dark:text-gray-400">
                      {user?.email || ''}
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={handleLogout}
                    className="text-gray-600 hover:text-red-600 dark:text-gray-400 dark:hover:text-red-400"
                  >
                    <LogOut className="h-4 w-4 mr-2" />
                    Logout
                  </Button>
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  className="md:hidden"
                  onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                >
                  {mobileMenuOpen ? (
                    <X className="h-5 w-5" />
                  ) : (
                    <Menu className="h-5 w-5" />
                  )}
                </Button>
              </>
            ) : (
              <div className="flex items-center gap-2">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => router.push('/login')}
                >
                  Sign In
                </Button>
                <Button
                  size="sm"
                  onClick={() => router.push('/register')}
                >
                  Get Started
                </Button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Mobile Menu */}
      <AnimatePresence>
        {mobileMenuOpen && isAuthenticated && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="md:hidden border-t border-gray-200 dark:border-gray-800"
          >
            <div className="container mx-auto px-4 py-4 space-y-2">
              {navigation.map((item) => {
                const Icon = item.icon
                const active = isActive(item.href)
                return (
                  <button
                    key={item.name}
                    onClick={() => {
                      router.push(item.href)
                      setMobileMenuOpen(false)
                    }}
                    className={cn(
                      'w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all',
                      active
                        ? 'bg-primary-50 text-primary-700 dark:bg-primary-900/30 dark:text-primary-400'
                        : 'text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800'
                    )}
                  >
                    <Icon className="h-5 w-5" />
                    {item.name}
                  </button>
                )}
              )}
              <button
                onClick={handleLogout}
                className="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium text-red-600 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-900/20"
              >
                <LogOut className="h-5 w-5" />
                Logout
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </nav>
  )
}

