import csv
import io
import json
from datetime import datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from passlib.context import CryptContext

from db.models import AppConfig, Detection


def get_config_value(db: Session, key: str, default: str) -> str:
    row = db.query(AppConfig).filter(AppConfig.key == key).first()
    return row.value if row else default


def set_config_value(db: Session, key: str, value: str) -> None:
    row = db.query(AppConfig).filter(AppConfig.key == key).first()
    if row:
        row.value = value
    else:
        db.add(AppConfig(key=key, value=value))
    db.commit()


def get_confidence_threshold(db: Session) -> float:
    import config

    raw = get_config_value(
        db, "confidence_threshold", str(config.DEFAULT_CONFIDENCE_THRESHOLD)
    )
    try:
        return float(raw)
    except ValueError:
        return config.DEFAULT_CONFIDENCE_THRESHOLD


def create_detection(
    db: Session,
    *,
    tenant_id: int,
    type_: str,
    content_preview: str,
    fake: bool,
    confidence: float,
    reason: str,
    model: str,
    source: str | None = None,
    filename: str | None = None,
    content_hash: str | None = None,
    latency_ms: float | None = None,
    cached: bool = False,
    emotion: str | None = None,
    emotion_confidence: float | None = None,
) -> Detection:
    row = Detection(
        tenant_id=tenant_id,
        type=type_,
        content_preview=content_preview[:500],
        content_hash=content_hash,
        fake=fake,
        confidence=confidence,
        reason=reason,
        model=model,
        source=source,
        filename=filename,
        latency_ms=latency_ms,
        cached=cached,
        emotion=emotion,
        emotion_confidence=emotion_confidence,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def get_cached_detection(
    db: Session, content_hash: str, ttl_hours: int, tenant_id: int | None = None
) -> Detection | None:
    cutoff = datetime.utcnow() - timedelta(hours=ttl_hours)
    q = db.query(Detection).filter(Detection.content_hash == content_hash, Detection.created_at >= cutoff)
    if tenant_id is not None:
        q = q.filter(Detection.tenant_id == tenant_id)
    return q.order_by(Detection.created_at.desc()).first()


def list_detections(
    db: Session,
    *,
    tenant_id: int | None = None,
    skip: int = 0,
    limit: int = 50,
    fake_only: bool | None = None,
    type_: str | None = None,
) -> tuple[list[Detection], int]:
    q = db.query(Detection)
    if fake_only is not None:
        q = q.filter(Detection.fake == fake_only)
    if type_:
        q = q.filter(Detection.type == type_)
    if tenant_id is not None:
        q = q.filter(Detection.tenant_id == tenant_id)
    total = q.count()
    items = (
        q.order_by(Detection.created_at.desc()).offset(skip).limit(limit).all()
    )
    return items, total


def export_detections(db: Session, limit: int = 5000, tenant_id: int | None = None) -> list[Detection]:
    q = db.query(Detection).order_by(Detection.created_at.desc())
    if tenant_id is not None:
        q = q.filter(Detection.tenant_id == tenant_id)
    return q.limit(limit).all()


def delete_old_detections(db: Session, hours: int = 24) -> int:
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    deleted_count = db.query(Detection).filter(Detection.created_at < cutoff).delete(synchronize_session=False)
    db.commit()
    return deleted_count


def get_stats(db: Session, tenant_id: int | None = None) -> dict:
    today_start = datetime.utcnow().replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    q = db.query(func.count(Detection.id)).filter(Detection.created_at >= today_start)
    if tenant_id is not None:
        q = q.filter(Detection.tenant_id == tenant_id)
    scanned_today = q.scalar() or 0
    qt = db.query(func.count(Detection.id)).filter(Detection.fake.is_(True))
    qd = db.query(func.count(Detection.id)).filter(Detection.fake.is_(True), Detection.created_at >= today_start)
    if tenant_id is not None:
        qt = qt.filter(Detection.tenant_id == tenant_id)
        qd = qd.filter(Detection.tenant_id == tenant_id)
    threats_total = qt.scalar() or 0
    threats_today = qd.scalar() or 0
    total_q = db.query(func.count(Detection.id))
    if tenant_id is not None:
        total_q = total_q.filter(Detection.tenant_id == tenant_id)
    total = total_q.scalar() or 0
    fake_rate = (threats_total / total * 100) if total else 0.0
    cache_q = db.query(func.count(Detection.id)).filter(Detection.cached.is_(True))
    if tenant_id is not None:
        cache_q = cache_q.filter(Detection.tenant_id == tenant_id)
    cache_hits = cache_q.scalar() or 0

    by_type_q = db.query(Detection.type, func.count(Detection.id)).group_by(Detection.type)
    if tenant_id is not None:
        by_type_q = by_type_q.filter(Detection.tenant_id == tenant_id)
    by_type_rows = by_type_q.all()
    by_type = {row[0]: row[1] for row in by_type_rows}

    week_start = today_start - timedelta(days=7)
    recent_q = db.query(func.count(Detection.id)).filter(Detection.created_at >= week_start)
    if tenant_id is not None:
        recent_q = recent_q.filter(Detection.tenant_id == tenant_id)
    recent_count = recent_q.scalar() or 0

    return {
        "scanned_today": scanned_today,
        "threats_total": threats_total,
        "threats_today": threats_today,
        "fake_rate_percent": round(fake_rate, 2),
        "recent_count": recent_count,
        "by_type": by_type,
        "cache_hits": cache_hits,
    }


def detections_to_json(items: list[Detection]) -> str:
    payload = [
        {
            "id": d.id,
            "type": d.type,
            "content_preview": d.content_preview,
            "fake": d.fake,
            "confidence": d.confidence,
            "reason": d.reason,
            "model": d.model,
            "source": d.source,
            "filename": d.filename,
            "latency_ms": d.latency_ms,
            "cached": d.cached,
            "emotion": d.emotion,
            "emotion_confidence": d.emotion_confidence,
            "created_at": d.created_at.isoformat(),
        }
        for d in items
    ]
    return json.dumps(payload, indent=2)


def detections_to_csv(items: list[Detection]) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(
        [
            "id",
            "type",
            "content_preview",
            "fake",
            "confidence",
            "reason",
            "model",
            "source",
            "filename",
            "latency_ms",
            "cached",
            "emotion",
            "emotion_confidence",
            "created_at",
        ]
    )
    for d in items:
        writer.writerow(
            [
                d.id,
                d.type,
                d.content_preview,
                d.fake,
                d.confidence,
                d.reason,
                d.model,
                d.source or "",
                d.filename or "",
                d.latency_ms or "",
                d.cached,
                d.emotion or "",
                d.emotion_confidence or "",
                d.created_at.isoformat(),
            ]
        )
    return buf.getvalue()


# --- User helpers (basic, synchronous) ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_user_by_username(db: Session, username: str):
    from db.user import User

    return db.query(User).filter(User.username == username).first()


def get_user_by_id(db: Session, user_id: int):
    from db.user import User

    return db.query(User).filter(User.id == user_id).first()


def create_user(db: Session, username: str, email: str | None, password: str, tenant_id: int):
    from db.user import User

    password_hash = pwd_context.hash(password)
    user = User(username=username, email=email, password_hash=password_hash, tenant_id=tenant_id)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False


# --- Refresh token helpers ---
import secrets


def create_refresh_token(db: Session, user_id: int, expires_days: int = 30) -> str:
    from db.user import RefreshToken

    token = secrets.token_urlsafe(64)
    token_hash = pwd_context.hash(token)
    issued = datetime.utcnow()
    expires = issued + timedelta(days=expires_days)
    row = RefreshToken(
        user_id=user_id,
        token_hash=token_hash,
        revoked=False,
        issued_at=issued.isoformat(),
        expires_at=expires.isoformat(),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return token


def _verify_refresh_token_row(row, token_plain: str) -> bool:
    if not row or row.revoked:
        return False
    try:
        if not pwd_context.verify(token_plain, row.token_hash):
            return False
    except Exception:
        return False
    # check expiry
    try:
        exp = datetime.fromisoformat(row.expires_at)
        if datetime.utcnow() > exp:
            return False
    except Exception:
        return False
    return True


def get_refresh_token_by_plain(db: Session, token_plain: str):
    from db.user import RefreshToken

    # naive search: iterate tokens and verify. OK for demo/smaller scale.
    rows = db.query(RefreshToken).filter(RefreshToken.revoked.is_(False)).all()
    for r in rows:
        if _verify_refresh_token_row(r, token_plain):
            return r
    return None


def create_refresh_token_with_meta(db: Session, user_id: int, ip: str | None = None, user_agent: str | None = None, expires_days: int = 30) -> str:
    from db.user import RefreshToken

    token = secrets.token_urlsafe(64)
    token_hash = pwd_context.hash(token)
    issued = datetime.utcnow()
    expires = issued + timedelta(days=expires_days)
    row = RefreshToken(
        user_id=user_id,
        token_hash=token_hash,
        revoked=False,
        issued_at=issued.isoformat(),
        expires_at=expires.isoformat(),
        ip_address=ip,
        user_agent=(user_agent[:512] if user_agent else None),
        last_used_at=None,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return token


def list_user_refresh_tokens(db: Session, user_id: int):
    from db.user import RefreshToken

    rows = (
        db.query(RefreshToken).filter(RefreshToken.user_id == user_id).order_by(RefreshToken.issued_at.desc()).all()
    )
    return rows


def revoke_refresh_token_by_id(db: Session, token_id: int) -> bool:
    from db.user import RefreshToken

    row = db.query(RefreshToken).filter(RefreshToken.id == token_id).first()
    if not row:
        return False
    row.revoked = True
    db.commit()
    return True


def touch_refresh_token(db: Session, token_row, used_at: datetime | None = None):
    if used_at is None:
        used_at = datetime.utcnow()
    token_row.last_used_at = used_at.isoformat()
    db.commit()


def revoke_refresh_token(db: Session, token_plain: str) -> bool:
    row = get_refresh_token_by_plain(db, token_plain)
    if not row:
        return False
    row.revoked = True
    db.commit()
    return True


def revoke_all_user_refresh_tokens(db: Session, user_id: int) -> int:
    from db.user import RefreshToken

    rows = db.query(RefreshToken).filter(RefreshToken.user_id == user_id, RefreshToken.revoked.is_(False)).all()
    count = 0
    for r in rows:
        r.revoked = True
        count += 1
    db.commit()
    return count


def rotate_refresh_token(db: Session, old_token_plain: str, user_id: int) -> str | None:
    ok = revoke_refresh_token(db, old_token_plain)
    if not ok:
        return None
    return create_refresh_token(db, user_id)


def create_email_verification_token(db: Session, user_id: int, expires_hours: int = 24) -> str:
    from db.user import EmailVerification

    token = secrets.token_urlsafe(32)
    token_hash = pwd_context.hash(token)
    issued = datetime.utcnow()
    expires = issued + timedelta(hours=expires_hours)
    row = EmailVerification(
        user_id=user_id,
        token_hash=token_hash,
        used=False,
        issued_at=issued.isoformat(),
        expires_at=expires.isoformat(),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return token


def verify_email_token(db: Session, token_plain: str) -> int | None:
    from db.user import EmailVerification, User

    rows = db.query(EmailVerification).filter(EmailVerification.used.is_(False)).all()
    for r in rows:
        try:
            if not pwd_context.verify(token_plain, r.token_hash):
                continue
        except Exception:
            continue
        # check expiry
        try:
            exp = datetime.fromisoformat(r.expires_at)
            if datetime.utcnow() > exp:
                return None
        except Exception:
            return None
        # mark used and set user's email_verified
        r.used = True
        user = db.query(User).filter(User.id == r.user_id).first()
        if user:
            user.email_verified = True
        db.commit()
        return r.user_id
    return None


def create_role(db: Session, name: str):
    from db.user import Role

    row = db.query(Role).filter(Role.name == name).first()
    if row:
        return row
    row = Role(name=name)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def assign_role_to_user(db: Session, user_id: int, role_name: str):
    from db.user import Role, UserRole

    role = db.query(Role).filter(Role.name == role_name).first()
    if not role:
        role = create_role(db, role_name)
    exists = db.query(UserRole).filter(UserRole.user_id == user_id, UserRole.role_id == role.id).first()
    if exists:
        return exists
    ur = UserRole(user_id=user_id, role_id=role.id)
    db.add(ur)
    db.commit()
    db.refresh(ur)
    return ur


def get_roles_for_user(db: Session, user_id: int) -> list[str]:
    from db.user import Role, UserRole

    rows = (
        db.query(Role.name)
        .join(UserRole, UserRole.role_id == Role.id)
        .filter(UserRole.user_id == user_id)
        .all()
    )
    return [r[0] for r in rows]


def list_roles(db: Session) -> list[str]:
    from db.user import Role

    return [r.name for r in db.query(Role).all()]


# --- Job persistence helpers ---
def create_job(db: Session, job_id: str, user_id: int, tenant_id: int, status: str = "queued", progress: int = 0):
    try:
        from db.models import Job
    except Exception:
        # Lazy import if file moved
        from db.models import Job
    row = Job(job_id=job_id, user_id=user_id, tenant_id=tenant_id, status=status, progress=progress)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def update_job_status(db: Session, job_id: str, status: str | None = None, progress: int | None = None, result: dict | None = None):
    from db.models import Job

    row = db.query(Job).filter(Job.job_id == job_id).first()
    if not row:
        return None
    if status is not None:
        row.status = status
    if progress is not None:
        row.progress = int(progress)
    if result is not None:
        import json

        row.result = json.dumps(result)
    from datetime import datetime

    row.updated_at = datetime.utcnow().isoformat()
    db.commit()
    db.refresh(row)
    return row


def get_job_by_job_id(db: Session, job_id: str):
    from db.models import Job

    return db.query(Job).filter(Job.job_id == job_id).first()


def list_jobs_for_user(db: Session, user_id: int):
    from db.models import Job

    return db.query(Job).filter(Job.user_id == user_id).order_by(Job.created_at.desc()).all()

