import { FlaskConical, Play, CheckCircle, XCircle } from 'lucide-react'
import { StatusBadge } from '@/components/ui/StatusBadge'
import type { EvaluationStatus } from '@/types/api'

const MOCK_RUNS = [
  { id: 'eval-001', name: 'GPT-4o Baseline',    agent: 'Customer Support', eval_type: 'llm_judge',    status: 'completed' as EvaluationStatus, total_items: 100, pass_rate: 0.87, avg_score: 0.82 },
  { id: 'eval-002', name: 'RAG Quality v2',     agent: 'Research Agent',   eval_type: 'rag',          status: 'running'   as EvaluationStatus, total_items: 50,  pass_rate: null, avg_score: null },
  { id: 'eval-003', name: 'Ground Truth Check', agent: 'SQL Agent',        eval_type: 'ground_truth', status: 'completed' as EvaluationStatus, total_items: 200, pass_rate: 0.91, avg_score: 0.89 },
  { id: 'eval-004', name: 'Hallucination Scan', agent: 'Coding Agent',     eval_type: 'llm_judge',    status: 'pending'   as EvaluationStatus, total_items: 75,  pass_rate: null, avg_score: null },
]

export function EvaluationsPage() {
  return (
    <div className="p-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Evaluations</h1>
          <p className="text-gray-400 mt-1">LLM-judge, RAGAS, ground-truth evaluation runs</p>
        </div>
        <button className="btn-primary flex items-center gap-2">
          <Play className="w-4 h-4" />
          New Evaluation Run
        </button>
      </div>

      <div className="space-y-3">
        {MOCK_RUNS.map(run => (
          <div key={run.id} className="card hover:border-gray-700 transition-colors cursor-pointer">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="w-10 h-10 bg-gray-800 rounded-lg flex items-center justify-center">
                  <FlaskConical className="w-5 h-5 text-purple-400" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-white">{run.name}</h3>
                  <p className="text-xs text-gray-500 mt-0.5">
                    {run.agent} · {run.eval_type.replace('_', ' ')} · {run.total_items} items
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-6">
                {run.pass_rate !== null && (
                  <div className="text-right">
                    <p className="text-xs text-gray-500">Pass Rate</p>
                    <p className="text-sm font-bold text-white">{(run.pass_rate * 100).toFixed(1)}%</p>
                  </div>
                )}
                {run.avg_score !== null && (
                  <div className="text-right">
                    <p className="text-xs text-gray-500">Avg Score</p>
                    <p className="text-sm font-bold text-white">{run.avg_score.toFixed(2)}</p>
                  </div>
                )}
                <StatusBadge status={run.status} />
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
