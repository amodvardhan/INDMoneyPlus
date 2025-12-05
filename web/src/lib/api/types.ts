// API Types - Generated from backend schemas

export interface User {
  id: number
  email: string
  is_active: boolean
  is_superuser: boolean
  created_at: string
  updated_at: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface RegisterRequest {
  email: string
  password: string
}

export interface LoginRequest {
  email: string
  password: string
}

export interface RefreshTokenRequest {
  refresh_token: string
}

export interface LogoutRequest {
  refresh_token: string
}

export interface ConsolidatedHolding {
  instrument_id: number | null
  isin: string | null
  ticker: string | null
  exchange: string | null
  total_qty: number
  avg_price: number | null
  total_valuation: number | null
  accounts: Array<{
    account_id: number
    broker_name: string
    qty: number
    avg_price: number | null
    valuation: number | null
  }>
}

export interface HoldingsResponse {
  user_id: number
  holdings: ConsolidatedHolding[]
  total_valuation: number | null
  last_updated: string
}

export interface PricePoint {
  id: number
  instrument_id: number
  timestamp: string
  open: number
  high: number
  low: number
  close: number
  volume: number | null
}

export interface PriceTimeseriesResponse {
  ticker: string
  exchange: string
  data: PricePoint[]
  count: number
}

export interface LatestPriceResponse {
  ticker: string
  exchange: string
  price: number
  timestamp: string
  open: number
  high: number
  low: number
  close: number
  volume: number | null
}

export interface AnalysisRequest {
  user_id: number
  portfolio_id: number
}

export interface AnalysisResponse {
  agent_run_id: number
  explanation: string
  metrics: Record<string, any>
  sources: string[]
  status: string
}

export interface RebalanceRequest {
  user_id: number
  portfolio_id: number
  target_alloc: Record<string, number>
}

export interface RebalanceResponse {
  agent_run_id: number
  proposal: Array<{
    instrument_id: number
    action: 'buy' | 'sell'
    quantity: number
    estimated_price: number
    estimated_cost: number
  }>
  total_estimated_cost: number
  total_estimated_tax?: number
  explanation: string
  sources: string[]
  status: string
}

export interface ExecutionPrepRequest {
  user_id: number
  agent_run_id: number
  human_confirmation: boolean
}

export interface ExecutionPrepResponse {
  agent_run_id: number
  order_envelopes: Array<{
    account_id: number
    orders: Array<{
      instrument_id: number
      action: 'buy' | 'sell'
      quantity: number
      order_type: string
    }>
  }>
  explanation: string
  requires_approval: boolean
  status: string
}

export interface AgentRun {
  id: number
  user_id: number
  flow_type: string
  status: string
  input_json: Record<string, any>
  output_json: Record<string, any> | null
  created_at: string
  updated_at: string
}

export interface AgentActionLog {
  id: number
  agent_run_id: number
  step: number
  action_type: string
  tool_name: string | null
  input_json: Record<string, any>
  output_json: Record<string, any> | null
  created_at: string
}

export interface Notification {
  id: number
  user_id: number
  type: string
  title: string
  message: string
  read: boolean
  created_at: string
}

export interface QueryRequest {
  user_id: number
  query: string
  context?: Record<string, any>
}

export interface SourceCitation {
  service: string
  endpoint: string
  timestamp: string
  data_point: string
}

export interface QueryResponse {
  agent_run_id: number
  answer: string
  query_type: string
  sources: SourceCitation[]
  suggested_actions: string[]
  status: string
}

export interface ApiError {
  detail: string
  status_code?: number
}

