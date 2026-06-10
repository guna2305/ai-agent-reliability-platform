import type { Agent, AgentVersion, PaginatedResponse } from '@/types/api'
import { apiClient } from './client'

export interface ListAgentsParams {
  org_slug: string
  status?: string
  limit?: number
  offset?: number
}

export const agentsApi = {
  list: async ({ org_slug, ...params }: ListAgentsParams): Promise<PaginatedResponse<Agent>> => {
    const { data } = await apiClient.get(`/organizations/${org_slug}/agents`, { params })
    return data
  },

  get: async (org_slug: string, agentId: string): Promise<Agent> => {
    const { data } = await apiClient.get(`/organizations/${org_slug}/agents/${agentId}`)
    return data
  },

  create: async (org_slug: string, payload: Partial<Agent>): Promise<Agent> => {
    const { data } = await apiClient.post(`/organizations/${org_slug}/agents`, payload)
    return data
  },

  updateStatus: async (org_slug: string, agentId: string, status: string): Promise<Agent> => {
    const { data } = await apiClient.patch(
      `/organizations/${org_slug}/agents/${agentId}/status`,
      { status },
    )
    return data
  },

  listVersions: async (org_slug: string, agentId: string): Promise<AgentVersion[]> => {
    const { data } = await apiClient.get(
      `/organizations/${org_slug}/agents/${agentId}/versions`,
    )
    return data
  },
}
