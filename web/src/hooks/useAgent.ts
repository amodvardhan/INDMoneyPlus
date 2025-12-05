import { useMutation, useQuery } from '@tanstack/react-query'
import { apiClient } from '@/lib/api/client'
import type {
  AnalysisRequest,
  AnalysisResponse,
  RebalanceRequest,
  RebalanceResponse,
  ExecutionPrepRequest,
  ExecutionPrepResponse,
  QueryRequest,
  QueryResponse,
  AgentRun,
  AgentActionLog,
} from '@/lib/api/types'

export function useAnalyzePortfolio() {
  return useMutation({
    mutationFn: (data: AnalysisRequest) => apiClient.analyzePortfolio(data),
  })
}

export function useRebalancePortfolio() {
  return useMutation({
    mutationFn: (data: RebalanceRequest) => apiClient.rebalancePortfolio(data),
  })
}

export function usePrepareExecution() {
  return useMutation({
    mutationFn: (data: ExecutionPrepRequest) => apiClient.prepareExecution(data),
  })
}

export function useAgentRun(agentRunId: number | null) {
  return useQuery({
    queryKey: ['agent-run', agentRunId],
    queryFn: () => apiClient.getAgentRun(agentRunId!),
    enabled: !!agentRunId,
  })
}

export function useAgentLogs(agentRunId: number | null) {
  return useQuery({
    queryKey: ['agent-logs', agentRunId],
    queryFn: () => apiClient.getAgentLogs(agentRunId!),
    enabled: !!agentRunId,
    refetchInterval: 2000, // Poll for logs every 2 seconds
  })
}

export function useQueryAssistant() {
  return useMutation({
    mutationFn: (data: QueryRequest) => apiClient.queryAssistant(data),
  })
}

