import type { Execution, ExecutionTrace, PaginatedResponse } from '@/types/api'
import { apiClient } from './client'

export const executionsApi = {
  list: async (params: {
    org_slug: string
    agent_id?: string
    status?: string
    limit?: number
    offset?: number
  }): Promise<PaginatedResponse<Execution>> => {
    const { org_slug, ...rest } = params
    const { data } = await apiClient.get(`/organizations/${org_slug}/executions`, { params: rest })
    return data
  },

  get: async (executionId: string): Promise<Execution> => {
    const { data } = await apiClient.get(`/executions/${executionId}`)
    return data
  },

  getTraces: async (executionId: string): Promise<ExecutionTrace[]> => {
    const { data } = await apiClient.get(`/executions/${executionId}/traces`)
    return data
  },

  start: async (payload: {
    org_id: string
    agent_id: string
    input: Record<string, unknown>
    agent_version_id?: string
    tags?: string[]
  }): Promise<Execution> => {
    const { data } = await apiClient.post('/executions', payload)
    return data
  },
}
