"""Seed the platform with realistic demo data.

Creates a demo user + organization and populates agents, executions (with
trace spans + tool calls), a golden dataset, an evaluation run with results,
hallucination reports, and clustered failure reports — so a fresh clone shows
a populated dashboard without needing to drive real agent traffic.

Usage:
    python -m scripts.seed_demo            # seed (skips if demo org exists)
    python -m scripts.seed_demo --reset    # delete demo org first, then seed

Login afterwards with:  demo@example.com  /  demodemo123
"""
from __future__ import annotations

import asyncio
import random
import sys
from datetime import UTC, datetime, timedelta

from src.domain.entities import (
    Dataset,
    DatasetItem,
    EvaluationResult,
    EvaluationRun,
    Execution,
    ExecutionTrace,
    FailureReport,
    HallucinationReport,
    Organization,
    OrgMember,
    ToolCall,
    User,
)
from src.domain.value_objects import (
    DetectionMethod,
    EvaluationStatus,
    EvaluationType,
    ExecutionStatus,
    FailureSeverity,
    FailureType,
    TraceType,
)
from src.infrastructure.ai.cost_calculator import calculate_cost
from src.infrastructure.database.connection import get_session_factory
from src.infrastructure.database.repositories import (
    PostgresAgentV2Repository,
    PostgresDatasetItemRepository,
    PostgresDatasetRepository,
    PostgresEvaluationResultRepository,
    PostgresEvaluationRunRepository,
    PostgresExecutionRepository,
    PostgresExecutionTraceRepository,
    PostgresFailureReportRepository,
    PostgresHallucinationReportRepository,
    PostgresOrganizationRepository,
    PostgresOrgMemberRepository,
    PostgresToolCallRepository,
)
from src.infrastructure.security.password_service import hash_password

DEMO_EMAIL = "demo@example.com"
DEMO_PASSWORD = "demodemo123"
DEMO_ORG_SLUG = "demo-org"

AGENTS = [
    ("Customer Support Agent", "customer_support", "langgraph", ["production", "tier-1"]),
    ("SQL Agent", "sql", "langchain", ["analytics"]),
    ("Research Agent", "research", "langgraph", ["experimental"]),
    ("Coding Agent", "coding", "custom", ["beta"]),
]

QUESTIONS = [
    "How do I reset my password?",
    "What were our top 5 products last quarter?",
    "Summarize the latest research on retrieval-augmented generation.",
    "Write a Python function to debounce calls.",
    "Why was my payment declined?",
    "Generate a SQL query for monthly active users.",
]

MODELS = ["llama3.2", "llama3.1", "mistral"]


