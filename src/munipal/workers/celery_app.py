"""
Celery application configuration.

Per spec: Celery is used for async extraction and processing tasks.
Workers run sync SQLAlchemy inside tasks.
"""

import ssl
from urllib.parse import parse_qsl, urlparse

from celery import Celery

from munipal.config import get_settings

settings = get_settings()


def _redis_ssl_config(url: str) -> dict[str, object] | None:
    """Translate rediss:// URL params into Celery SSL config."""
    parsed = urlparse(url)
    if parsed.scheme != "rediss":
        return None

    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    cert_reqs = {
        "required": ssl.CERT_REQUIRED,
        "optional": ssl.CERT_OPTIONAL,
        "none": ssl.CERT_NONE,
        "CERT_REQUIRED": ssl.CERT_REQUIRED,
        "CERT_OPTIONAL": ssl.CERT_OPTIONAL,
        "CERT_NONE": ssl.CERT_NONE,
    }.get(query.get("ssl_cert_reqs", "required"), ssl.CERT_REQUIRED)

    ssl_config: dict[str, object] = {"ssl_cert_reqs": cert_reqs}
    for key in ("ssl_ca_certs", "ssl_certfile", "ssl_keyfile"):
        if query.get(key):
            ssl_config[key] = query[key]
    return ssl_config


redis_ssl_config = _redis_ssl_config(settings.redis_connection_url)

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

    # Hosted Redis TLS support
    broker_use_ssl=redis_ssl_config,
    redis_backend_use_ssl=redis_ssl_config,
)

# Beat schedule for periodic tasks (if needed)
celery_app.conf.beat_schedule = {
    # Example: Clean up old extraction jobs
    # "cleanup-old-jobs": {
    #     "task": "munipal.workers.tasks.maintenance.cleanup_old_jobs",
    #     "schedule": 3600.0,  # Every hour
    # },
}
