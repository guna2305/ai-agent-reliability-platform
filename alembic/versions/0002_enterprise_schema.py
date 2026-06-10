"""Enterprise schema: users, orgs, agent versions, executions, traces, evaluations

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-10 00:00:00.000000

Design decisions:
- String(36) UUIDs for portability (no native UUID type dependency)
- JSONB for all flexible/semi-structured data with GIN indexes where queried
- Composite indexes on (org_id, *) for multi-tenant query patterns
- HNSW-ready: failure_reports.embedding_vector prepared as TEXT (migrate to
  pgvector in 0003 once extension confirmed on target cluster)
- Cascade deletes from executions to traces/tool_calls (time-series child rows)
- Numeric(5,4) for 0-1 scores preserving 4 decimal places of precision
- Numeric(10,8) for cost tracking (sub-cent precision)
"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ──────────────────────────────────────────────
    # Users & Auth
    # ──────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("is_superuser", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # ──────────────────────────────────────────────
    # Organizations (Multi-tenancy root)
    # ──────────────────────────────────────────────
    op.create_table(
        "organizations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(63), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("plan", sa.String(20), nullable=False, server_default="free"),
        sa.Column("metadata", JSONB, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_organizations_slug", "organizations", ["slug"], unique=True)
    op.create_index("ix_organizations_name", "organizations", ["name"], unique=True)

    op.create_table(
        "org_members",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("org_id", sa.String(36),
                  sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.String(36),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("org_id", "user_id", name="uq_org_members_org_user"),
    )
    op.create_index("ix_org_members_org_id", "org_members", ["org_id"])
    op.create_index("ix_org_members_user_id", "org_members", ["user_id"])

    op.create_table(
        "api_keys",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("org_id", sa.String(36),
                  sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.String(36),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("key_hash", sa.String(64), nullable=False),
        sa.Column("key_prefix", sa.String(20), nullable=False),
        sa.Column("scopes", JSONB, nullable=False, server_default="[]"),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_api_keys_key_hash", "api_keys", ["key_hash"], unique=True)
    op.create_index("ix_api_keys_org_id", "api_keys", ["org_id"])

    # ──────────────────────────────────────────────
    # Agent Registry v2 (org-owned, versioned)
    # ──────────────────────────────────────────────
    op.create_table(
        "agents_v2",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("org_id", sa.String(36),
                  sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("agent_type", sa.String(50), nullable=False),
        sa.Column("framework", sa.String(50), nullable=False, server_default="custom"),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("created_by", sa.String(36),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("tags", ARRAY(sa.String), nullable=False, server_default="{}"),
        sa.Column("metadata", JSONB, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("org_id", "slug", name="uq_agents_v2_org_slug"),
    )
    op.create_index("ix_agents_v2_org_id", "agents_v2", ["org_id"])
    op.create_index("ix_agents_v2_status", "agents_v2", ["status"])
    op.create_index("ix_agents_v2_org_status", "agents_v2", ["org_id", "status"])

    op.create_table(
        "agent_versions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("agent_id", sa.String(36),
                  sa.ForeignKey("agents_v2.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version", sa.String(50), nullable=False),
        sa.Column("version_number", sa.Integer, nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("config", JSONB, nullable=False, server_default="{}"),
        sa.Column("system_prompt", sa.Text, nullable=True),
        sa.Column("tools", JSONB, nullable=False, server_default="[]"),
        sa.Column("is_production", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_by", sa.String(36), nullable=False),
        sa.Column("metadata", JSONB, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("agent_id", "version_number", name="uq_agent_versions_agent_vnum"),
    )
    op.create_index("ix_agent_versions_agent_id", "agent_versions", ["agent_id"])
    op.create_index("ix_agent_versions_is_production", "agent_versions", ["is_production"])

    # ──────────────────────────────────────────────
    # Executions (rich execution tracking)
    # ──────────────────────────────────────────────
    op.create_table(
        "executions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("org_id", sa.String(36),
                  sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("agent_id", sa.String(36), nullable=False),
        sa.Column("agent_version_id", sa.String(36), nullable=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("trigger_type", sa.String(20), nullable=False),
        sa.Column("input", JSONB, nullable=False),
        sa.Column("output", JSONB, nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_ms", sa.Integer, nullable=True),
        sa.Column("total_tokens", sa.Integer, nullable=True),
        sa.Column("input_tokens", sa.Integer, nullable=True),
        sa.Column("output_tokens", sa.Integer, nullable=True),
        sa.Column("total_cost_usd", sa.Numeric(10, 8), nullable=True),
        sa.Column("model_provider", sa.String(50), nullable=True),
        sa.Column("model_name", sa.String(100), nullable=True),
        sa.Column("tags", ARRAY(sa.String), nullable=False, server_default="{}"),
        sa.Column("metadata", JSONB, nullable=False, server_default="{}"),
        sa.Column("initiated_by", sa.String(36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_executions_org_id", "executions", ["org_id"])
    op.create_index("ix_executions_agent_id", "executions", ["agent_id"])
    op.create_index("ix_executions_status", "executions", ["status"])
    op.create_index("ix_executions_started_at", "executions", ["started_at"])
    # Composite: most common dashboard query
    op.create_index(
        "ix_executions_org_agent_started",
        "executions",
        ["org_id", "agent_id", sa.text("started_at DESC")],
    )

    op.create_table(
        "execution_traces",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("execution_id", sa.String(36),
                  sa.ForeignKey("executions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("parent_trace_id", sa.String(36), nullable=True),
        sa.Column("span_id", sa.String(36), nullable=False),
        sa.Column("trace_type", sa.String(30), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("input", JSONB, nullable=False),
        sa.Column("output", JSONB, nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_ms", sa.Integer, nullable=True),
        sa.Column("model", sa.String(100), nullable=True),
        sa.Column("input_tokens", sa.Integer, nullable=True),
        sa.Column("output_tokens", sa.Integer, nullable=True),
        sa.Column("cost_usd", sa.Numeric(10, 8), nullable=True),
        sa.Column("error", sa.Text, nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="success"),
        sa.Column("sequence_order", sa.Integer, nullable=False),
        sa.Column("metadata", JSONB, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_exec_traces_execution_id", "execution_traces", ["execution_id"])
    op.create_index(
        "ix_exec_traces_exec_seq",
        "execution_traces",
        ["execution_id", "sequence_order"],
    )

    op.create_table(
        "tool_calls",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("execution_id", sa.String(36),
                  sa.ForeignKey("executions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("trace_id", sa.String(36), nullable=True),
        sa.Column("tool_name", sa.String(255), nullable=False),
        sa.Column("tool_type", sa.String(50), nullable=False),
        sa.Column("input", JSONB, nullable=False),
        sa.Column("output", JSONB, nullable=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("duration_ms", sa.Integer, nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_tool_calls_execution_id", "tool_calls", ["execution_id"])
    op.create_index("ix_tool_calls_tool_name", "tool_calls", ["tool_name"])

    # ──────────────────────────────────────────────
    # Evaluation Framework
    # ──────────────────────────────────────────────
    op.create_table(
        "datasets",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("org_id", sa.String(36),
                  sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("dataset_type", sa.String(30), nullable=False),
        sa.Column("created_by", sa.String(36), nullable=False),
        sa.Column("metadata", JSONB, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_datasets_org_id", "datasets", ["org_id"])

    op.create_table(
        "dataset_items",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("dataset_id", sa.String(36),
                  sa.ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("input", JSONB, nullable=False),
        sa.Column("expected_output", JSONB, nullable=True),
        sa.Column("context", JSONB, nullable=False, server_default="[]"),
        sa.Column("metadata", JSONB, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_dataset_items_dataset_id", "dataset_items", ["dataset_id"])

    op.create_table(
        "evaluation_runs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("org_id", sa.String(36),
                  sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("agent_id", sa.String(36), nullable=False),
        sa.Column("agent_version_id", sa.String(36), nullable=True),
        sa.Column("dataset_id", sa.String(36), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("eval_type", sa.String(30), nullable=False),
        sa.Column("config", JSONB, nullable=False, server_default="{}"),
        sa.Column("total_items", sa.Integer, nullable=False, server_default="0"),
        sa.Column("completed_items", sa.Integer, nullable=False, server_default="0"),
        sa.Column("failed_items", sa.Integer, nullable=False, server_default="0"),
        sa.Column("aggregate_scores", JSONB, nullable=False, server_default="{}"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.String(36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_eval_runs_org_id", "evaluation_runs", ["org_id"])
    op.create_index("ix_eval_runs_agent_id", "evaluation_runs", ["agent_id"])
    op.create_index("ix_eval_runs_status", "evaluation_runs", ["status"])

    op.create_table(
        "evaluation_results",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("eval_run_id", sa.String(36),
                  sa.ForeignKey("evaluation_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("execution_id", sa.String(36), nullable=True),
        sa.Column("dataset_item_id", sa.String(36), nullable=True),
        sa.Column("correctness_score", sa.Numeric(5, 4), nullable=True),
        sa.Column("relevance_score", sa.Numeric(5, 4), nullable=True),
        sa.Column("faithfulness_score", sa.Numeric(5, 4), nullable=True),
        sa.Column("helpfulness_score", sa.Numeric(5, 4), nullable=True),
        sa.Column("hallucination_score", sa.Numeric(5, 4), nullable=True),
        sa.Column("context_precision", sa.Numeric(5, 4), nullable=True),
        sa.Column("context_recall", sa.Numeric(5, 4), nullable=True),
        sa.Column("answer_relevancy", sa.Numeric(5, 4), nullable=True),
        sa.Column("custom_scores", JSONB, nullable=False, server_default="{}"),
        sa.Column("reasoning", sa.Text, nullable=True),
        sa.Column("passed", sa.Boolean, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_eval_results_eval_run_id", "evaluation_results", ["eval_run_id"])
    op.create_index("ix_eval_results_passed", "evaluation_results", ["eval_run_id", "passed"])

    # ──────────────────────────────────────────────
    # Hallucination & Failure Tracking
    # ──────────────────────────────────────────────
    op.create_table(
        "hallucination_reports",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("execution_id", sa.String(36),
                  sa.ForeignKey("executions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("eval_result_id", sa.String(36), nullable=True),
        sa.Column("hallucination_score", sa.Numeric(5, 4), nullable=False),
        sa.Column("confidence", sa.Numeric(5, 4), nullable=False),
        sa.Column("detection_method", sa.String(50), nullable=False),
        sa.Column("flagged_segments", JSONB, nullable=False, server_default="[]"),
        sa.Column("reasoning", sa.Text, nullable=True),
        sa.Column("is_confirmed", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_hallucination_reports_execution_id", "hallucination_reports", ["execution_id"])

    op.create_table(
        "failure_reports",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("org_id", sa.String(36),
                  sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("execution_id", sa.String(36),
                  sa.ForeignKey("executions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("eval_result_id", sa.String(36), nullable=True),
        sa.Column("failure_type", sa.String(30), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("root_cause", sa.Text, nullable=True),
        sa.Column("embedding_vector", sa.Text, nullable=True),  # JSON list; migrate to pgvector later
        sa.Column("cluster_id", sa.Integer, nullable=True),
        sa.Column("is_resolved", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("resolution_notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_failure_reports_org_id", "failure_reports", ["org_id"])
    op.create_index("ix_failure_reports_execution_id", "failure_reports", ["execution_id"])
    op.create_index("ix_failure_reports_type", "failure_reports", ["org_id", "failure_type"])
    op.create_index("ix_failure_reports_cluster", "failure_reports", ["cluster_id"])
    op.create_index("ix_failure_reports_created_at", "failure_reports", ["created_at"])

    # ──────────────────────────────────────────────
    # Analytics, Experiments, Audit
    # ──────────────────────────────────────────────
    op.create_table(
        "metrics",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("org_id", sa.String(36),
                  sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("agent_id", sa.String(36), nullable=True),
        sa.Column("metric_name", sa.String(100), nullable=False),
        sa.Column("metric_value", sa.Numeric(15, 4), nullable=False),
        sa.Column("unit", sa.String(30), nullable=False),
        sa.Column("dimensions", JSONB, nullable=False, server_default="{}"),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_metrics_org_name_at", "metrics", ["org_id", "metric_name", sa.text("recorded_at DESC")])
    op.create_index("ix_metrics_agent_name_at", "metrics", ["agent_id", "metric_name", sa.text("recorded_at DESC")])

    op.create_table(
        "experiments",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("org_id", sa.String(36),
                  sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("config", JSONB, nullable=False, server_default="{}"),
        sa.Column("created_by", sa.String(36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_experiments_org_id", "experiments", ["org_id"])

    op.create_table(
        "experiment_variants",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("experiment_id", sa.String(36),
                  sa.ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("agent_version_id", sa.String(36), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("traffic_weight", sa.Numeric(5, 2), nullable=False),
        sa.Column("config", JSONB, nullable=False, server_default="{}"),
    )
    op.create_index("ix_experiment_variants_exp_id", "experiment_variants", ["experiment_id"])

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("org_id", sa.String(36), nullable=True),
        sa.Column("user_id", sa.String(36), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("resource_type", sa.String(100), nullable=False),
        sa.Column("resource_id", sa.String(36), nullable=True),
        sa.Column("old_value", JSONB, nullable=True),
        sa.Column("new_value", JSONB, nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_audit_logs_org_id", "audit_logs", ["org_id", sa.text("created_at DESC")])


def downgrade() -> None:
    for table in [
        "audit_logs", "experiment_variants", "experiments", "metrics",
        "failure_reports", "hallucination_reports",
        "evaluation_results", "evaluation_runs", "dataset_items", "datasets",
        "tool_calls", "execution_traces", "executions",
        "agent_versions", "agents_v2",
        "api_keys", "org_members", "organizations", "users",
    ]:
        op.drop_table(table)
