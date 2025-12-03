import axios, { AxiosInstance, AxiosError } from 'axios'
import type {
  User,
  TokenResponse,
  RegisterRequest,
  LoginRequest,
  RefreshTokenRequest,
  LogoutRequest,
  HoldingsResponse,
  PriceTimeseriesResponse,
  LatestPriceResponse,
  AnalysisRequest,
  AnalysisResponse,
  RebalanceRequest,
  RebalanceResponse,
  ExecutionPrepRequest,
  ExecutionPrepResponse,
  AgentRun,
  AgentActionLog,
  Notification,
  ApiError,
} from './types'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

class ApiClient {
  private client: AxiosInstance

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    // Request interceptor to add auth token
    this.client.interceptors.request.use(
      (config) => {
        if (typeof window !== 'undefined') {
          const token = localStorage.getItem('access_token')
          if (token) {
            config.headers.Authorization = `Bearer ${token}`
          }
        }
        return config
      },
      (error) => Promise.reject(error)
    )

    // Response interceptor for token refresh
    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError<ApiError>) => {
        const originalRequest = error.config as any

        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true

          try {
            const refreshToken = localStorage.getItem('refresh_token')
            if (refreshToken) {
              const response = await axios.post<TokenResponse>(
                `${API_BASE_URL}/api/v1/auth/refresh`,
                { refresh_token: refreshToken }
              )

              const { access_token, refresh_token: newRefreshToken } = response.data
              localStorage.setItem('access_token', access_token)
              localStorage.setItem('refresh_token', newRefreshToken)

              originalRequest.headers.Authorization = `Bearer ${access_token}`
              return this.client(originalRequest)
            }
          } catch (refreshError) {
            // Refresh failed, clear tokens and redirect to login
            if (typeof window !== 'undefined') {
              localStorage.removeItem('access_token')
              localStorage.removeItem('refresh_token')
              window.location.href = '/login'
            }
            return Promise.reject(refreshError)
          }
        }

        return Promise.reject(error)
      }
    )
  }

  // Auth endpoints
  async register(data: RegisterRequest): Promise<User> {
    const response = await this.client.post<User>('/api/v1/auth/register', data)
    return response.data
  }

  async login(data: LoginRequest): Promise<TokenResponse> {
    const response = await this.client.post<TokenResponse>('/api/v1/auth/login', data)
    if (typeof window !== 'undefined') {
      localStorage.setItem('access_token', response.data.access_token)
      localStorage.setItem('refresh_token', response.data.refresh_token)
    }
    return response.data
  }

  async refresh(data: RefreshTokenRequest): Promise<TokenResponse> {
    const response = await this.client.post<TokenResponse>('/api/v1/auth/refresh', data)
    if (typeof window !== 'undefined') {
      localStorage.setItem('access_token', response.data.access_token)
      localStorage.setItem('refresh_token', response.data.refresh_token)
    }
    return response.data
  }

  async logout(data: LogoutRequest): Promise<void> {
    await this.client.post('/api/v1/auth/logout', data)
    if (typeof window !== 'undefined') {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
    }
  }

  async getCurrentUser(): Promise<User> {
    const response = await this.client.get<User>('/api/v1/auth/me')
    return response.data
  }

  // Holdings endpoints
  async getHoldings(userId: number): Promise<HoldingsResponse> {
    const response = await this.client.get<HoldingsResponse>(`/api/v1/aggregator/holdings/${userId}`)
    return response.data
  }

  // Market data endpoints
  async getPriceTimeseries(
    ticker: string,
    exchange: string,
    fromDate: string,
    toDate: string
  ): Promise<PriceTimeseriesResponse> {
    const response = await this.client.get<PriceTimeseriesResponse>(
      `/api/v1/marketdata/prices/${ticker}`,
      {
        params: {
          exchange,
          from: fromDate,
          to: toDate,
        },
      }
    )
    return response.data
  }

  async getLatestPrice(ticker: string, exchange: string): Promise<LatestPriceResponse> {
    const response = await this.client.get<LatestPriceResponse>(
      `/api/v1/marketdata/price/${ticker}/latest`,
      {
        params: { exchange },
      }
    )
    return response.data
  }

  // Agent endpoints
  async analyzePortfolio(data: AnalysisRequest): Promise<AnalysisResponse> {
    const response = await this.client.post<AnalysisResponse>(
      '/api/v1/agents/analyze',
      data
    )
    return response.data
  }

  async rebalancePortfolio(data: RebalanceRequest): Promise<RebalanceResponse> {
    const response = await this.client.post<RebalanceResponse>(
      '/api/v1/agents/rebalance',
      data
    )
    return response.data
  }

  async prepareExecution(data: ExecutionPrepRequest): Promise<ExecutionPrepResponse> {
    const response = await this.client.post<ExecutionPrepResponse>(
      '/api/v1/agents/prepare_execution',
      data
    )
    return response.data
  }

  async getAgentRun(agentRunId: number): Promise<AgentRun> {
    const response = await this.client.get<AgentRun>(`/api/v1/agents/${agentRunId}`)
    return response.data
  }

  async getAgentLogs(agentRunId: number): Promise<AgentActionLog[]> {
    const response = await this.client.get<AgentActionLog[]>(
      `/api/v1/agents/${agentRunId}/logs`
    )
    return response.data
  }

  // Notification endpoints (mock for now)
  async getNotifications(userId: number): Promise<Notification[]> {
    const response = await this.client.get<Notification[]>(
      `/api/v1/notifications/${userId}`
    )
    return response.data
  }
}

export const apiClient = new ApiClient()

