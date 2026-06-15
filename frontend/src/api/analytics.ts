import { apiClient } from './client'

export interface ExecutionStats {
  total: number
  succeeded: number
  failed: number
  success_rate: number
  avg_duration_ms: number
  total_tokens: number
  total_cost_usd: number
}

export interface CostByModel {
  provider: string
  model: string
  cost_usd: number
  tokens: number
  executions: number
}

export interface DailyCost {
  date: string
  cost_usd: number
  tokens: number
  executions: number
  succeeded: number
  failed: number
}

export interface CostSummary {
  total_cost_usd: number
  total_tokens: number
  total_executions: number
  avg_cost_per_execution: number
  by_model: CostByModel[]
  daily: DailyCost[]
  period_days: number
}

export const analyticsApi = {
  executionStats: async (orgSlug: string, days = 30, agentId?: string): Promise<ExecutionStats> => {
    const { data } = await apiClient.get(`/organizations/${orgSlug}/analytics/executions`, {
      params: { days, agent_id: agentId },
    })
    return data
  },

  costSummary: async (orgSlug: string, days = 30): Promise<CostSummary> => {
    const { data } = await apiClient.get(`/organizations/${orgSlug}/analytics/costs`, {
      params: { days },
    })
    return data
  },
}
