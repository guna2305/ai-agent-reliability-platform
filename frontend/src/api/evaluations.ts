import type { EvaluationRun, EvaluationResult, PaginatedResponse } from '@/types/api'
import { apiClient } from './client'

export const evaluationsApi = {
  listRuns: async (orgSlug: string, params?: { agent_id?: string; limit?: number; offset?: number }): Promise<PaginatedResponse<EvaluationRun>> => {
    const { data } = await apiClient.get(`/organizations/${orgSlug}/evaluations/runs`, { params })
    return data
  },

  getRun: async (orgSlug: string, runId: string): Promise<EvaluationRun> => {
    const { data } = await apiClient.get(`/organizations/${orgSlug}/evaluations/runs/${runId}`)
    return data
  },

  getResults: async (orgSlug: string, runId: string, params?: { passed?: boolean; limit?: number; offset?: number }): Promise<PaginatedResponse<EvaluationResult>> => {
    const { data } = await apiClient.get(`/organizations/${orgSlug}/evaluations/runs/${runId}/results`, { params })
    return data
  },

  createRun: async (orgSlug: string, payload: {
    agent_id: string
    name: string
    eval_type: string
    dataset_id?: string
    config?: Record<string, unknown>
  }): Promise<EvaluationRun> => {
    const { data } = await apiClient.post(`/organizations/${orgSlug}/evaluations/runs`, payload)
    return data
  },
}
