import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ChevronRight } from 'lucide-react'
import { StatusBadge } from '@/components/ui/StatusBadge'
import type { ExecutionStatus } from '@/types/api'

const MOCK_EXECUTIONS = [
  { id: 'exec-001', agent: 'Customer Support', status: 'succeeded' as ExecutionStatus, duration_ms: 1240, tokens: 1820, cost: '$0.0042', model: 'gpt-4o', started_at: '2026-06-10T14:32:00Z' },
  { id: 'exec-002', agent: 'SQL Agent',        status: 'failed'    as ExecutionStatus, duration_ms: 320,  tokens: 450,  cost: '$0.0008', model: 'gpt-4o', started_at: '2026-06-10T14:31:00Z' },
  { id: 'exec-003', agent: 'Research Agent',   status: 'running'   as ExecutionStatus, duration_ms: null, tokens: null, cost: null,      model: 'claude-3-5-sonnet', started_at: '2026-06-10T14:30:00Z' },
  { id: 'exec-004', agent: 'Coding Agent',     status: 'succeeded' as ExecutionStatus, duration_ms: 8900, tokens: 6200, cost: '$0.0231', model: 'gpt-4o', started_at: '2026-06-10T14:28:00Z' },
  { id: 'exec-005', agent: 'Customer Support', status: 'timed_out' as ExecutionStatus, duration_ms: 30000, tokens: 500, cost: '$0.0009', model: 'gpt-4o', started_at: '2026-06-10T14:25:00Z' },
]

export function ExecutionsPage() {
  const navigate = useNavigate()
  const [statusFilter, setStatusFilter] = useState<string>('all')

  const filtered = statusFilter === 'all'
    ? MOCK_EXECUTIONS
    : MOCK_EXECUTIONS.filter(e => e.status === statusFilter)

  return (
    <div className="p-8 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Executions</h1>
        <p className="text-gray-400 mt-1">Track every agent run with full observability</p>
      </div>

      {/* Filters */}
      <div className="flex gap-2">
        {['all', 'running', 'succeeded', 'failed', 'timed_out'].map(s => (
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

      {/* Table */}
      <div className="card p-0 overflow-hidden">
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
            {filtered.map((exec) => (
              <tr
                key={exec.id}
                className="hover:bg-gray-800/40 transition-colors cursor-pointer"
                onClick={() => navigate(`/traces/${exec.id}`)}
              >
                <td className="px-6 py-3 font-mono text-xs text-gray-500">{exec.id}</td>
                <td className="px-6 py-3 text-white font-medium">{exec.agent}</td>
                <td className="px-6 py-3"><StatusBadge status={exec.status} /></td>
                <td className="px-6 py-3 text-gray-400 font-mono">
                  {exec.duration_ms ? `${(exec.duration_ms / 1000).toFixed(2)}s` : <span className="text-blue-400 animate-pulse">running…</span>}
                </td>
                <td className="px-6 py-3 text-gray-400">{exec.tokens?.toLocaleString() ?? '—'}</td>
                <td className="px-6 py-3 text-gray-400 font-mono">{exec.cost ?? '—'}</td>
                <td className="px-6 py-3 text-gray-500 text-xs">{exec.model}</td>
                <td className="px-6 py-3"><ChevronRight className="w-4 h-4 text-gray-600" /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
