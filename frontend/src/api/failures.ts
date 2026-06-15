import type { FailureReport, PaginatedResponse } from '@/types/api'
import { apiClient } from './client'

export interface TypeBreakdown {
  failure_type: string
  count: number
}

export interface ClusterSummary {
  cluster_id: number
  size: number
  dominant_type: string
}

export const failuresApi = {
  list: async (orgSlug: string, params?: {
    failure_type?: string
    cluster_id?: number
    is_resolved?: boolean
    limit?: number
    offset?: number
  }): Promise<PaginatedResponse<FailureReport>> => {
    const { data } = await apiClient.get(`/organizations/${orgSlug}/failures`, { params })
    return data
  },

  breakdown: async (orgSlug: string): Promise<TypeBreakdown[]> => {
    const { data } = await apiClient.get(`/organizations/${orgSlug}/failures/breakdown`)
    return data
  },

  clusters: async (orgSlug: string): Promise<ClusterSummary[]> => {
    const { data } = await apiClient.get(`/organizations/${orgSlug}/failures/clusters`)
    return data
  },

  runClustering: async (orgSlug: string, k?: number): Promise<{ clustered: number; newly_embedded: number; k: number }> => {
    const { data } = await apiClient.post(`/organizations/${orgSlug}/failures/cluster`, null, { params: { k } })
    return data
  },

  resolve: async (orgSlug: string, reportId: string, notes: string): Promise<FailureReport> => {
    const { data } = await apiClient.post(`/organizations/${orgSlug}/failures/${reportId}/resolve`, { notes })
    return data
  },
}
