import { AlertTriangle, Search } from 'lucide-react'
import { StatusBadge } from '@/components/ui/StatusBadge'
import type { FailureType, FailureSeverity } from '@/types/api'

const MOCK_FAILURES = [
  { id: 'f-001', title: 'Retrieval returned empty context', failure_type: 'retrieval' as FailureType, severity: 'high' as FailureSeverity, agent: 'Research Agent', cluster_id: 3, is_resolved: false, created_at: '2026-06-10T14:12:00Z' },
  { id: 'f-002', title: 'Tool call timeout: search_web',   failure_type: 'tool'      as FailureType, severity: 'medium' as FailureSeverity, agent: 'Research Agent', cluster_id: 1, is_resolved: false, created_at: '2026-06-10T14:08:00Z' },
  { id: 'f-003', title: 'Invalid SQL generated',           failure_type: 'output'    as FailureType, severity: 'critical' as FailureSeverity, agent: 'SQL Agent',      cluster_id: 2, is_resolved: true,  created_at: '2026-06-10T13:55:00Z' },
  { id: 'f-004', title: 'Hallucination detected (0.89)',   failure_type: 'hallucination' as FailureType, severity: 'high' as FailureSeverity, agent: 'Customer Support', cluster_id: 4, is_resolved: false, created_at: '2026-06-10T13:40:00Z' },
]

export function FailuresPage() {
  return (
    <div className="p-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Failure Analysis</h1>
          <p className="text-gray-400 mt-1">Automatically clustered failures with root cause analysis</p>
        </div>
        <button className="btn-secondary flex items-center gap-2">
          <Search className="w-4 h-4" />
          Semantic Search
        </button>
      </div>

      {/* Cluster summary */}
      <div className="grid grid-cols-4 gap-3">
        {[1,2,3,4].map(c => (
          <div key={c} className="card p-4 text-center cursor-pointer hover:border-gray-700 transition-colors">
            <p className="text-xs text-gray-500">Cluster {c}</p>
            <p className="text-2xl font-bold text-white mt-1">{Math.floor(Math.random() * 15 + 3)}</p>
            <p className="text-xs text-gray-600 mt-1">failures</p>
          </div>
        ))}
      </div>

      {/* Failure list */}
      <div className="card p-0 overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-gray-500 border-b border-gray-800 bg-gray-900/50">
              <th className="px-6 py-3 font-medium">Title</th>
              <th className="px-6 py-3 font-medium">Agent</th>
              <th className="px-6 py-3 font-medium">Type</th>
              <th className="px-6 py-3 font-medium">Severity</th>
              <th className="px-6 py-3 font-medium">Cluster</th>
              <th className="px-6 py-3 font-medium">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-800">
            {MOCK_FAILURES.map(f => (
              <tr key={f.id} className="hover:bg-gray-800/40 transition-colors cursor-pointer">
                <td className="px-6 py-3">
                  <div className="flex items-center gap-2">
                    <AlertTriangle className={`w-3.5 h-3.5 flex-shrink-0 ${f.severity === 'critical' ? 'text-red-400' : f.severity === 'high' ? 'text-orange-400' : 'text-yellow-400'}`} />
                    <span className="text-white text-xs font-medium">{f.title}</span>
                  </div>
                </td>
                <td className="px-6 py-3 text-gray-400 text-xs">{f.agent}</td>
                <td className="px-6 py-3"><StatusBadge status={f.failure_type} /></td>
                <td className="px-6 py-3"><StatusBadge status={f.severity} /></td>
                <td className="px-6 py-3 text-gray-500 text-xs">#{f.cluster_id}</td>
                <td className="px-6 py-3">
                  <span className={`text-xs font-medium ${f.is_resolved ? 'text-green-400' : 'text-yellow-400'}`}>
                    {f.is_resolved ? 'Resolved' : 'Open'}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
