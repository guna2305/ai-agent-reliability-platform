import { AlertTriangle, Loader2, Sparkles } from 'lucide-react'
import { StatusBadge } from '@/components/ui/StatusBadge'
import { QueryBoundary } from '@/components/ui/QueryBoundary'
import { useFailureClusters, useFailures, useRunClustering } from '@/hooks/useApi'

export function FailuresPage() {
  const failures = useFailures()
  const clusters = useFailureClusters()
  const runClustering = useRunClustering()

  const items = failures.data?.items ?? []
  const clusterList = clusters.data ?? []

  return (
    <div className="p-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Failure Analysis</h1>
          <p className="text-gray-400 mt-1">Automatically clustered failures with root cause analysis</p>
        </div>
        <button
          className="btn-primary flex items-center gap-2"
          disabled={runClustering.isPending}
          onClick={() => runClustering.mutate(undefined)}
        >
          {runClustering.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
          Re-cluster (Ollama)
        </button>
      </div>

      {/* Cluster summary */}
      {clusterList.length > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {clusterList.map((c) => (
            <div key={c.cluster_id} className="card p-4 text-center">
              <p className="text-xs text-gray-500">Cluster {c.cluster_id}</p>
              <p className="text-2xl font-bold text-white mt-1">{c.size}</p>
              <p className="text-xs text-gray-600 mt-1">{c.dominant_type.replace('_', ' ')}</p>
            </div>
          ))}
        </div>
      )}

      {/* Failure list */}
      <div className="card p-0 overflow-hidden">
        <QueryBoundary
          isLoading={failures.isLoading}
          isError={failures.isError}
          isEmpty={items.length === 0}
          emptyMessage="No failures recorded yet."
        >
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-gray-500 border-b border-gray-800 bg-gray-900/50">
                <th className="px-6 py-3 font-medium">Title</th>
                <th className="px-6 py-3 font-medium">Type</th>
                <th className="px-6 py-3 font-medium">Severity</th>
                <th className="px-6 py-3 font-medium">Cluster</th>
                <th className="px-6 py-3 font-medium">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800">
              {items.map((f) => (
                <tr key={f.id} className="hover:bg-gray-800/40 transition-colors cursor-pointer">
                  <td className="px-6 py-3">
                    <div className="flex items-center gap-2">
                      <AlertTriangle
                        className={`w-3.5 h-3.5 flex-shrink-0 ${
                          f.severity === 'critical' ? 'text-red-400' : f.severity === 'high' ? 'text-orange-400' : 'text-yellow-400'
                        }`}
                      />
                      <span className="text-white text-xs font-medium">{f.title}</span>
                    </div>
                  </td>
                  <td className="px-6 py-3"><StatusBadge status={f.failure_type} /></td>
                  <td className="px-6 py-3"><StatusBadge status={f.severity} /></td>
                  <td className="px-6 py-3 text-gray-500 text-xs">{f.cluster_id != null ? `#${f.cluster_id}` : '—'}</td>
                  <td className="px-6 py-3">
                    <span className={`text-xs font-medium ${f.is_resolved ? 'text-green-400' : 'text-yellow-400'}`}>
                      {f.is_resolved ? 'Resolved' : 'Open'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </QueryBoundary>
      </div>
    </div>
  )
}
