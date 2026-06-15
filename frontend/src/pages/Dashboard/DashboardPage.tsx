import { Zap, CheckCircle, DollarSign, Clock } from 'lucide-react'
import {
  ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid,
} from 'recharts'
import { StatCard } from '@/components/ui/StatCard'
import { StatusBadge } from '@/components/ui/StatusBadge'
import { QueryBoundary } from '@/components/ui/QueryBoundary'
import { useCostSummary, useExecutionStats, useExecutions } from '@/hooks/useApi'

export function DashboardPage() {
  const stats = useExecutionStats(7)
  const cost = useCostSummary(14)
  const executions = useExecutions()

  const recent = executions.data?.items.slice(0, 6) ?? []
  const trend =
    cost.data?.daily.map((d) => ({
      date: new Date(d.date).toLocaleDateString('en', { month: 'short', day: 'numeric' }),
      executions: d.executions,
      failures: d.failed,
    })) ?? []

  const fmtCost = (v: number | undefined) => (v != null ? `$${v.toFixed(4)}` : '—')
  const fmtLatency = (ms: number | undefined) =>
    ms != null ? `${(ms / 1000).toFixed(2)}s` : '—'

  return (
    <div className="p-8 space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-white">Platform Overview</h1>
        <p className="text-gray-400 mt-1">Monitor your AI agents in real-time</p>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-2 xl:grid-cols-4 gap-4">
        <StatCard title="Executions (7d)" value={stats.data?.total ?? '—'} icon={Zap} iconColor="text-brand-400" />
        <StatCard
          title="Success Rate"
          value={stats.data ? `${stats.data.success_rate}%` : '—'}
          icon={CheckCircle}
          iconColor="text-green-400"
        />
        <StatCard
          title="Avg Latency"
          value={fmtLatency(stats.data?.avg_duration_ms)}
          icon={Clock}
          iconColor="text-yellow-400"
        />
        <StatCard
          title="Cost (14d)"
          value={fmtCost(cost.data?.total_cost_usd)}
          icon={DollarSign}
          iconColor="text-purple-400"
        />
      </div>

      {/* Execution trend */}
      <div className="card">
        <h2 className="text-base font-semibold text-white mb-4">Executions Over Time</h2>
        <QueryBoundary
          isLoading={cost.isLoading}
          isError={cost.isError}
          isEmpty={trend.length === 0}
          emptyMessage="No executions in the last 14 days."
        >
          <ResponsiveContainer width="100%" height={220}>
            <AreaChart data={trend}>
              <defs>
                <linearGradient id="execGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
              <XAxis dataKey="date" tick={{ fill: '#6b7280', fontSize: 12 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: '#6b7280', fontSize: 12 }} axisLine={false} tickLine={false} />
              <Tooltip contentStyle={{ background: '#111827', border: '1px solid #1f2937', borderRadius: 8 }} labelStyle={{ color: '#9ca3af' }} />
              <Area type="monotone" dataKey="executions" stroke="#3b82f6" fill="url(#execGrad)" strokeWidth={2} />
              <Area type="monotone" dataKey="failures" stroke="#ef4444" fill="transparent" strokeWidth={1.5} strokeDasharray="4 2" />
            </AreaChart>
          </ResponsiveContainer>
        </QueryBoundary>
      </div>

      {/* Recent executions */}
      <div className="card">
        <h2 className="text-base font-semibold text-white mb-4">Recent Executions</h2>
        <QueryBoundary
          isLoading={executions.isLoading}
          isError={executions.isError}
          isEmpty={recent.length === 0}
          emptyMessage="No executions recorded yet."
        >
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
              {recent.map((row) => (
                <tr key={row.id} className="hover:bg-gray-800/50 transition-colors">
                  <td className="py-3 text-white font-mono text-xs">{row.agent_id.slice(0, 8)}</td>
                  <td className="py-3"><StatusBadge status={row.status} /></td>
                  <td className="py-3 text-gray-400 font-mono">{fmtLatency(row.duration_ms ?? undefined)}</td>
                  <td className="py-3 text-gray-400 font-mono">{row.total_cost_usd ? `$${row.total_cost_usd}` : '—'}</td>
                  <td className="py-3 text-gray-500 text-xs">{row.model_name ?? '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </QueryBoundary>
      </div>
    </div>
  )
}
