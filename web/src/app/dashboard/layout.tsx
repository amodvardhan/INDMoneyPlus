'use client'

import { ChatButton } from '@/components/ai-assistant/chat-button'

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <>
      {children}
      <ChatButton />
    </>
  )
}

