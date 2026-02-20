"""
Celery application configuration.

Per spec: Celery is used for async extraction and processing tasks.
Workers run sync SQLAlchemy inside tasks.
"""

from celery import Celery

from munipal.config import get_settings

settings = get_settings()

# Create Celery app
celery_app = Celery(
    "munipal",
    broker=settings.celery_broker,
    backend=settings.celery_backend,
    include=[
        "munipal.workers.tasks.artifact_tasks",
        "munipal.workers.tasks.extraction_tasks",
        "munipal.workers.tasks.deliverable_tasks",
    ],
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,

    # Task execution
    task_acks_late=True,  # Acknowledge after task completes (for reliability)
    task_reject_on_worker_lost=True,
    task_track_started=True,

    # Result backend
    result_expires=86400,  # Results expire after 24 hours

    # Worker settings
    worker_prefetch_multiplier=1,  # Process one task at a time (for AI tasks)
    worker_concurrency=4,  # Number of concurrent workers

    # Task routing
    task_routes={
        "munipal.workers.tasks.extraction_tasks.*": {"queue": "extraction"},
        "munipal.workers.tasks.artifact_tasks.*": {"queue": "artifacts"},
        "munipal.workers.tasks.deliverable_tasks.*": {"queue": "deliverables"},
    },

    # Default queue
    task_default_queue="default",

    # Retry settings
    task_annotations={
        "*": {
            "rate_limit": "10/m",  # Default rate limit
            "max_retries": 3,
            "default_retry_delay": 60,
        },
        # AI extraction tasks get special handling
        "munipal.workers.tasks.extraction_tasks.*": {
            "rate_limit": "5/m",  # Lower rate for AI API calls
            "max_retries": 2,
            "default_retry_delay": 120,
        },
    },
)

# Beat schedule for periodic tasks (if needed)
celery_app.conf.beat_schedule = {
    # Example: Clean up old extraction jobs
    # "cleanup-old-jobs": {
    #     "task": "munipal.workers.tasks.maintenance.cleanup_old_jobs",
    #     "schedule": 3600.0,  # Every hour
    # },
}
