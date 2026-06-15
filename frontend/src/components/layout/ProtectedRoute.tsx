import { type ReactNode, useEffect } from 'react'
import { Navigate } from 'react-router-dom'
import { authApi } from '@/api/auth'
import { useAuthStore } from '@/stores/authStore'
import { useOrgStore } from '@/stores/orgStore'

export function ProtectedRoute({ children }: { children: ReactNode }) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  const organizations = useOrgStore((s) => s.organizations)
  const setOrganizations = useOrgStore((s) => s.setOrganizations)

  // Refresh the org list on mount if we're authenticated but have none cached
  useEffect(() => {
    if (isAuthenticated && organizations.length === 0) {
      authApi.listOrganizations().then(setOrganizations).catch(() => {})
    }
  }, [isAuthenticated, organizations.length, setOrganizations])

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }
  return <>{children}</>
}
