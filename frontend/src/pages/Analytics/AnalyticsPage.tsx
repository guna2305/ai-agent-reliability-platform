import { DollarSign, TrendingUp, Activity, Clock } from 'lucide-react'
import { StatCard } from '@/components/ui/StatCard'
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, LineChart, Line, Legend,
} from 'recharts'

const COST_BY_MODEL = [
  { model: 'gpt-4o',               cost: 28.42 },
  { model: 'claude-3-5-sonnet',    cost: 12.19 },
  { model: 'gpt-4o-mini',          cost: 5.82 },
  { model: 'claude-haiku',         cost: 1.78 },
]

const COST_TREND = Array.from({ length: 7 }, (_, i) => ({
  day: ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'][i],
  cost: parseFloat((Math.random() * 8 + 4).toFixed(2)),
  executions: Math.floor(Math.random() * 300 + 100),
}))

export function AnalyticsPage() {
  return (
    <div className="p-8 space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-white">Analytics</h1>
        <p className="text-gray-400 mt-1">Cost tracking, performance metrics, and reliability trends</p>
      </div>

      <div className="grid grid-cols-2 xl:grid-cols-4 gap-4">
        <StatCard title="7-Day Cost"    value="$48.21" delta="12% vs prior week" deltaPositive={false} icon={DollarSign} iconColor="text-green-400" />
        <StatCard title="Avg Score"     value="0.84"   delta="0.03 vs prior week" deltaPositive icon={TrendingUp} iconColor="text-brand-400" />
        <StatCard title="p95 Latency"   value="4.2s"   delta="0.8s vs prior week" deltaPositive={false} icon={Clock} iconColor="text-yellow-400" />
        <StatCard title="Error Rate"    value="5.8%"   delta="1.3pp vs prior week" deltaPositive icon={Activity} iconColor="text-red-400" />
      </div>

      <div className="grid grid-cols-2 gap-6">
        {/* Cost by model */}
        <div className="card">
          <h2 className="text-base font-semibold text-white mb-4">Cost by Model (7d)</h2>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={COST_BY_MODEL} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" horizontal={false} />
              <XAxis type="number" tick={{ fill: '#6b7280', fontSize: 11 }} tickFormatter={v => `$${v}`} axisLine={false} tickLine={false} />
              <YAxis type="category" dataKey="model" tick={{ fill: '#9ca3af', fontSize: 11 }} width={120} axisLine={false} tickLine={false} />
              <Tooltip contentStyle={{ background: '#111827', border: '1px solid #1f2937', borderRadius: 8 }} formatter={(v) => [`$${v}`, 'Cost']} />
              <Bar dataKey="cost" fill="#3b82f6" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Daily trend */}
        <div className="card">
          <h2 className="text-base font-semibold text-white mb-4">Daily Cost & Executions</h2>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={COST_TREND}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
              <XAxis dataKey="day" tick={{ fill: '#6b7280', fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis yAxisId="left"  tick={{ fill: '#6b7280', fontSize: 11 }} axisLine={false} tickLine={false} tickFormatter={v => `$${v}`} />
              <YAxis yAxisId="right" orientation="right" tick={{ fill: '#6b7280', fontSize: 11 }} axisLine={false} tickLine={false} />
              <Tooltip contentStyle={{ background: '#111827', border: '1px solid #1f2937', borderRadius: 8 }} />
              <Legend wrapperStyle={{ color: '#9ca3af', fontSize: 12 }} />
              <Line yAxisId="left"  type="monotone" dataKey="cost"       stroke="#3b82f6" strokeWidth={2} dot={false} name="Cost ($)" />
              <Line yAxisId="right" type="monotone" dataKey="executions" stroke="#8b5cf6" strokeWidth={2} dot={false} name="Executions" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  )
}
