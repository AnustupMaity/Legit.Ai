from typing import Dict, Any, List
from api.ml_pipeline.trainer import trainer_manager
import config
from api.tasks.training_tasks import run_training_task
import db.crud as db_crud
from db.database import SessionLocal
import uuid


class FineTuner:
    def __init__(self):
        pass

    def enqueue_fine_tune(self, dataset: List[Dict[str, Any]], user_id: int, tenant_id: int, config_overrides: dict | None = None) -> str:
        """Enqueue a fine-tuning job and return a job id."""
        cfg = config_overrides or {}
        if getattr(config, "USE_CELERY", False):
            # create job id and schedule via Celery; worker will run trainer._do_training
            job_id = str(uuid.uuid4())
            # create DB job row
            db = SessionLocal()
            try:
                db_crud.create_job(db, job_id=job_id, user_id=user_id, tenant_id=tenant_id, status="queued", progress=0)
            finally:
                db.close()
            # submit Celery task
            run_training_task.apply_async(args=[job_id, dataset, user_id, tenant_id, cfg])
            return job_id
        else:
            job_id = trainer_manager.start_training(dataset, user_id=user_id, tenant_id=tenant_id, config_overrides=cfg)
            return job_id

    def job_status(self, job_id: str) -> Dict[str, Any]:
        return trainer_manager.get_status(job_id)

