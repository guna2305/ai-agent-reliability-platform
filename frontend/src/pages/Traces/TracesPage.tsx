import { useParams } from 'react-router-dom'
import { ChevronRight, Cpu, Search, Wrench, FileText, Brain } from 'lucide-react'
import { clsx } from 'clsx'
import type { TraceType } from '@/types/api'

const TRACE_ICONS: Record<TraceType | string, React.ElementType> = {
  llm_call:  Cpu,
  tool_call: Wrench,
  retrieval: Search,
  planner:   Brain,
  memory:    FileText,
  custom:    ChevronRight,
}

const TRACE_COLORS: Record<string, string> = {
  llm_call:  'text-blue-400 bg-blue-900/20 border-blue-800',
  tool_call: 'text-yellow-400 bg-yellow-900/20 border-yellow-800',
  retrieval: 'text-purple-400 bg-purple-900/20 border-purple-800',
  planner:   'text-green-400 bg-green-900/20 border-green-800',
  memory:    'text-gray-400 bg-gray-800 border-gray-700',
  custom:    'text-gray-400 bg-gray-800 border-gray-700',
}

const MOCK_TRACES = [
  { id: 't1', trace_type: 'planner',   name: 'Plan user query',          duration_ms: 210,  status: 'success', input_tokens: 320,  output_tokens: 95 },
  { id: 't2', trace_type: 'retrieval', name: 'Retrieve relevant docs',   duration_ms: 380,  status: 'success', input_tokens: null, output_tokens: null },
  { id: 't3', trace_type: 'llm_call',  name: 'Generate draft response',  duration_ms: 1840, status: 'success', input_tokens: 1200, output_tokens: 480 },
  { id: 't4', trace_type: 'tool_call', name: 'search_knowledge_base',    duration_ms: 95,   status: 'success', input_tokens: null, output_tokens: null },
  { id: 't5', trace_type: 'llm_call',  name: 'Refine and format output', duration_ms: 920,  status: 'success', input_tokens: 680,  output_tokens: 210 },
]

export function TracesPage() {
  const { executionId } = useParams()

  return (
    <div className="p-8 space-y-6">
      <div>
        <p className="text-xs text-gray-500 font-mono mb-1">Execution / {executionId}</p>
        <h1 className="text-2xl font-bold text-white">Trace Viewer</h1>
        <p className="text-gray-400 mt-1">Step-by-step execution timeline</p>
      </div>

      {/* Timeline */}
      <div className="card space-y-2">
        {MOCK_TRACES.map((trace, i) => {
          const Icon = TRACE_ICONS[trace.trace_type] ?? ChevronRight
          const colorClass = TRACE_COLORS[trace.trace_type] ?? TRACE_COLORS.custom
          return (
            <div key={trace.id} className="flex gap-4">
              {/* Connector */}
              <div className="flex flex-col items-center">
                <div className={clsx('w-8 h-8 rounded-lg border flex items-center justify-center flex-shrink-0', colorClass)}>
                  <Icon className="w-4 h-4" />
                </div>
                {i < MOCK_TRACES.length - 1 && (
                  <div className="w-px flex-1 bg-gray-800 mt-1" />
                )}
              </div>

              {/* Content */}
              <div className="flex-1 pb-4">
                <div className="flex items-start justify-between">
                  <div>
                    <span className="text-xs font-medium uppercase tracking-wide text-gray-500">{trace.trace_type.replace('_', ' ')}</span>
                    <h3 className="text-sm font-medium text-white mt-0.5">{trace.name}</h3>
                  </div>
                  <div className="text-right">
                    <span className="text-xs font-mono text-gray-400">{trace.duration_ms}ms</span>
                    {trace.input_tokens && (
                      <p className="text-xs text-gray-600 mt-0.5">
                        {trace.input_tokens}↑ {trace.output_tokens}↓ tokens
                      </p>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* Token / cost summary */}
      <div className="grid grid-cols-3 gap-4">
        {[
          { label: 'Total Tokens', value: '2,985' },
          { label: 'Est. Cost',    value: '$0.0089' },
          { label: 'Total Time',   value: '3.44s' },
        ].map(({ label, value }) => (
          <div key={label} className="card text-center">
            <p className="text-xs text-gray-500">{label}</p>
            <p className="text-xl font-bold text-white mt-1 font-mono">{value}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
