import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { Organization } from '@/types/api'

interface OrgState {
  currentOrg: Organization | null
  organizations: Organization[]
  setCurrentOrg: (org: Organization | null) => void
  setOrganizations: (orgs: Organization[]) => void
}

export const useOrgStore = create<OrgState>()(
  persist(
    (set) => ({
      currentOrg: null,
      organizations: [],
      setCurrentOrg: (org) => set({ currentOrg: org }),
      setOrganizations: (orgs) =>
        set((state) => ({
          organizations: orgs,
          // Auto-select the first org if none chosen yet
          currentOrg: state.currentOrg ?? orgs[0] ?? null,
        })),
    }),
    { name: 'org-store' },
  ),
)