async def _seed(reset: bool) -> None:
    factory = get_session_factory()
    async with factory() as session:
        org_repo = PostgresOrganizationRepository(session)
        member_repo = PostgresOrgMemberRepository(session)
        agent_repo = PostgresAgentV2Repository(session)
        exec_repo = PostgresExecutionRepository(session)
        trace_repo = PostgresExecutionTraceRepository(session)
        tool_repo = PostgresToolCallRepository(session)
        dataset_repo = PostgresDatasetRepository(session)
        item_repo = PostgresDatasetItemRepository(session)
        eval_run_repo = PostgresEvaluationRunRepository(session)
        eval_result_repo = PostgresEvaluationResultRepository(session)
        halluc_repo = PostgresHallucinationReportRepository(session)
        failure_repo = PostgresFailureReportRepository(session)

        existing = await org_repo.get_by_slug(DEMO_ORG_SLUG)
        if existing and not reset:
            print(f"Demo org '{DEMO_ORG_SLUG}' already exists — nothing to do. Use --reset to rebuild.")
            return
        if existing and reset:
            # Cascade delete: removing the org cascades to agents/executions/etc.
            from sqlalchemy import text
            await session.execute(
                text("DELETE FROM organizations WHERE slug = :slug"), {"slug": DEMO_ORG_SLUG}
            )
            await session.commit()
            print(f"Deleted existing demo org '{DEMO_ORG_SLUG}'.")

        # ── User + Org + membership ──────────────────────────────────────────
        user = User.create(
            email=DEMO_EMAIL,
            hashed_password=hash_password(DEMO_PASSWORD),
            full_name="Demo User",
        )
        # User may already exist from a prior partial seed; tolerate it.
        from sqlalchemy import text
        await session.execute(
            text("DELETE FROM users WHERE email = :e"), {"e": DEMO_EMAIL}
        )
        from src.infrastructure.database.repositories import PostgresUserRepository
        await PostgresUserRepository(session).save(user)

        org = Organization.create(name="Demo Organization", description="Seeded demo data")
        org.slug = DEMO_ORG_SLUG
        await org_repo.save(org)
        await member_repo.save(OrgMember.create(org_id=org.id, user_id=user.id, role="owner"))

        # ── Agents ───────────────────────────────────────────────────────────
        agent_ids: list[str] = []
        for name, atype, framework, tags in AGENTS:
            saved = await agent_repo.save({
                "id": __import__("uuid").uuid4().__str__(),
                "org_id": org.id,
                "name": name,
                "agent_type": atype,
                "framework": framework,
                "status": "active",
                "created_by": user.id,
                "tags": tags,
                "metadata": {},
            })
            agent_ids.append(saved["id"])

        # ── Executions + traces + tool calls ─────────────────────────────────
        now = datetime.now(UTC)
        exec_ids: list[tuple[str, str, str]] = []  # (exec_id, agent_id, status)
        for i in range(40):
            agent_id = random.choice(agent_ids)
            question = random.choice(QUESTIONS)
            model = random.choice(MODELS)
            started = now - timedelta(days=random.randint(0, 13), minutes=random.randint(0, 1440))

            ex = Execution.create(org_id=org.id, agent_id=agent_id, input={"question": question},
                                  initiated_by=user.id, tags=["demo"])
            ex.started_at = started
            roll = random.random()
            in_tok, out_tok = random.randint(200, 1500), random.randint(50, 600)

            if roll < 0.78:
                ex.status = ExecutionStatus.SUCCEEDED
                ex.output = {"answer": f"Demo answer for: {question}"}
            elif roll < 0.92:
                ex.status = ExecutionStatus.FAILED
                ex.error_message = random.choice([
                    "Tool call timeout: search_web",
                    "Failed to parse JSON response",
                    "Retrieval returned no documents",
                ])
            else:
                ex.status = ExecutionStatus.TIMED_OUT
                ex.error_message = "Execution exceeded time limit"

            duration = random.randint(300, 9000)
            ex.completed_at = started + timedelta(milliseconds=duration)
            ex.duration_ms = duration
            ex.input_tokens, ex.output_tokens = in_tok, out_tok
            ex.total_tokens = in_tok + out_tok
            ex.model_provider, ex.model_name = "ollama", model
            ex.total_cost_usd = calculate_cost("ollama", model, in_tok, out_tok)  # $0 (free)
            await exec_repo.save(ex)
            exec_ids.append((ex.id, agent_id, ex.status.value))

            # A couple of trace spans per execution
            planner = ExecutionTrace.create(ex.id, TraceType.PLANNER, "Plan query",
                                            {"q": question}, sequence_order=0)
            planner.complete(output={"plan": "answer"}, input_tokens=120, output_tokens=40)
            await trace_repo.save(planner)
            llm = ExecutionTrace.create(ex.id, TraceType.LLM_CALL, "Generate response",
                                        {"prompt": question}, sequence_order=1, model=model)
            if ex.status == ExecutionStatus.SUCCEEDED:
                llm.complete(output={"text": "..."}, input_tokens=in_tok, output_tokens=out_tok)
            else:
                llm.fail(ex.error_message or "error")
            await trace_repo.save(llm)

            if "tool" in (ex.error_message or "").lower():
                tc = ToolCall.create(ex.id, "search_web", "search", {"q": question})
                tc.fail("Upstream 504 Gateway Timeout")
                await tool_repo.save(tc)

        await session.commit()

        # ── Golden dataset ───────────────────────────────────────────────────
        dataset = Dataset.create(org_id=org.id, name="Support QA — Golden Set",
                                 created_by=user.id, dataset_type="golden",
                                 description="Hand-labelled support Q&A pairs")
        await dataset_repo.save(dataset)
        items = [
            DatasetItem.create(dataset.id, {"question": q},
                               expected_output={"answer": f"Reference answer for: {q}"})
            for q in QUESTIONS
        ]
        await item_repo.save_bulk(items)
        await session.commit()

        # ── Evaluation run + results ─────────────────────────────────────────
        run = EvaluationRun.create(org_id=org.id, agent_id=agent_ids[0], created_by=user.id,
                                   name="LLM-Judge Baseline", eval_type=EvaluationType.LLM_JUDGE,
                                   dataset_id=dataset.id)
        run.start(total_items=len(items))
        results = []
        passed_count = 0
        for item in items:
            passed = random.random() < 0.82
            passed_count += int(passed)
            results.append(EvaluationResult.create(
                eval_run_id=run.id, passed=passed, dataset_item_id=item.id,
                correctness_score=round(random.uniform(0.5, 1.0), 4),
                relevance_score=round(random.uniform(0.6, 1.0), 4),
                helpfulness_score=round(random.uniform(0.5, 1.0), 4),
                reasoning="Demo-seeded score",
            ))
            run.record_item_completed()
        await eval_result_repo.save_bulk(results)
        run.complete(aggregate_scores={
            "pass_rate": round(passed_count / len(items), 4),
            "total": len(items), "passed": passed_count,
        })
        run.status = EvaluationStatus.COMPLETED
        await eval_run_repo.save(run)
        await session.commit()

        # ── Hallucination reports (on a few failed/odd execs) ────────────────
        for exec_id, _agent, _status in exec_ids[:5]:
            score = round(random.uniform(0.2, 0.95), 4)
            await halluc_repo.save(HallucinationReport.create(
                execution_id=exec_id, hallucination_score=score,
                confidence=round(random.uniform(0.6, 0.95), 4),
                detection_method=DetectionMethod.LLM_JUDGE,
                flagged_segments=[{"text": "fabricated claim", "reason": "unsupported"}] if score >= 0.7 else [],
                reasoning="Demo-seeded detection",
            ))

        # ── Failure reports (for failed/timed-out execs) ─────────────────────
        ftype_map = {
            "tool": (FailureType.TOOL, FailureSeverity.MEDIUM, "Tool call failure"),
            "parse": (FailureType.OUTPUT, FailureSeverity.HIGH, "Output parse failure"),
            "retrieval": (FailureType.RETRIEVAL, FailureSeverity.HIGH, "Retrieval returned empty"),
            "time": (FailureType.TIMEOUT, FailureSeverity.HIGH, "Execution timed out"),
        }
        cluster = 0
        for exec_id, _agent, status in exec_ids:
            if status in ("failed", "timed_out"):
                ftype, sev, title = FailureType.UNKNOWN, FailureSeverity.MEDIUM, "Execution failed"
                # crude keyword pick for variety
                key = random.choice(list(ftype_map))
                ftype, sev, title = ftype_map[key]
                fr = FailureReport.create(
                    org_id=org.id, execution_id=exec_id, failure_type=ftype, severity=sev,
                    title=title, description=f"Demo-seeded {ftype.value} failure",
                    root_cause="Seeded for demo",
                )
                fr.assign_cluster(cluster % 4)
                cluster += 1
                await failure_repo.save(fr)

        await session.commit()

        print("✓ Demo data seeded.")
        print(f"  Org:    {org.name} (slug: {org.slug})")
        print(f"  Login:  {DEMO_EMAIL} / {DEMO_PASSWORD}")
        print(f"  Agents: {len(agent_ids)}  Executions: {len(exec_ids)}  Dataset items: {len(items)}")


def main() -> None:
    reset = "--reset" in sys.argv
    asyncio.run(_seed(reset))


if __name__ == "__main__":
    main()
