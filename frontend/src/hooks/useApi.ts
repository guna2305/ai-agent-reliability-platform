import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { agentsApi } from '@/api/agents'
import { analyticsApi } from '@/api/analytics'
import { evaluationsApi } from '@/api/evaluations'
import { executionsApi } from '@/api/executions'
import { failuresApi } from '@/api/failures'
import { useOrgStore } from '@/stores/orgStore'

/** The current org slug, or '' when none selected (queries stay disabled). */
function useOrgSlug(): string {
  return useOrgStore((s) => s.currentOrg?.slug ?? '')
}

// ─── Agents ─────────────────────────────────────────────────────────────────

export function useAgents(status?: string) {
  const slug = useOrgSlug()
  return useQuery({
    queryKey: ['agents', slug, status],
    queryFn: () => agentsApi.list({ org_slug: slug, status }),
    enabled: !!slug,
  })
}

// ─── Executions ──────────────────────────────────────────────────────────────

export function useExecutions(filters?: { agent_id?: string; status?: string }) {
  const slug = useOrgSlug()
  return useQuery({
    queryKey: ['executions', slug, filters],
    queryFn: () => executionsApi.list({ org_slug: slug, ...filters }),
    enabled: !!slug,
  })
}

export function useExecutionTraces(executionId: string | undefined) {
  return useQuery({
    queryKey: ['traces', executionId],
    queryFn: () => executionsApi.getTraces(executionId!),
    enabled: !!executionId,
  })
}

// ─── Analytics ───────────────────────────────────────────────────────────────

export function useExecutionStats(days = 30) {
  const slug = useOrgSlug()
  return useQuery({
    queryKey: ['exec-stats', slug, days],
    queryFn: () => analyticsApi.executionStats(slug, days),
    enabled: !!slug,
  })
}

export function useCostSummary(days = 30) {
  const slug = useOrgSlug()
  return useQuery({
    queryKey: ['cost-summary', slug, days],
    queryFn: () => analyticsApi.costSummary(slug, days),
    enabled: !!slug,
  })
}

// ─── Evaluations ─────────────────────────────────────────────────────────────

export function useEvaluationRuns() {
  const slug = useOrgSlug()
  return useQuery({
    queryKey: ['eval-runs', slug],
    queryFn: () => evaluationsApi.listRuns(slug),
    enabled: !!slug,
  })
}

// ─── Failures ────────────────────────────────────────────────────────────────

export function useFailures(filters?: { failure_type?: string; cluster_id?: number; is_resolved?: boolean }) {
  const slug = useOrgSlug()
  return useQuery({
    queryKey: ['failures', slug, filters],
    queryFn: () => failuresApi.list(slug, filters),
    enabled: !!slug,
  })
}

export function useFailureBreakdown() {
  const slug = useOrgSlug()
  return useQuery({
    queryKey: ['failure-breakdown', slug],
    queryFn: () => failuresApi.breakdown(slug),
    enabled: !!slug,
  })
}

export function useFailureClusters() {
  const slug = useOrgSlug()
  return useQuery({
    queryKey: ['failure-clusters', slug],
    queryFn: () => failuresApi.clusters(slug),
    enabled: !!slug,
  })
}

export function useRunClustering() {
  const slug = useOrgSlug()
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (k?: number) => failuresApi.runClustering(slug, k),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['failures', slug] })
      qc.invalidateQueries({ queryKey: ['failure-clusters', slug] })
    },
  })
}
