'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { MessageCircle, Sparkles, X } from 'lucide-react'
import { ChatOverlay } from './chat-overlay'

export function ChatButton() {
  const [isOpen, setIsOpen] = useState(false)

  return (
    <>
      <AnimatePresence>
        {!isOpen && (
          <motion.div
            initial={{ scale: 0, rotate: -180 }}
            animate={{ scale: 1, rotate: 0 }}
            exit={{ scale: 0, rotate: 180 }}
            whileHover={{ scale: 1.1, rotate: 5 }}
            whileTap={{ scale: 0.95 }}
            className="fixed bottom-6 right-6 z-40"
          >
            <button
              onClick={() => setIsOpen(true)}
              className="relative group"
            >
              {/* Glow effect */}
              <div className="absolute inset-0 bg-gradient-to-r from-primary-500 to-primary-600 rounded-full blur-xl opacity-50 group-hover:opacity-75 transition-opacity animate-pulse" />

              {/* Main button */}
              <div className="relative bg-gradient-to-br from-primary-600 via-primary-500 to-primary-700 rounded-full p-4 shadow-2xl hover:shadow-primary-500/50 transition-all">
                <div className="relative flex items-center justify-center">
                  <MessageCircle className="h-6 w-6 text-white" />
                  <motion.div
                    animate={{
                      scale: [1, 1.2, 1],
                      opacity: [0.5, 1, 0.5]
                    }}
                    transition={{
                      duration: 2,
                      repeat: Infinity,
                      ease: "easeInOut"
                    }}
                    className="absolute inset-0 bg-white/20 rounded-full"
                  />
                </div>
              </div>

              {/* Notification badge */}
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 rounded-full border-2 border-white dark:border-gray-900 flex items-center justify-center"
              >
                <Sparkles className="h-2.5 w-2.5 text-white" />
              </motion.div>
            </button>
          </motion.div>
        )}
      </AnimatePresence>

      <ChatOverlay isOpen={isOpen} onClose={() => setIsOpen(false)} />
    </>
  )
}
