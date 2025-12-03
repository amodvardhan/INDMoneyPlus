import { apiClient } from './api/client'
import type { User, LoginRequest, RegisterRequest } from './api/types'

export interface AuthState {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
}

class AuthService {
  private user: User | null = null
  private listeners: Set<(state: AuthState) => void> = new Set()
  private initialized = false

  constructor() {
    // Don't restore session in constructor to avoid hydration issues
    // Session will be restored in useAuth hook after mount
  }

  subscribe(listener: (state: AuthState) => void) {
    this.listeners.add(listener)
    return () => {
      this.listeners.delete(listener)
    }
  }

  private notify() {
    const state = this.getState()
    this.listeners.forEach((listener) => listener(state))
  }

  getState(): AuthState {
    return {
      user: this.user,
      isAuthenticated: !!this.user,
      isLoading: false,
    }
  }

  async restoreSession() {
    if (this.initialized) {
      return // Already initialized
    }
    this.initialized = true
    
    try {
      if (typeof window === 'undefined') {
        return // Skip on server
      }
      const token = localStorage.getItem('access_token')
      if (token) {
        this.user = await apiClient.getCurrentUser()
        this.notify()
      } else {
        // No token, notify with initial state
        this.notify()
      }
    } catch (error) {
      // Session invalid, clear tokens
      this.user = null
      if (typeof window !== 'undefined') {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
      }
      this.notify()
    }
  }

  async login(credentials: LoginRequest) {
    try {
      await apiClient.login(credentials)
      this.user = await apiClient.getCurrentUser()
      this.notify()
      return { success: true }
    } catch (error: any) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Login failed',
      }
    }
  }

  async register(data: RegisterRequest) {
    try {
      await apiClient.register(data)
      // Auto-login after registration
      return await this.login({ email: data.email, password: data.password })
    } catch (error: any) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Registration failed',
      }
    }
  }

  async logout() {
    try {
      const refreshToken = localStorage.getItem('refresh_token')
      if (refreshToken) {
        await apiClient.logout({ refresh_token: refreshToken })
      }
    } catch (error) {
      // Ignore logout errors
    } finally {
      this.user = null
      if (typeof window !== 'undefined') {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
      }
      this.notify()
    }
  }

  getCurrentUser(): User | null {
    return this.user
  }

  isAuthenticated(): boolean {
    return !!this.user
  }
}

export const authService = new AuthService()

