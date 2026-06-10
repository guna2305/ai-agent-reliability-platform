import { useQuery } from '@tanstack/react-query'
import { Zap, CheckCircle, DollarSign, AlertTriangle, Activity, Clock } from 'lucide-react'
import { StatCard } from '@/components/ui/StatCard'
import { StatusBadge } from '@/components/ui/StatusBadge'
import {
  ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid,
} from 'recharts'

// Placeholder data — replaced by real API calls in Phase 7
const MOCK_EXECUTIONS_TREND = Array.from({ length: 14 }, (_, i) => ({
  date: new Date(Date.now() - (13 - i) * 86400000).toLocaleDateString('en', { month: 'short', day: 'numeric' }),
  executions: Math.floor(Math.random() * 200 + 50),
  failures: Math.floor(Math.random() * 20),
}))

const MOCK_RECENT = [
  { id: 'exec-1', agent: 'Customer Support', status: 'succeeded', duration_ms: 1240, cost: '$0.0042', model: 'gpt-4o' },
  { id: 'exec-2', agent: 'SQL Agent',        status: 'failed',    duration_ms: 320,  cost: '$0.0008', model: 'gpt-4o' },
  { id: 'exec-3', agent: 'Research Agent',   status: 'running',   duration_ms: null, cost: null,      model: 'claude-3-5-sonnet' },
  { id: 'exec-4', agent: 'Coding Agent',     status: 'succeeded', duration_ms: 8900, cost: '$0.0231', model: 'gpt-4o' },
]

export function DashboardPage() {
  return (
    <div className="p-8 space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white">Platform Overview</h1>
        <p className="text-gray-400 mt-1">Monitor your AI agents in real-time</p>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-2 xl:grid-cols-4 gap-4">
        <StatCard title="Total Executions"   value="12,847"  delta="8% vs last week" deltaPositive icon={Zap}           iconColor="text-brand-400" />
        <StatCard title="Success Rate"       value="94.2%"   delta="1.3pp vs last week" deltaPositive icon={CheckCircle} iconColor="text-green-400" />
        <StatCard title="Avg Latency"        value="1.8s"    delta="120ms vs last week" deltaPositive={false} icon={Clock} iconColor="text-yellow-400" />
        <StatCard title="Total Cost (7d)"    value="$48.21"  delta="$3.10 vs last week" deltaPositive={false} icon={DollarSign} iconColor="text-purple-400" />
      </div>

      {/* Execution trend */}
      <div className="card">
        <h2 className="text-base font-semibold text-white mb-4">Executions Over Time</h2>
        <ResponsiveContainer width="100%" height={220}>
          <AreaChart data={MOCK_EXECUTIONS_TREND}>
            <defs>
              <linearGradient id="execGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%"  stopColor="#3b82f6" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
            <XAxis dataKey="date" tick={{ fill: '#6b7280', fontSize: 12 }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fill: '#6b7280', fontSize: 12 }} axisLine={false} tickLine={false} />
            <Tooltip
              contentStyle={{ background: '#111827', border: '1px solid #1f2937', borderRadius: 8 }}
              labelStyle={{ color: '#9ca3af' }}
            />
            <Area type="monotone" dataKey="executions" stroke="#3b82f6" fill="url(#execGrad)" strokeWidth={2} />
            <Area type="monotone" dataKey="failures"   stroke="#ef4444" fill="transparent" strokeWidth={1.5} strokeDasharray="4 2" />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Recent executions */}
      <div className="card">
        <h2 className="text-base font-semibold text-white mb-4">Recent Executions</h2>
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-gray-500 border-b border-gray-800">
              <th className="pb-3 font-medium">Agent</th>
              <th className="pb-3 font-medium">Status</th>
              <th className="pb-3 font-medium">Duration</th>
              <th className="pb-3 font-medium">Cost</th>
              <th className="pb-3 font-medium">Model</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-800">
            {MOCK_RECENT.map((row) => (
              <tr key={row.id} className="hover:bg-gray-800/50 transition-colors cursor-pointer">
                <td className="py-3 text-white font-medium">{row.agent}</td>
                <td className="py-3"><StatusBadge status={row.status} /></td>
                <td className="py-3 text-gray-400 font-mono">
                  {row.duration_ms ? `${(row.duration_ms / 1000).toFixed(2)}s` : '—'}
                </td>
                <td className="py-3 text-gray-400 font-mono">{row.cost ?? '—'}</td>
                <td className="py-3 text-gray-500 text-xs">{row.model}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
