from __future__ import annotations
from celery import Celery
import config

celery = Celery(
    "legitai_tasks",
    broker=config.CELERY_BROKER_URL,
    backend=config.CELERY_RESULT_BACKEND,
)

# Optional: configure Celery settings
celery.conf.update(task_serializer='json', accept_content=['json'], result_serializer='json')
import os

from celery import Celery

import config

# Celery configuration
celery_app = Celery(
    "legit_ai",
    broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
    backend=os.getenv("CELERY_BACKEND_URL", "redis://localhost:6379/1"),
    include=["celery_tasks"]
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
)

# Optional: Configure for development
if os.getenv("ENVIRONMENT") == "development":
    celery_app.conf.update(
        task_acks_late=True,
        worker_prefetch_multiplier=4,
    )

print("Celery app configured successfully")