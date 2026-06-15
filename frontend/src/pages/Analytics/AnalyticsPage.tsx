import { DollarSign, TrendingUp, Activity, Clock } from 'lucide-react'
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, LineChart, Line, Legend,
} from 'recharts'
import { StatCard } from '@/components/ui/StatCard'
import { QueryBoundary } from '@/components/ui/QueryBoundary'
import { useCostSummary, useExecutionStats } from '@/hooks/useApi'

export function AnalyticsPage() {
  const stats = useExecutionStats(30)
  const cost = useCostSummary(30)

  const byModel = cost.data?.by_model.map((m) => ({ model: m.model, cost: m.cost_usd })) ?? []
  const daily =
    cost.data?.daily.map((d) => ({
      day: new Date(d.date).toLocaleDateString('en', { month: 'short', day: 'numeric' }),
      cost: d.cost_usd,
      executions: d.executions,
    })) ?? []

  return (
    <div className="p-8 space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-white">Analytics</h1>
        <p className="text-gray-400 mt-1">Cost tracking, performance metrics, and reliability trends (30 days)</p>
      </div>

      <div className="grid grid-cols-2 xl:grid-cols-4 gap-4">
        <StatCard title="30-Day Cost" value={cost.data ? `$${cost.data.total_cost_usd.toFixed(4)}` : '—'} icon={DollarSign} iconColor="text-green-400" />
        <StatCard title="Executions" value={stats.data?.total ?? '—'} icon={TrendingUp} iconColor="text-brand-400" />
        <StatCard title="Avg Latency" value={stats.data ? `${(stats.data.avg_duration_ms / 1000).toFixed(2)}s` : '—'} icon={Clock} iconColor="text-yellow-400" />
        <StatCard
          title="Failure Rate"
          value={stats.data ? `${(100 - stats.data.success_rate).toFixed(1)}%` : '—'}
          icon={Activity}
          iconColor="text-red-400"
        />
      </div>

      <div className="grid grid-cols-2 gap-6">
        <div className="card">
          <h2 className="text-base font-semibold text-white mb-4">Cost by Model</h2>
          <QueryBoundary isLoading={cost.isLoading} isError={cost.isError} isEmpty={byModel.length === 0} emptyMessage="No cost data (Ollama runs are free).">
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={byModel} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" horizontal={false} />
                <XAxis type="number" tick={{ fill: '#6b7280', fontSize: 11 }} tickFormatter={(v) => `$${v}`} axisLine={false} tickLine={false} />
                <YAxis type="category" dataKey="model" tick={{ fill: '#9ca3af', fontSize: 11 }} width={120} axisLine={false} tickLine={false} />
                <Tooltip contentStyle={{ background: '#111827', border: '1px solid #1f2937', borderRadius: 8 }} formatter={(v) => [`$${v}`, 'Cost']} />
                <Bar dataKey="cost" fill="#3b82f6" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </QueryBoundary>
        </div>

        <div className="card">
          <h2 className="text-base font-semibold text-white mb-4">Daily Cost & Executions</h2>
          <QueryBoundary isLoading={cost.isLoading} isError={cost.isError} isEmpty={daily.length === 0} emptyMessage="No daily activity yet.">
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={daily}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                <XAxis dataKey="day" tick={{ fill: '#6b7280', fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis yAxisId="left" tick={{ fill: '#6b7280', fontSize: 11 }} axisLine={false} tickLine={false} tickFormatter={(v) => `$${v}`} />
                <YAxis yAxisId="right" orientation="right" tick={{ fill: '#6b7280', fontSize: 11 }} axisLine={false} tickLine={false} />
                <Tooltip contentStyle={{ background: '#111827', border: '1px solid #1f2937', borderRadius: 8 }} />
                <Legend wrapperStyle={{ color: '#9ca3af', fontSize: 12 }} />
                <Line yAxisId="left" type="monotone" dataKey="cost" stroke="#3b82f6" strokeWidth={2} dot={false} name="Cost ($)" />
                <Line yAxisId="right" type="monotone" dataKey="executions" stroke="#8b5cf6" strokeWidth={2} dot={false} name="Executions" />
              </LineChart>
            </ResponsiveContainer>
          </QueryBoundary>
        </div>
      </div>
    </div>
  )
}
