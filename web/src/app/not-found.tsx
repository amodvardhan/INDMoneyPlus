'use client'

import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Home } from 'lucide-react'
import { motion } from 'framer-motion'

export default function NotFound() {
  const router = useRouter()

  return (
    <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center px-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center max-w-md"
      >
        <h1 className="text-9xl font-extrabold text-primary-600 dark:text-primary-400 mb-4">
          404
        </h1>
        <h2 className="text-3xl font-bold mb-4 text-gray-900 dark:text-white">
          Page Not Found
        </h2>
        <p className="text-gray-600 dark:text-gray-400 mb-8">
          The page you're looking for doesn't exist or has been moved.
        </p>
        <Button
          onClick={() => router.push('/')}
          size="lg"
          className="shadow-lg"
        >
          <Home className="h-4 w-4 mr-2" />
          Go Home
        </Button>
      </motion.div>
    </div>
  )
}

