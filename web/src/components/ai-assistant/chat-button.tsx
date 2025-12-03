'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { Bot } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { ChatOverlay } from './chat-overlay'

export function ChatButton() {
  const [isOpen, setIsOpen] = useState(false)

  return (
    <>
      <motion.div
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.9 }}
        className="fixed bottom-6 right-6 z-40"
      >
        <Button
          size="lg"
          className="rounded-full h-14 w-14 shadow-lg"
          onClick={() => setIsOpen(true)}
        >
          <Bot className="h-6 w-6" />
        </Button>
      </motion.div>
      <ChatOverlay isOpen={isOpen} onClose={() => setIsOpen(false)} />
    </>
  )
}

