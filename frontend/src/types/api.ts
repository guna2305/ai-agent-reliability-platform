// ─── Core API Types ─────────────────────────────────────────────────────────

export type AgentStatus = 'active' | 'inactive' | 'deprecated'
export type AgentType = 'customer_support' | 'resume_screening' | 'sql' | 'research' | 'coding' | 'rag' | 'custom'
export type ExecutionStatus = 'queued' | 'running' | 'succeeded' | 'failed' | 'cancelled' | 'timed_out'
export type EvaluationStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'
export type FailureType = 'prompt' | 'retrieval' | 'tool' | 'output' | 'timeout' | 'cost' | 'hallucination' | 'unknown'
export type FailureSeverity = 'low' | 'medium' | 'high' | 'critical'
export type TraceType = 'llm_call' | 'tool_call' | 'retrieval' | 'planner' | 'memory' | 'custom'

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  limit: number
  offset: number
}

// ─── Agents ─────────────────────────────────────────────────────────────────

export interface Agent {
  id: string
  org_id: string
  name: string
  slug: string
  description: string | null
  agent_type: AgentType
  framework: string
  status: AgentStatus
  tags: string[]
  created_by: string
  created_at: string
  updated_at: string
}

export interface AgentVersion {
  id: string
  agent_id: string
  version: string
  version_number: number
  description: string | null
  config: Record<string, unknown>
  system_prompt: string | null
  tools: ToolDefinition[]
  is_production: boolean
  created_by: string
  created_at: string
}

export interface ToolDefinition {
  name: string
  description: string
  parameters: Record<string, unknown>
}

// ─── Executions ──────────────────────────────────────────────────────────────

export interface Execution {
  id: string
  org_id: string
  agent_id: string
  agent_version_id: string | null
  status: ExecutionStatus
  trigger_type: string
  input: Record<string, unknown>
  output: Record<string, unknown> | null
  error_message: string | null
  started_at: string
  completed_at: string | null
  duration_ms: number | null
  total_tokens: number | null
  input_tokens: number | null
  output_tokens: number | null
  total_cost_usd: string | null
  model_provider: string | null
  model_name: string | null
  tags: string[]
}

export interface ExecutionTrace {
  id: string
  execution_id: string
  parent_trace_id: string | null
  trace_type: TraceType
  name: string
  input: Record<string, unknown>
  output: Record<string, unknown> | null
  started_at: string
  ended_at: string | null
  duration_ms: number | null
  model: string | null
  input_tokens: number | null
  output_tokens: number | null
  cost_usd: string | null
  error: string | null
  status: string
  sequence_order: number
}

// ─── Evaluations ─────────────────────────────────────────────────────────────

export interface EvaluationRun {
  id: string
  org_id: string
  agent_id: string
  name: string
  status: EvaluationStatus
  eval_type: string
  total_items: number
  completed_items: number
  failed_items: number
  aggregate_scores: Record<string, number>
  started_at: string | null
  completed_at: string | null
  created_at: string
}

export interface EvaluationResult {
  id: string
  eval_run_id: string
  correctness_score: string | null
  relevance_score: string | null
  faithfulness_score: string | null
  helpfulness_score: string | null
  hallucination_score: string | null
  context_precision: string | null
  context_recall: string | null
  answer_relevancy: string | null
  reasoning: string | null
  passed: boolean
  created_at: string
}

// ─── Analytics ───────────────────────────────────────────────────────────────

export interface CostSummary {
  total_cost_usd: number
  total_executions: number
  avg_cost_per_execution: number
  by_model: Record<string, number>
  by_day: DailyCost[]
}

export interface DailyCost {
  date: string
  cost_usd: number
  executions: number
  tokens: number
}

export interface PerformanceSummary {
  success_rate: number
  avg_latency_ms: number
  p50_latency_ms: number
  p95_latency_ms: number
  total_executions: number
  failed_executions: number
}

// ─── Failures ────────────────────────────────────────────────────────────────

export interface FailureReport {
  id: string
  org_id: string
  execution_id: string
  failure_type: FailureType
  severity: FailureSeverity
  title: string
  description: string
  root_cause: string | null
  cluster_id: number | null
  is_resolved: boolean
  created_at: string
}
