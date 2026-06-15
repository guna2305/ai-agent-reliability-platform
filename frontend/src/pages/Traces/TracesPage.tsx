import { useParams } from 'react-router-dom'
import { ChevronRight, Cpu, Search, Wrench, FileText, Brain } from 'lucide-react'
import { clsx } from 'clsx'
import { QueryBoundary } from '@/components/ui/QueryBoundary'
import { useExecutionTraces } from '@/hooks/useApi'
import type { TraceType } from '@/types/api'

const TRACE_ICONS: Record<TraceType | string, React.ElementType> = {
  llm_call: Cpu,
  tool_call: Wrench,
  retrieval: Search,
  planner: Brain,
  memory: FileText,
  custom: ChevronRight,
}

const TRACE_COLORS: Record<string, string> = {
  llm_call: 'text-blue-400 bg-blue-900/20 border-blue-800',
  tool_call: 'text-yellow-400 bg-yellow-900/20 border-yellow-800',
  retrieval: 'text-purple-400 bg-purple-900/20 border-purple-800',
  planner: 'text-green-400 bg-green-900/20 border-green-800',
  memory: 'text-gray-400 bg-gray-800 border-gray-700',
  custom: 'text-gray-400 bg-gray-800 border-gray-700',
}

interface TraceNode {
  id: string
  trace_type: string
  name: string
  status: string
  duration_ms: number | null
  input_tokens: number | null
  output_tokens: number | null
  cost_usd: string | null
  children: TraceNode[]
}

export function TracesPage() {
  const { executionId } = useParams()
  const { data, isLoading, isError } = useExecutionTraces(executionId)

  // The backend returns a nested tree; flatten depth-first for the timeline view.
  const flatten = (nodes: TraceNode[], depth = 0): Array<TraceNode & { depth: number }> =>
    nodes.flatMap((n) => [{ ...n, depth }, ...flatten(n.children ?? [], depth + 1)])

  // The /traces endpoint returns a nested tree (TraceNode), not the flat
  // ExecutionTrace shape the API client is typed with — cast through unknown.
  const spans = flatten((data as unknown as TraceNode[]) ?? [])

  const totalTokens = spans.reduce((sum, s) => sum + (s.input_tokens ?? 0) + (s.output_tokens ?? 0), 0)
  const totalMs = spans.reduce((sum, s) => sum + (s.duration_ms ?? 0), 0)
  const totalCost = spans.reduce((sum, s) => sum + (s.cost_usd ? parseFloat(s.cost_usd) : 0), 0)

  return (
    <div className="p-8 space-y-6">
      <div>
        <p className="text-xs text-gray-500 font-mono mb-1">Execution / {executionId}</p>
        <h1 className="text-2xl font-bold text-white">Trace Viewer</h1>
        <p className="text-gray-400 mt-1">Step-by-step execution timeline</p>
      </div>

      <div className="card space-y-2">
        <QueryBoundary
          isLoading={isLoading}
          isError={isError}
          isEmpty={spans.length === 0}
          emptyMessage="No trace spans recorded for this execution."
        >
          {spans.map((trace, i) => {
            const Icon = TRACE_ICONS[trace.trace_type] ?? ChevronRight
            const colorClass = TRACE_COLORS[trace.trace_type] ?? TRACE_COLORS.custom
            return (
              <div key={trace.id} className="flex gap-4" style={{ marginLeft: trace.depth * 24 }}>
                <div className="flex flex-col items-center">
                  <div className={clsx('w-8 h-8 rounded-lg border flex items-center justify-center flex-shrink-0', colorClass)}>
                    <Icon className="w-4 h-4" />
                  </div>
                  {i < spans.length - 1 && <div className="w-px flex-1 bg-gray-800 mt-1" />}
                </div>
                <div className="flex-1 pb-4">
                  <div className="flex items-start justify-between">
                    <div>
                      <span className="text-xs font-medium uppercase tracking-wide text-gray-500">
                        {trace.trace_type.replace('_', ' ')}
                      </span>
                      <h3 className={clsx('text-sm font-medium mt-0.5', trace.status === 'error' ? 'text-red-400' : 'text-white')}>
                        {trace.name}
                      </h3>
                    </div>
                    <div className="text-right">
                      <span className="text-xs font-mono text-gray-400">{trace.duration_ms ?? 0}ms</span>
                      {(trace.input_tokens || trace.output_tokens) && (
                        <p className="text-xs text-gray-600 mt-0.5">
                          {trace.input_tokens ?? 0}↑ {trace.output_tokens ?? 0}↓ tokens
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )
          })}
        </QueryBoundary>
      </div>

      {spans.length > 0 && (
        <div className="grid grid-cols-3 gap-4">
          {[
            { label: 'Total Tokens', value: totalTokens.toLocaleString() },
            { label: 'Est. Cost', value: `$${totalCost.toFixed(6)}` },
            { label: 'Total Span Time', value: `${(totalMs / 1000).toFixed(2)}s` },
          ].map(({ label, value }) => (
            <div key={label} className="card text-center">
              <p className="text-xs text-gray-500">{label}</p>
              <p className="text-xl font-bold text-white mt-1 font-mono">{value}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
