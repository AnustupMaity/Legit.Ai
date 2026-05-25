from api.celery_app import celery
import db.crud as db_crud
from db.database import SessionLocal


@celery.task(bind=True)
def run_training_task(self, job_id: str, data: list, user_id: int, tenant_id: int, cfg: dict):
    # Import trainer here to avoid heavy imports at module load
    from api.ml_pipeline.trainer import trainer_manager

    # mark job as running in DB
    db = SessionLocal()
    try:
        db_crud.update_job_status(db, job_id, status="running", progress=0)
    finally:
        db.close()

    # Run training synchronously within the worker process
    trainer_manager._do_training(job_id, data, user_id, tenant_id, cfg)

    # After completion, try to read status.json and update DB
    db = SessionLocal()
    try:
        status = trainer_manager.get_status(job_id)
        db_crud.update_job_status(db, job_id, status=status.get("status"), progress=status.get("progress", 0), result=status.get("result"))
    finally:
        db.close()

    return {"status": "submitted", "job_id": job_id}
