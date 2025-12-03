'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { TrendingUp, Shield, Zap, BarChart3 } from 'lucide-react'
import { motion } from 'framer-motion'

export default function HomePage() {
  const router = useRouter()
  const { isAuthenticated } = useAuth()

  useEffect(() => {
    if (isAuthenticated) {
      router.push('/dashboard')
    }
  }, [isAuthenticated, router])

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 via-white to-primary-100 dark:from-gray-900 dark:via-gray-900 dark:to-gray-800">
      <div className="container mx-auto px-4 py-16">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="text-center mb-16"
        >
          <h1 className="text-5xl md:text-6xl font-bold mb-4 bg-gradient-to-r from-primary-600 to-primary-400 bg-clip-text text-transparent">
            Portfolio Superapp
          </h1>
          <p className="text-xl text-gray-600 dark:text-gray-300 max-w-2xl mx-auto">
            World-class portfolio management powered by AI. Track, analyze, and optimize your investments across India and US markets.
          </p>
        </motion.div>

        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 mb-16">
          {features.map((feature, index) => (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
            >
              <Card className="h-full hover:shadow-lg transition-shadow">
                <CardHeader>
                  <div className="w-12 h-12 rounded-lg bg-primary-100 dark:bg-primary-900 flex items-center justify-center mb-4">
                    <feature.icon className="h-6 w-6 text-primary-600 dark:text-primary-400" />
                  </div>
                  <CardTitle className="text-xl">{feature.title}</CardTitle>
                  <CardDescription>{feature.description}</CardDescription>
                </CardHeader>
              </Card>
            </motion.div>
          ))}
        </div>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.4 }}
          className="text-center"
        >
          <div className="flex gap-4 justify-center">
            <Button
              size="lg"
              onClick={() => router.push('/login')}
              className="text-lg px-8"
            >
              Get Started
            </Button>
            <Button
              size="lg"
              variant="outline"
              onClick={() => router.push('/login')}
              className="text-lg px-8"
            >
              Sign In
            </Button>
          </div>
        </motion.div>
      </div>
    </div>
  )
}

const features = [
  {
    icon: TrendingUp,
    title: 'Smart Analytics',
    description: 'AI-powered insights and recommendations for your portfolio',
  },
  {
    icon: Shield,
    title: 'Secure & Private',
    description: 'Bank-level security with end-to-end encryption',
  },
  {
    icon: Zap,
    title: 'Real-time Updates',
    description: 'Live market data and instant portfolio valuations',
  },
  {
    icon: BarChart3,
    title: 'Multi-Market',
    description: 'Track investments across India and US markets',
  },
]
