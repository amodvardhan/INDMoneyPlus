'use client'

import { Navbar } from './navbar'
import { ChatButton } from '@/components/ai-assistant/chat-button'
import { ReactNode } from 'react'

interface AppLayoutProps {
  children: ReactNode
}

export function AppLayout({ children }: AppLayoutProps) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-gray-50 dark:from-gray-950 dark:via-gray-900 dark:to-gray-950">
      <Navbar />
      <main className="pb-8 min-h-[calc(100vh-4rem)]">{children}</main>
      <ChatButton />
    </div>
  )
}

