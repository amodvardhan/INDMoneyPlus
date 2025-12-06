'use client'

import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, Send, Bot, User, Sparkles, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useAnalyzePortfolio, useQueryAssistant } from '@/hooks/useAgent'
import { useAuth } from '@/hooks/useAuth'
import { toast } from 'sonner'
import { cn } from '@/lib/utils'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

interface ChatOverlayProps {
  isOpen: boolean
  onClose: () => void
}

export function ChatOverlay({ isOpen, onClose }: ChatOverlayProps) {
  const { user } = useAuth()
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: 'Hello! 👋 I\'m your AI portfolio assistant. I can help you with:\n\n• Portfolio analysis and insights\n• Stock market questions and education\n• IPOs and NFOs explanations\n• Rebalancing strategies\n• Investment concepts and terminology\n• Market trends and analysis\n\nAsk me anything about investing, your portfolio, or the stock market!',
      timestamp: new Date(),
    },
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const analyzeMutation = useAnalyzePortfolio()
  const queryMutation = useQueryAssistant()

  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [messages])

  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus()
    }
  }, [isOpen])

  const handleSend = async () => {
    if (!input.trim() || !user || isLoading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    const currentInput = input
    setInput('')
    setIsLoading(true)

      try {
      // Check if user wants portfolio analysis (use dedicated endpoint)
      if (
        currentInput.toLowerCase().includes('analyze') &&
        (currentInput.toLowerCase().includes('portfolio') || currentInput.toLowerCase().includes('my portfolio'))
      ) {
        const result = await analyzeMutation.mutateAsync({
          user_id: user.id,
          portfolio_id: 1, // Mock portfolio ID
        })

        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: `✅ Analysis complete!\n\n${result.explanation}\n\n📊 Key Metrics:\n${Object.entries(result.metrics)
            .map(([key, value]) => `• ${key}: ${value}`)
            .join('\n')}\n\n📚 Sources: ${result.sources.join(', ')}`,
          timestamp: new Date(),
        }

        setMessages((prev) => [...prev, assistantMessage])
      } else {
        // Use the general query endpoint for all other queries
        const result = await queryMutation.mutateAsync({
          user_id: user.id,
          query: currentInput,
        })

        let content = result.answer

        // Add suggested actions if available
        if (result.suggested_actions && result.suggested_actions.length > 0) {
          content += `\n\n💡 Suggested Actions:\n${result.suggested_actions.map((action) => `• ${action}`).join('\n')}`
        }

        // Add sources if available
        if (result.sources && result.sources.length > 0) {
          content += `\n\n📚 Sources: ${result.sources.map((s) => s.service).join(', ')}`
        }

        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content,
          timestamp: new Date(),
        }

        setMessages((prev) => [...prev, assistantMessage])
      }
    } catch (error: any) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `❌ I apologize, but I encountered an error: ${error.response?.data?.detail || error.message || 'Unknown error'}. Please try again later.`,
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  if (!isOpen) return null

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={onClose}
        className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm pointer-events-auto"
      />
      <motion.div
        initial={{ opacity: 0, scale: 0.9, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.9, y: 20 }}
        transition={{ type: 'spring', damping: 25, stiffness: 300 }}
        onClick={(e) => e.stopPropagation()}
        className="fixed bottom-6 right-6 z-50 w-full max-w-md h-[700px] pointer-events-auto"
      >
        <div className="flex flex-col h-full bg-white dark:bg-gray-900 rounded-2xl shadow-2xl border-2 border-gray-200 dark:border-gray-800 overflow-hidden">
          {/* Header */}
          <div className="flex items-center justify-between p-5 border-b border-gray-200 dark:border-gray-800 bg-gradient-to-r from-primary-50 to-primary-100/50 dark:from-primary-950/50 dark:to-primary-900/30">
            <div className="flex items-center gap-3">
              <div className="relative">
                <div className="absolute inset-0 bg-primary-500 rounded-full blur-md opacity-50" />
                <div className="relative bg-gradient-to-br from-primary-600 to-primary-700 p-2.5 rounded-full shadow-lg">
                  <Sparkles className="h-5 w-5 text-white" />
                </div>
              </div>
              <div>
                <h3 className="font-bold text-lg text-gray-900 dark:text-white">AI Assistant</h3>
                <p className="text-xs text-gray-500 dark:text-gray-400">Portfolio insights & analysis</p>
              </div>
            </div>
            <Button
              variant="ghost"
              size="icon"
              onClick={onClose}
              className="hover:bg-gray-200 dark:hover:bg-gray-800 rounded-full"
            >
              <X className="h-5 w-5" />
            </Button>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-5 space-y-4 bg-gradient-to-b from-white to-gray-50/50 dark:from-gray-900 dark:to-gray-950/50">
            {messages.map((message, index) => (
              <motion.div
                key={message.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className={cn(
                  'flex gap-3',
                  message.role === 'user' ? 'justify-end' : 'justify-start'
                )}
              >
                {message.role === 'assistant' && (
                  <div className="flex-shrink-0">
                    <div className="w-9 h-9 rounded-full bg-gradient-to-br from-primary-500 to-primary-600 flex items-center justify-center shadow-md">
                      <Bot className="h-5 w-5 text-white" />
                    </div>
                  </div>
                )}
                <div
                  className={cn(
                    'max-w-[80%] rounded-2xl px-4 py-3 shadow-sm',
                    message.role === 'user'
                      ? 'bg-gradient-to-br from-primary-600 to-primary-700 text-white rounded-br-sm'
                      : 'bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 border border-gray-200 dark:border-gray-700 rounded-bl-sm'
                  )}
                >
                  <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
                  <p className={cn(
                    'text-xs mt-2',
                    message.role === 'user' ? 'text-primary-100' : 'text-gray-400'
                  )}>
                    {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </p>
                </div>
                {message.role === 'user' && (
                  <div className="flex-shrink-0">
                    <div className="w-9 h-9 rounded-full bg-gradient-to-br from-gray-400 to-gray-500 flex items-center justify-center shadow-md">
                      <User className="h-5 w-5 text-white" />
                    </div>
                  </div>
                )}
              </motion.div>
            ))}
            {isLoading && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex gap-3"
              >
                <div className="flex-shrink-0">
                  <div className="w-9 h-9 rounded-full bg-gradient-to-br from-primary-500 to-primary-600 flex items-center justify-center shadow-md">
                    <Bot className="h-5 w-5 text-white" />
                  </div>
                </div>
                <div className="bg-white dark:bg-gray-800 rounded-2xl rounded-bl-sm px-4 py-3 shadow-sm border border-gray-200 dark:border-gray-700">
                  <div className="flex gap-1.5">
                    <motion.div
                      className="w-2 h-2 bg-primary-500 rounded-full"
                      animate={{ y: [0, -8, 0] }}
                      transition={{ duration: 0.6, repeat: Infinity, delay: 0 }}
                    />
                    <motion.div
                      className="w-2 h-2 bg-primary-500 rounded-full"
                      animate={{ y: [0, -8, 0] }}
                      transition={{ duration: 0.6, repeat: Infinity, delay: 0.2 }}
                    />
                    <motion.div
                      className="w-2 h-2 bg-primary-500 rounded-full"
                      animate={{ y: [0, -8, 0] }}
                      transition={{ duration: 0.6, repeat: Infinity, delay: 0.4 }}
                    />
                  </div>
                </div>
              </motion.div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div className="p-4 border-t border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900">
            <div className="flex gap-2">
              <Input
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault()
                    handleSend()
                  }
                }}
                placeholder="Ask me anything about stocks, portfolio, IPOs, NFOs, or investing..."
                disabled={isLoading}
                className="flex-1 h-12 border-2 focus:border-primary-500 rounded-xl"
              />
              <Button
                onClick={handleSend}
                disabled={isLoading || !input.trim()}
                className="h-12 px-4 rounded-xl shadow-md hover:shadow-lg transition-all"
                size="lg"
              >
                {isLoading ? (
                  <Loader2 className="h-5 w-5 animate-spin" />
                ) : (
                  <Send className="h-5 w-5" />
                )}
              </Button>
            </div>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-2 text-center">
              Try: "What is an IPO?", "Explain rebalancing", "Tell me about my portfolio", or "What are NFOs?"
            </p>
          </div>
        </div>
      </motion.div>
    </AnimatePresence>
  )
}
