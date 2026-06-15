import { FlaskConical } from 'lucide-react'
import { StatusBadge } from '@/components/ui/StatusBadge'
import { QueryBoundary } from '@/components/ui/QueryBoundary'
import { useEvaluationRuns } from '@/hooks/useApi'
import type { EvaluationRun } from '@/types/api'

export function EvaluationsPage() {
  const { data, isLoading, isError } = useEvaluationRuns()
  const runs = data?.items ?? []

  return (
    <div className="p-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Evaluations</h1>
          <p className="text-gray-400 mt-1">LLM-judge, ground-truth, and RAG evaluation runs</p>
        </div>
      </div>

      <QueryBoundary
        isLoading={isLoading}
        isError={isError}
        isEmpty={runs.length === 0}
        emptyMessage="No evaluation runs yet."
      >
        <div className="space-y-3">
          {runs.map((run) => (
            <EvalRunCard key={run.id} run={run} />
          ))}
        </div>
      </QueryBoundary>
    </div>
  )
}

function EvalRunCard({ run }: { run: EvaluationRun }) {
  const passRate = run.aggregate_scores?.pass_rate as number | undefined
  const progress = run.total_items > 0 ? Math.round((run.completed_items / run.total_items) * 100) : 0

  return (
    <div className="card hover:border-gray-700 transition-colors cursor-pointer">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="w-10 h-10 bg-gray-800 rounded-lg flex items-center justify-center">
            <FlaskConical className="w-5 h-5 text-purple-400" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-white">{run.name}</h3>
            <p className="text-xs text-gray-500 mt-0.5">
              {run.eval_type.replace('_', ' ')} · {run.completed_items}/{run.total_items} items
              {run.failed_items > 0 && <span className="text-red-400"> · {run.failed_items} failed</span>}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-6">
          {passRate != null && (
            <div className="text-right">
              <p className="text-xs text-gray-500">Pass Rate</p>
              <p className="text-sm font-bold text-white">{(passRate * 100).toFixed(1)}%</p>
            </div>
          )}
          {run.status === 'running' && (
            <div className="text-right">
              <p className="text-xs text-gray-500">Progress</p>
              <p className="text-sm font-bold text-blue-400">{progress}%</p>
            </div>
          )}
          <StatusBadge status={run.status} />
        </div>
      </div>
    </div>
  )
}
