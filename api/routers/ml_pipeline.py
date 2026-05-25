from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from db.database import get_db

from api.dependencies import get_current_user, get_current_tenant # Assuming these are needed for auth context
from db.user import User
from db.tenant import Tenant
from api.ml_pipeline.data_preprocessor import DataPreprocessor
from api.ml_pipeline.fine_tuner import FineTuner
from api.ml_pipeline.model_manager import ModelVersionManager

from api.ml_pipeline.trainer import trainer_manager


router = APIRouter()

# Initialize pipeline components
preprocessor = DataPreprocessor()
fine_tuner = FineTuner()
model_manager = ModelVersionManager()


@router.post("/fine-tune", response_model=Dict[str, Any])
async def start_fine_tuning(
    dataset_file: UploadFile = File(...),
    # Depend on auth and tenant resolution to get user and tenant context
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    # Add other parameters as needed, e.g., model_config, training_epochs
):
    """Upload a dataset and initiate a model fine-tuning process."""
    # In a real application, you would save the uploaded file securely
    # and then process it.
    dataset_content = await dataset_file.read()
    # For simplicity, assume the uploaded file is a JSON list of records
    # In a real app, parse dataset_content appropriately (e.g., json.loads, pandas.read_csv)
    try:
        # Placeholder: Simulate loading dataset from bytes
        # Replace this with actual parsing based on expected file format
        import json
        dataset = json.loads(dataset_content.decode())
        if not isinstance(dataset, list):
            dataset = [dataset] # Ensure it's a list if a single dict is uploaded

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON dataset format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing dataset: {e}")

    # Preprocess the data
    processed_data = preprocessor.preprocess(dataset)

    # Enqueue fine-tuning as background job
    job_id = fine_tuner.enqueue_fine_tune(processed_data, user_id=current_user.id, tenant_id=current_tenant.id)

    print(f"Fine-tuning job {job_id} enqueued by user {current_user.id} for tenant {current_tenant.id}.")

    return {"job_id": job_id}



@router.get("/fine-tune/status/{job_id}")
def fine_tune_status(job_id: str):
    return trainer_manager.get_status(job_id)


@router.get("/models/{version_id}")
def get_model_info(version_id: str):
    """Retrieve information about a specific fine-tuned model version."""
    model_path = model_manager.get_model_path(version_id)
    if not model_path:
        raise HTTPException(status_code=404, detail=f"Model version {version_id} not found")
    # In a real app, you might return more details about the model
    return {"version_id": version_id, "model_path": model_path}


@router.get("/jobs")
def list_jobs(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # List jobs for the current user from DB
    rows = []
    try:
        rows = db.query(__import__('db.models', fromlist=['Job']).Job).filter_by(user_id=current_user.id).order_by(__import__('sqlalchemy').desc(__import__('db.models', fromlist=['Job']).Job.created_at)).all()
    except Exception:
        # fallback: empty
        rows = []
    results = []
    import json
    for r in rows:
        try:
            res = json.loads(r.result) if r.result else None
        except Exception:
            res = r.result
        results.append({
            'job_id': r.job_id,
            'status': r.status,
            'progress': r.progress,
            'result': res,
            'created_at': r.created_at,
            'updated_at': r.updated_at,
        })
    return {'jobs': results}
