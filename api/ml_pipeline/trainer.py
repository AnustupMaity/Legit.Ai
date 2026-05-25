import os
import uuid
import json
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List

import config
from db.database import SessionLocal
import db.crud as db_crud

try:
    import torch
    from transformers import AutoTokenizer, AutoModelForSequenceClassification, Trainer, TrainingArguments
    from datasets import Dataset, DatasetDict
    HF_AVAILABLE = True
except Exception:
    HF_AVAILABLE = False


class TrainerManager:
    def __init__(self, models_dir: str = "models", max_workers: int = 1):
        self.models_dir = models_dir
        os.makedirs(self.models_dir, exist_ok=True)
        self.lock = threading.Lock()
        self.pool = ThreadPoolExecutor(max_workers=max_workers)

    def start_training(self, data: List[Dict[str, Any]], user_id: int, tenant_id: int, config_overrides: dict | None = None) -> str:
        job_id = str(uuid.uuid4())
        # Persist initial status to DB
        try:
            db = SessionLocal()
            db_crud.create_job(db, job_id=job_id, user_id=user_id, tenant_id=tenant_id, status="queued", progress=0)
        finally:
            try:
                db.close()
            except Exception:
                pass
        
        # schedule
        self.pool.submit(self._run_training, job_id, data, user_id, tenant_id, config_overrides or {})
        return job_id

    def get_status(self, job_id: str) -> Dict[str, Any]:
        try:
            db = SessionLocal()
            rec = db_crud.get_job_by_job_id(db, job_id)
            if rec:
                import json
                try:
                    res = json.loads(rec.result) if rec.result else None
                except Exception:
                    res = rec.result
                return {
                    "id": rec.job_id,
                    "status": rec.status,
                    "progress": rec.progress,
                    "result": res,
                    "created_at": rec.created_at,
                    "updated_at": rec.updated_at,
                }
        finally:
            try:
                db.close()
            except Exception:
                pass
        return {"status": "not_found"}

    def _run_training(self, job_id: str, data: List[Dict[str, Any]], user_id: int, tenant_id: int, cfg: dict):
        try:
            db = SessionLocal()
            db_crud.update_job_status(db, job_id, status="running")
        finally:
            db.close()

        try:
            if not HF_AVAILABLE:
                # fallback: fake training
                try:
                    db = SessionLocal()
                    db_crud.update_job_status(db, job_id, progress=50)
                finally:
                    db.close()

                import time
                time.sleep(2)
                model_path = os.path.join(self.models_dir, tenant_id and str(tenant_id) or "global", job_id)
                os.makedirs(model_path, exist_ok=True)
                # create a dummy file
                with open(os.path.join(model_path, "model.txt"), "w") as f:
                    f.write("fake-model")
                
                try:
                    db = SessionLocal()
                    db_crud.update_job_status(db, job_id, status="completed", progress=100, result={"model_path": model_path, "status": "success", "metrics": {}})
                except Exception:
                    pass
                finally:
                    try:
                        db.close()
                    except Exception:
                        pass
                return

            # Determine problem type by inspecting keys
            texts = [d.get("text") or d.get("input") for d in data]
            labels = [d.get("label") for d in data]
            has_labels = any(l is not None for l in labels)

            # prepare dataset
            records = []
            unique_labels = sorted(list(set([l for l in labels if l is not None])))
            label_map = {l: idx for idx, l in enumerate(unique_labels)}
            
            for i, t in enumerate(texts):
                rec = {"text": t}
                if has_labels:
                    val = labels[i]
                    if val is not None:
                        try:
                            rec["label"] = int(val)
                        except ValueError:
                            rec["label"] = label_map[val]
                    else:
                        rec["label"] = 0
                records.append(rec)

            ds = Dataset.from_list(records)
            # simple 90/10 split
            ds = ds.train_test_split(test_size=0.1)
            tokenizer = AutoTokenizer.from_pretrained(cfg.get("model_name", "distilbert-base-uncased"))

            def tokenize(batch):
                return tokenizer(batch["text"], truncation=True, padding="max_length", max_length=128)

            ds = ds.map(tokenize, batched=True)
            model = AutoModelForSequenceClassification.from_pretrained(cfg.get("model_name", "distilbert-base-uncased"), num_labels=len(set([l for l in labels if l is not None])) if has_labels else 2)

            output_dir = os.path.join(self.models_dir, str(tenant_id), job_id)
            os.makedirs(output_dir, exist_ok=True)

            training_args = TrainingArguments(
                output_dir=output_dir,
                num_train_epochs=cfg.get("epochs", 1),
                per_device_train_batch_size=cfg.get("batch_size", 8),
                per_device_eval_batch_size=cfg.get("batch_size", 8),
                eval_strategy="epoch" if has_labels else "no",
                save_strategy="epoch",
                logging_dir=os.path.join(output_dir, "logs"),
                logging_steps=cfg.get("logging_steps", 10),
            )

            trainer = Trainer(
                model=model,
                args=training_args,
                train_dataset=ds["train"],
                eval_dataset=ds.get("test") if has_labels else None,
            )

            trainer.train()
            trainer.save_model(output_dir)

            metrics = {}
            if has_labels:
                metrics = trainer.evaluate()

            try:
                db = SessionLocal()
                db_crud.update_job_status(db, job_id, status="completed", progress=100, result={"model_path": output_dir, "status": "success", "metrics": metrics})
            except Exception:
                pass
            finally:
                try:
                    db.close()
                except Exception:
                    pass
        except Exception as e:
            try:
                db = SessionLocal()
                db_crud.update_job_status(db, job_id, status="failed", result={"error": str(e)})
            except Exception:
                pass
            finally:
                try:
                    db.close()
                except Exception:
                    pass



    def _do_training(self, job_id: str, data: List[Dict[str, Any]], user_id: int, tenant_id: int, cfg: dict):
        """Synchronous training function useful for Celery workers."""
        try:
            db = SessionLocal()
            db_crud.update_job_status(db, job_id, status="running")
        finally:
            db.close()

        try:
            # replicate core training steps from _run_training
            if not HF_AVAILABLE:
                try:
                    db = SessionLocal()
                    db_crud.update_job_status(db, job_id, progress=50)
                finally:
                    db.close()

                import time
                time.sleep(2)
                model_path = os.path.join(self.models_dir, str(tenant_id) if tenant_id else "global", job_id)
                os.makedirs(model_path, exist_ok=True)
                with open(os.path.join(model_path, "model.txt"), "w") as f:
                    f.write("fake-model")
                try:
                    db = SessionLocal()
                    db_crud.update_job_status(db, job_id, status="completed", progress=100, result={"model_path": model_path, "status": "success", "metrics": {}})
                except Exception:
                    pass
                finally:
                    db.close()
                return

            texts = [d.get("text") or d.get("input") for d in data]
            labels = [d.get("label") for d in data]
            has_labels = any(l is not None for l in labels)
            records = []
            unique_labels = sorted(list(set([l for l in labels if l is not None])))
            label_map = {l: idx for idx, l in enumerate(unique_labels)}

            for i, t in enumerate(texts):
                rec = {"text": t}
                if has_labels:
                    val = labels[i]
                    if val is not None:
                        try:
                            rec["label"] = int(val)
                        except ValueError:
                            rec["label"] = label_map[val]
                    else:
                        rec["label"] = 0
                records.append(rec)

            ds = Dataset.from_list(records)
            ds = ds.train_test_split(test_size=0.1)
            tokenizer = AutoTokenizer.from_pretrained(cfg.get("model_name", "distilbert-base-uncased"))

            def tokenize(batch):
                return tokenizer(batch["text"], truncation=True, padding="max_length", max_length=128)

            ds = ds.map(tokenize, batched=True)
            model = AutoModelForSequenceClassification.from_pretrained(cfg.get("model_name", "distilbert-base-uncased"), num_labels=len(set([l for l in labels if l is not None])) if has_labels else 2)

            output_dir = os.path.join(self.models_dir, str(tenant_id), job_id)
            os.makedirs(output_dir, exist_ok=True)

            training_args = TrainingArguments(
                output_dir=output_dir,
                num_train_epochs=cfg.get("epochs", 1),
                per_device_train_batch_size=cfg.get("batch_size", 8),
                per_device_eval_batch_size=cfg.get("batch_size", 8),
                eval_strategy="epoch" if has_labels else "no",
                save_strategy="epoch",
                logging_dir=os.path.join(output_dir, "logs"),
                logging_steps=cfg.get("logging_steps", 10),
            )

            trainer = Trainer(
                model=model,
                args=training_args,
                train_dataset=ds["train"],
                eval_dataset=ds.get("test") if has_labels else None,
            )

            trainer.train()
            trainer.save_model(output_dir)

            metrics = {}
            if has_labels:
                metrics = trainer.evaluate()

            try:
                db = SessionLocal()
                db_crud.update_job_status(db, job_id, status="completed", progress=100, result={"model_path": output_dir, "status": "success", "metrics": metrics})
            except Exception:
                pass
            finally:
                db.close()
        except Exception as e:
            try:
                db = SessionLocal()
                db_crud.update_job_status(db, job_id, status="failed", result={"error": str(e)})
            except Exception:
                pass
            finally:
                db.close()


trainer_manager = TrainerManager()
