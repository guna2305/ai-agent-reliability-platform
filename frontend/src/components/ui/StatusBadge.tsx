import { clsx } from 'clsx'
import type { ExecutionStatus, AgentStatus, EvaluationStatus, FailureSeverity } from '@/types/api'

type AnyStatus = ExecutionStatus | AgentStatus | EvaluationStatus | FailureSeverity | string

const STATUS_STYLES: Record<string, string> = {
  // Execution
  succeeded: 'bg-green-900/30 text-green-400 border-green-800',
  running:   'bg-blue-900/30 text-blue-400 border-blue-800',
  queued:    'bg-gray-800 text-gray-400 border-gray-700',
  failed:    'bg-red-900/30 text-red-400 border-red-800',
  cancelled: 'bg-gray-800 text-gray-500 border-gray-700',
  timed_out: 'bg-orange-900/30 text-orange-400 border-orange-800',
  // Agent
  active:     'bg-green-900/30 text-green-400 border-green-800',
  inactive:   'bg-gray-800 text-gray-400 border-gray-700',
  deprecated: 'bg-red-900/30 text-red-400 border-red-800',
  // Evaluation
  pending:   'bg-yellow-900/30 text-yellow-400 border-yellow-800',
  completed: 'bg-green-900/30 text-green-400 border-green-800',
  // Severity
  critical: 'bg-red-900/30 text-red-400 border-red-800',
  high:     'bg-orange-900/30 text-orange-400 border-orange-800',
  medium:   'bg-yellow-900/30 text-yellow-400 border-yellow-800',
  low:      'bg-gray-800 text-gray-400 border-gray-700',
}

interface StatusBadgeProps {
  status: AnyStatus
  className?: string
}

export function StatusBadge({ status, className }: StatusBadgeProps) {
  const styles = STATUS_STYLES[status] ?? 'bg-gray-800 text-gray-400 border-gray-700'
  return (
    <span className={clsx(
      'inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium border',
      styles, className
    )}>
      {status.replace(/_/g, ' ')}
    </span>
  )
}
