import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ChevronRight } from 'lucide-react'
import { StatusBadge } from '@/components/ui/StatusBadge'
import { QueryBoundary } from '@/components/ui/QueryBoundary'
import { useExecutions } from '@/hooks/useApi'

const STATUS_FILTERS = ['all', 'running', 'succeeded', 'failed', 'timed_out']

export function ExecutionsPage() {
  const navigate = useNavigate()
  const [statusFilter, setStatusFilter] = useState<string>('all')

  const { data, isLoading, isError } = useExecutions(
    statusFilter === 'all' ? undefined : { status: statusFilter },
  )
  const items = data?.items ?? []

  const fmt = (ms: number | null) => (ms != null ? `${(ms / 1000).toFixed(2)}s` : null)

  return (
    <div className="p-8 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Executions</h1>
        <p className="text-gray-400 mt-1">Track every agent run with full observability</p>
      </div>

      <div className="flex gap-2">
        {STATUS_FILTERS.map((s) => (
          <button
            key={s}
            onClick={() => setStatusFilter(s)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
              statusFilter === s ? 'bg-brand-600 text-white' : 'bg-gray-800 text-gray-400 hover:text-white'
            }`}
          >
            {s.replace('_', ' ')}
          </button>
        ))}
      </div>

      <div className="card p-0 overflow-hidden">
        <QueryBoundary
          isLoading={isLoading}
          isError={isError}
          isEmpty={items.length === 0}
          emptyMessage="No executions match this filter."
        >
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-gray-500 border-b border-gray-800 bg-gray-900/50">
                <th className="px-6 py-3 font-medium">ID</th>
                <th className="px-6 py-3 font-medium">Agent</th>
                <th className="px-6 py-3 font-medium">Status</th>
                <th className="px-6 py-3 font-medium">Duration</th>
                <th className="px-6 py-3 font-medium">Tokens</th>
                <th className="px-6 py-3 font-medium">Cost</th>
                <th className="px-6 py-3 font-medium">Model</th>
                <th className="px-6 py-3 font-medium"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800">
              {items.map((exec) => (
                <tr
                  key={exec.id}
                  className="hover:bg-gray-800/40 transition-colors cursor-pointer"
                  onClick={() => navigate(`/traces/${exec.id}`)}
                >
                  <td className="px-6 py-3 font-mono text-xs text-gray-500">{exec.id.slice(0, 8)}</td>
                  <td className="px-6 py-3 text-white font-mono text-xs">{exec.agent_id.slice(0, 8)}</td>
                  <td className="px-6 py-3"><StatusBadge status={exec.status} /></td>
                  <td className="px-6 py-3 text-gray-400 font-mono">
                    {fmt(exec.duration_ms) ?? <span className="text-blue-400 animate-pulse">running…</span>}
                  </td>
                  <td className="px-6 py-3 text-gray-400">{exec.total_tokens?.toLocaleString() ?? '—'}</td>
                  <td className="px-6 py-3 text-gray-400 font-mono">{exec.total_cost_usd ? `$${exec.total_cost_usd}` : '—'}</td>
                  <td className="px-6 py-3 text-gray-500 text-xs">{exec.model_name ?? '—'}</td>
                  <td className="px-6 py-3"><ChevronRight className="w-4 h-4 text-gray-600" /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </QueryBoundary>
      </div>
    </div>
  )
}
