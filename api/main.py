from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, File, HTTPException, Query, UploadFile, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, Response
from sqlalchemy.orm import Session

import config
from backend.model import fake_detection
from backend.model.audio_detector import is_audio_model_loaded
from backend.model.image_detector import (
    is_ai_image_model_loaded,
    is_image_model_loaded,
)
from backend.model.text_detector import is_enhanced_model_loaded, is_text_model_loaded
from backend.model.zero_shot_classifier import is_zero_shot_model_loaded
from db import crud
from db.database import get_db, init_db
from middleware.rate_limit import RateLimitMiddleware
from schemas import (
    AppSettings,
    BatchDetectionResponse,
    BatchTextRequest,
    DetectionRecord,
    DetectionResult,
    HealthResponse,
    HistoryResponse,
    StatsResponse,
    TextDetectionRequest,
    UrlDetectionRequest,
)
from services import detection_service

from api.routers import auth, ml_pipeline, xai
from api.routers.xai import router as xai_router
from db.user import User
from db.tenant import Tenant
from api.dependencies import get_current_user, get_current_tenant


import asyncio

async def background_cleanup_loop():
    while True:
        try:
            # Run cleanup every hour
            await asyncio.sleep(3600)
            from db.database import SessionLocal
            db = SessionLocal()
            try:
                crud.delete_old_detections(db, hours=24)
            finally:
                db.close()
        except asyncio.CancelledError:
            break
        except Exception as exc:
            print(f"Background cleanup error: {exc}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    if config.EAGER_LOAD_MODELS:
        fake_detection.preload_models()
    
    # Start the background cleanup task
    cleanup_task = asyncio.create_task(background_cleanup_loop())
    
    # Initialize default admin user
    from db.database import SessionLocal
    import db.crud as db_crud
    db = SessionLocal()
    try:
        admin_user = db_crud.get_user_by_username(db, "admin")
        if not admin_user:
            admin_user = db_crud.create_user(db, username="admin", email=None, password="adminpass", tenant_id=0)
            db_crud.assign_role_to_user(db, admin_user.id, "admin")
    finally:
        db.close()
    
    yield
    
    # Cancel the task on shutdown
    cleanup_task.cancel()


app = FastAPI(title="Legit.ai API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(
    RateLimitMiddleware, requests_per_minute=config.RATE_LIMIT_PER_MINUTE
)

# Auth is disabled
def auth_dependency():
    pass

# Dependency to extract tenant information from the JWT payload
async def get_current_tenant(request: Request, db: Session = Depends(get_db)) -> Tenant:
    """Extract tenant_id from JWT payload and return the tenant object."""
    payload = getattr(request.state, "user", None)
    if not payload or "tenant_id" not in payload:
        raise HTTPException(status_code=401, detail="Tenant information not found in token")

    tenant_id = int(payload["tenant_id"])
    # In a real app, you might fetch the tenant from DB based on tenant_id
    # For now, we'll assume tenant exists if ID is present in token
    # tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    # if not tenant:
    #     raise HTTPException(status_code=404, detail=f"Tenant with ID {tenant_id} not found")

    # Mock tenant object for now
    mock_tenant = Tenant(id=tenant_id, name=f"Tenant-{tenant_id}")
    return mock_tenant




@app.get("/")
def read_root():
    return {"message": "Legit.ai API is running"}


@app.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(
        status="ok",
        text_model_loaded=is_text_model_loaded(),
        image_model_loaded=is_image_model_loaded(),
        image_ai_model_loaded=is_ai_image_model_loaded(),
        enhanced_text_model_loaded=is_enhanced_model_loaded(),
        audio_model_loaded=is_audio_model_loaded(),
        zero_shot_model_loaded=is_zero_shot_model_loaded(),
        gemini_configured=bool(config.GEMINI_API_KEY),
        use_llm=config.USE_LLM,
        cache_enabled=config.CACHE_ENABLED,
        rate_limit_per_minute=config.RATE_LIMIT_PER_MINUTE,
    )


@app.get("/settings", response_model=AppSettings)
def get_settings(db: Session = Depends(get_db)):
    threshold = crud.get_confidence_threshold(db)
    use_llm_raw = crud.get_config_value(db, "use_llm", str(config.USE_LLM).lower())
    return AppSettings(
        confidence_threshold=threshold,
        use_llm=use_llm_raw.lower() in ("true", "1", "yes"),
    )


@app.patch("/settings", response_model=AppSettings)
def update_settings(payload: AppSettings, db: Session = Depends(get_db)):
    crud.set_config_value(db, "confidence_threshold", str(payload.confidence_threshold))
    if payload.use_llm is not None:
        crud.set_config_value(db, "use_llm", str(payload.use_llm).lower())
        config.USE_LLM = payload.use_llm
    return get_settings(db)


@app.post("/detect/text", response_model=DetectionResult)
def detect_text(request: TextDetectionRequest, db: Session = Depends(get_db), req: Request = None):
    try:
        # prefer X-Tenant-Id header; default to 0 if not provided
        tenant_id = 0
        try:
            tenant_hdr = req.headers.get('x-tenant-id') if req else None
            if tenant_hdr:
                tenant_id = int(tenant_hdr)
        except Exception:
            tenant_id = 0
        return detection_service.detect_text_content(
            db,
            request.text,
            tenant_id=tenant_id,
            source=request.source,
            confidence_threshold=request.confidence_threshold,
        )
    except TimeoutError as exc:
        raise HTTPException(status_code=504, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/detect/url", response_model=DetectionResult)
def detect_url(request: UrlDetectionRequest, db: Session = Depends(get_db), req: Request = None):
    try:
        tenant_id = 0
        try:
            tenant_hdr = req.headers.get('x-tenant-id') if req else None
            if tenant_hdr:
                tenant_id = int(tenant_hdr)
        except Exception:
            tenant_id = 0
        return detection_service.detect_url_content(
            db,
            request.url,
            tenant_id=tenant_id,
            confidence_threshold=request.confidence_threshold,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except TimeoutError as exc:
        raise HTTPException(status_code=504, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/detect/text/batch", response_model=BatchDetectionResponse)
def detect_text_batch(request: BatchTextRequest, db: Session = Depends(get_db), req: Request = None):
    results: list[DetectionResult] = []
    for i, text in enumerate(request.texts):
        text = text.strip()
        if not text:
            continue
        try:
            tenant_id = 0
            try:
                tenant_hdr = req.headers.get('x-tenant-id') if req else None
                if tenant_hdr:
                    tenant_id = int(tenant_hdr)
            except Exception:
                tenant_id = 0
            r = detection_service.detect_text_content(
                db,
                text,
                tenant_id=tenant_id,
                source=request.source or f"batch-{i + 1}",
                confidence_threshold=request.confidence_threshold,
            )
            results.append(r)
        except TimeoutError:
            raise HTTPException(
                status_code=504,
                detail=f"Batch item {i + 1} timed out",
            )
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Batch item {i + 1} failed: {exc}",
            ) from exc
    if not results:
        raise HTTPException(status_code=400, detail="No non-empty texts provided")
    return BatchDetectionResponse(results=results, total=len(results))


@app.post("/detect/image", response_model=DetectionResult)
async def detect_image(
    file: UploadFile = File(...),
    confidence_threshold: float | None = Query(None, ge=0, le=100),
    db: Session = Depends(get_db),
    req: Request = None,
):
    if file.content_type not in config.ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported image type: {file.content_type}",
        )
    data = await file.read()
    if len(data) > config.MAX_IMAGE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"Image exceeds max size of {config.MAX_IMAGE_BYTES} bytes",
        )
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")

    try:
        tenant_id = 0
        try:
            tenant_hdr = req.headers.get('x-tenant-id') if req else None
            if tenant_hdr:
                tenant_id = int(tenant_hdr)
        except Exception:
            tenant_id = 0
        return detection_service.detect_image_content(
            db,
            data,
            file.filename,
            tenant_id=tenant_id,
            confidence_threshold=confidence_threshold,
        )
    except TimeoutError as exc:
        raise HTTPException(status_code=504, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/detect/audio", response_model=DetectionResult)
async def detect_audio(
    file: UploadFile = File(...),
    confidence_threshold: float | None = Query(None, ge=0, le=100),
    db: Session = Depends(get_db),
    req: Request = None,
):
    """Detect AI-generated or deepfake audio content."""
    allowed_audio_types = {"audio/wav", "audio/mpeg", "audio/mp3", "audio/ogg", "audio/flac"}
    if file.content_type not in allowed_audio_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported audio type: {file.content_type}",
        )

    data = await file.read()
    max_audio_bytes = int(config.MAX_IMAGE_BYTES * 10)  # Allow larger audio files
    if len(data) > max_audio_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"Audio exceeds max size of {max_audio_bytes} bytes",
        )
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")

    try:
        tenant_id = 0
        try:
            tenant_hdr = req.headers.get('x-tenant-id') if req else None
            if tenant_hdr:
                tenant_id = int(tenant_hdr)
        except Exception:
            tenant_id = 0
        return detection_service.detect_audio_content(
            db,
            data,
            file.filename,
            tenant_id=tenant_id,
            confidence_threshold=confidence_threshold,
        )
    except TimeoutError as exc:
        raise HTTPException(status_code=504, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/detect/video", response_model=DetectionResult)
async def detect_video(
    file: UploadFile = File(...),
    confidence_threshold: float | None = Query(None, ge=0, le=100),
    db: Session = Depends(get_db),
    req: Request = None,
):
    """Detect AI-generated or manipulated content in video by analyzing frames."""
    allowed_video_types = {"video/mp4", "video/avi", "video/mov", "video/webm", "video/mkv"}
    if file.content_type not in allowed_video_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported video type: {file.content_type}",
        )

    data = await file.read()
    max_video_bytes = int(config.MAX_IMAGE_BYTES * 50)  # Allow larger video files
    if len(data) > max_video_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"Video exceeds max size of {max_video_bytes} bytes",
        )
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")

    try:
        tenant_id = 0
        try:
            tenant_hdr = req.headers.get('x-tenant-id') if req else None
            if tenant_hdr:
                tenant_id = int(tenant_hdr)
        except Exception:
            tenant_id = 0
        return detection_service.detect_video_content(
            db,
            data,
            file.filename,
            tenant_id=tenant_id,
            confidence_threshold=confidence_threshold,
        )
    except TimeoutError as exc:
        raise HTTPException(status_code=504, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/detect/document", response_model=DetectionResult)
async def detect_document(
    file: UploadFile = File(...),
    confidence_threshold: float | None = Query(None, ge=0, le=100),
    db: Session = Depends(get_db),
    req: Request = None,
):
    """Detect misinformation in documents (PDF, DOCX, TXT) by extracting and analyzing text."""
    allowed_document_types = {
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain",
        "application/msword",
    }
    if file.content_type not in allowed_document_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported document type: {file.content_type}",
        )

    data = await file.read()
    max_document_bytes = int(config.MAX_IMAGE_BYTES * 20)  # Allow larger document files
    if len(data) > max_document_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"Document exceeds max size of {max_document_bytes} bytes",
        )
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")

    try:
        tenant_id = 0
        try:
            tenant_hdr = req.headers.get('x-tenant-id') if req else None
            if tenant_hdr:
                tenant_id = int(tenant_hdr)
        except Exception:
            tenant_id = 0
        return detection_service.detect_document_content(
            db,
            data,
            file.filename,
            tenant_id=tenant_id,
            confidence_threshold=confidence_threshold,
        )
    except TimeoutError as exc:
        raise HTTPException(status_code=504, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/history", response_model=HistoryResponse)
def history(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    fake_only: bool | None = None,
    type: str | None = None,
    db: Session = Depends(get_db),
    req: Request = None,
):
    tenant_id = 0
    try:
        tenant_hdr = req.headers.get('x-tenant-id') if req else None
        if tenant_hdr:
            tenant_id = int(tenant_hdr)
    except Exception:
        tenant_id = 0
    items, total = crud.list_detections(db, tenant_id=tenant_id, skip=skip, limit=limit, fake_only=fake_only, type_=type)
    return HistoryResponse(
        items=[DetectionRecord.model_validate(i) for i in items],
        total=total,
    )


@app.get("/history/export")
def export_history(
    format: str = Query("json", pattern="^(json|csv)$"),
    limit: int = Query(1000, ge=1, le=5000),
    db: Session = Depends(get_db),
    req: Request = None,
):
    tenant_id = 0
    try:
        tenant_hdr = req.headers.get('x-tenant-id') if req else None
        if tenant_hdr:
            tenant_id = int(tenant_hdr)
    except Exception:
        tenant_id = 0
    items = crud.export_detections(db, limit=limit, tenant_id=tenant_id)
    if format == "csv":
        return PlainTextResponse(
            crud.detections_to_csv(items),
            media_type="text/csv",
            headers={
                "Content-Disposition": 'attachment; filename="legitai-history.csv"'
            },
        )
    return Response(
        content=crud.detections_to_json(items),
        media_type="application/json",
        headers={
            "Content-Disposition": 'attachment; filename="legitai-history.json"'
        },
    )


@app.get("/stats", response_model=StatsResponse)
def stats(db: Session = Depends(get_db), req: Request = None):
    tenant_id = 0
    try:
        tenant_hdr = req.headers.get('x-tenant-id') if req else None
        if tenant_hdr:
            tenant_id = int(tenant_hdr)
    except Exception:
        tenant_id = 0
    return StatsResponse(**crud.get_stats(db, tenant_id=tenant_id))

app.include_router(auth.router, prefix="/auth", tags=["auth"])
from api.routers import trainer
app.include_router(trainer.router, prefix="/trainers", tags=["trainers"])
app.include_router(ml_pipeline.router, prefix="/ml_pipeline", tags=["ml_pipeline"])
app.include_router(xai_router, prefix="/xai", tags=["xai"])
