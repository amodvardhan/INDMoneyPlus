'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { TrendingUp, Shield, Zap, BarChart3, ArrowRight, Sparkles } from 'lucide-react'
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
    <div className="relative min-h-[calc(100vh-4rem)] overflow-hidden">
      {/* Background gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-primary-50/50 via-white to-primary-100/30 dark:from-gray-900 dark:via-gray-950 dark:to-gray-900"></div>
      
      {/* Animated background elements */}
      <motion.div 
        className="absolute top-0 left-1/4 w-96 h-96 bg-primary-200/20 rounded-full blur-3xl"
        animate={{
          scale: [1, 1.2, 1],
          opacity: [0.3, 0.5, 0.3],
        }}
        transition={{
          duration: 8,
          repeat: Infinity,
          ease: "easeInOut",
        }}
      />
      <motion.div 
        className="absolute bottom-0 right-1/4 w-96 h-96 bg-primary-300/20 rounded-full blur-3xl"
        animate={{
          scale: [1, 1.2, 1],
          opacity: [0.3, 0.5, 0.3],
        }}
        transition={{
          duration: 8,
          repeat: Infinity,
          ease: "easeInOut",
          delay: 1,
        }}
      />

      <div className="relative container mx-auto px-4 py-20">
        {/* Hero Section */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="text-center mb-20 max-w-4xl mx-auto"
        >
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ delay: 0.2, duration: 0.5 }}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 text-sm font-medium mb-6"
          >
            <Sparkles className="h-4 w-4" />
            AI-Powered Portfolio Management
          </motion.div>
          
          <h1 className="text-6xl md:text-7xl font-extrabold mb-6 leading-tight">
            <span className="bg-gradient-to-r from-primary-600 via-primary-500 to-primary-700 bg-clip-text text-transparent">
              Smart Portfolio
            </span>
            <br />
            <span className="text-gray-900 dark:text-white">Management</span>
          </h1>
          
          <p className="text-xl md:text-2xl text-gray-600 dark:text-gray-300 mb-8 leading-relaxed">
            Track, analyze, and optimize your investments across India and US markets with AI-powered insights
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
            <Button
              size="lg"
              onClick={() => router.push('/register')}
              className="text-lg px-8 py-6 h-auto shadow-lg hover:shadow-xl transition-all group"
            >
              Get Started Free
              <ArrowRight className="ml-2 h-5 w-5 group-hover:translate-x-1 transition-transform" />
            </Button>
            <Button
              size="lg"
              variant="outline"
              onClick={() => router.push('/login')}
              className="text-lg px-8 py-6 h-auto border-2 hover:bg-gray-50 dark:hover:bg-gray-800"
            >
              Sign In
            </Button>
          </div>
        </motion.div>

        {/* Features Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 mb-20">
          {features.map((feature, index) => (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.3 + index * 0.1 }}
              whileHover={{ y: -5 }}
            >
              <Card className="h-full border-2 hover:border-primary-200 dark:hover:border-primary-800 hover:shadow-xl transition-all bg-white/80 dark:bg-gray-900/80 backdrop-blur-sm">
                <CardHeader>
                  <motion.div
                    whileHover={{ scale: 1.1, rotate: 5 }}
                    className="w-14 h-14 rounded-xl bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center mb-4 shadow-lg"
                  >
                    <feature.icon className="h-7 w-7 text-white" />
                  </motion.div>
                  <CardTitle className="text-xl mb-2">{feature.title}</CardTitle>
                  <CardDescription className="text-base">{feature.description}</CardDescription>
                </CardHeader>
              </Card>
            </motion.div>
          ))}
        </div>

        {/* Stats Section */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.7, duration: 0.5 }}
          className="grid grid-cols-2 md:grid-cols-4 gap-6 max-w-4xl mx-auto"
        >
          {stats.map((stat, index) => (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.8 + index * 0.1 }}
              className="text-center"
            >
              <div className="text-3xl md:text-4xl font-bold text-primary-600 dark:text-primary-400 mb-2">
                {stat.value}
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400">{stat.label}</div>
            </motion.div>
          ))}
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

const stats = [
  { value: '10K+', label: 'Active Users' },
  { value: '₹50Cr+', label: 'Assets Tracked' },
  { value: '99.9%', label: 'Uptime' },
  { value: '24/7', label: 'Support' },
]
