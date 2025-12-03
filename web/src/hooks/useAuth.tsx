'use client'

import { useState, useEffect, useCallback } from 'react'
import { authService, type AuthState } from '@/lib/auth'
import type { LoginRequest, RegisterRequest } from '@/lib/api/types'

// Initial state that's consistent between server and client
const initialAuthState: AuthState = {
  user: null,
  isAuthenticated: false,
  isLoading: true, // Start with loading=true to prevent hydration mismatch
}

export function useAuth() {
  const [state, setState] = useState<AuthState>(initialAuthState)
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
    // Restore session and update state after mount
    authService.restoreSession().then(() => {
      setState(authService.getState())
    })
    
    const unsubscribe = authService.subscribe(setState)
    return unsubscribe
  }, [])

  const login = useCallback(async (credentials: LoginRequest) => {
    return await authService.login(credentials)
  }, [])

  const register = useCallback(async (data: RegisterRequest) => {
    return await authService.register(data)
  }, [])

  const logout = useCallback(async () => {
    await authService.logout()
  }, [])

  return {
    ...state,
    login,
    register,
    logout,
  }
}

