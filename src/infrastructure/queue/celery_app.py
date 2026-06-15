from celery import Celery
from kombu import Exchange, Queue

from src.infrastructure.config.settings import get_settings


def create_celery_app() -> Celery:
    settings = get_settings()

    app = Celery(
        "agent_reliability",
        broker=settings.celery_broker_url,
        backend=settings.celery_result_backend,
        include=[
            "src.infrastructure.queue.tasks.evaluation_tasks",
            "src.infrastructure.queue.tasks.hallucination_tasks",
            "src.infrastructure.queue.tasks.analytics_tasks",
            "src.infrastructure.queue.tasks.embedding_tasks",
        ],
    )

    # Queues with priority tiers
    app.conf.task_queues = (
        Queue("critical", Exchange("critical"), routing_key="critical"),
        Queue("evaluations", Exchange("evaluations"), routing_key="evaluations"),
        Queue("analytics", Exchange("analytics"), routing_key="analytics"),
    )
    app.conf.task_default_queue = "evaluations"
    app.conf.task_default_exchange = "evaluations"
    app.conf.task_default_routing_key = "evaluations"

    app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        task_track_started=True,
        task_acks_late=True,                 # Requeue on worker crash
        worker_prefetch_multiplier=1,        # Fair dispatch
        task_always_eager=settings.celery_task_always_eager,
        task_soft_time_limit=settings.eval_job_timeout_seconds,
        task_time_limit=settings.eval_job_timeout_seconds + 60,
        worker_max_tasks_per_child=200,      # Prevent memory leaks
        result_expires=86400,                # 24h result retention
    )

    return app


celery_app = create_celery_app()
