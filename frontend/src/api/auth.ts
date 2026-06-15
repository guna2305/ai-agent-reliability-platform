import type { AuthTokens, CurrentUser, Organization } from '@/types/api'
import { apiClient } from './client'

export const authApi = {
  register: async (payload: {
    email: string
    password: string
    full_name: string
    org_name?: string
  }): Promise<AuthTokens> => {
    const { data } = await apiClient.post('/auth/register', payload)
    return data
  },

  login: async (email: string, password: string): Promise<AuthTokens> => {
    const { data } = await apiClient.post('/auth/login', { email, password })
    return data
  },

  logout: async (refresh_token: string | null): Promise<void> => {
    await apiClient.post('/auth/logout', { refresh_token })
  },

  me: async (): Promise<CurrentUser> => {
    const { data } = await apiClient.get('/auth/me')
    return data
  },

  listOrganizations: async (): Promise<Organization[]> => {
    const { data } = await apiClient.get('/organizations')
    return data
  },
}
