from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.async_database import Base
from db.models import AppConfig, Detection


async def async_get_config_value(db: AsyncSession, key: str, default: str) -> str:
    result = await db.execute(select(AppConfig).filter(AppConfig.key == key))
    row = result.scalar_one_or_none()
    return row.value if row else default


async def async_set_config_value(db: AsyncSession, key: str, value: str) -> None:
    result = await db.execute(select(AppConfig).filter(AppConfig.key == key))
    row = result.scalar_one_or_none()
    
    if row:
        row.value = value
    else:
        db.add(AppConfig(key=key, value=value))
    
    await db.commit()


async def async_get_confidence_threshold(db: AsyncSession) -> float:
    import config
    
    raw = await async_get_config_value(
        db, "confidence_threshold", str(config.DEFAULT_CONFIDENCE_THRESHOLD)
    )
    try:
        return float(raw)
    except ValueError:
        return config.DEFAULT_CONFIDENCE_THRESHOLD


async def async_create_detection(
    db: AsyncSession,
    *,
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
    await db.commit()
    await db.refresh(row)
    return row


async def async_get_cached_detection(
    db: AsyncSession, content_hash: str, ttl_hours: int
) -> Detection | None:
    cutoff = datetime.utcnow() - timedelta(hours=ttl_hours)
    result = await db.execute(
        select(Detection)
        .filter(
            Detection.content_hash == content_hash,
            Detection.created_at >= cutoff,
        )
        .order_by(Detection.created_at.desc())
    )
    return result.scalar_one_or_none()


async def async_list_detections(
    db: AsyncSession,
    *,
    skip: int = 0,
    limit: int = 50,
    fake_only: bool | None = None,
    type_: str | None = None,
) -> tuple[list[Detection], int]:
    query = select(Detection)
    
    if fake_only is not None:
        query = query.filter(Detection.fake == fake_only)
    if type_:
        query = query.filter(Detection.type == type_)
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Get paginated results
    query = query.order_by(Detection.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    items = result.scalars().all()
    
    return list(items), total or 0


async def async_export_detections(db: AsyncSession, limit: int = 5000) -> list[Detection]:
    query = select(Detection).order_by(Detection.created_at.desc()).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def async_get_stats(db: AsyncSession) -> dict:
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Scanned today
    scanned_today_result = await db.execute(
        select(func.count(Detection.id)).filter(Detection.created_at >= today_start)
    )
    scanned_today = scanned_today_result.scalar() or 0
    
    # Total threats
    threats_total_result = await db.execute(
        select(func.count(Detection.id)).filter(Detection.fake.is_(True))
    )
    threats_total = threats_total_result.scalar() or 0
    
    # Threats today
    threats_today_result = await db.execute(
        select(func.count(Detection.id)).filter(
            Detection.fake.is_(True), 
            Detection.created_at >= today_start
        )
    )
    threats_today = threats_today_result.scalar() or 0
    
    # Total count
    total_result = await db.execute(select(func.count(Detection.id)))
    total = total_result.scalar() or 0
    
    # Fake rate
    fake_rate = (threats_total / total * 100) if total else 0.0
    
    # Cache hits
    cache_hits_result = await db.execute(
        select(func.count(Detection.id)).filter(Detection.cached.is_(True))
    )
    cache_hits = cache_hits_result.scalar() or 0
    
    # By type
    by_type_result = await db.execute(
        select(Detection.type, func.count(Detection.id))
        .group_by(Detection.type)
    )
    by_type_rows = by_type_result.all()
    by_type = {row[0]: row[1] for row in by_type_rows}
    
    # Recent count (last 7 days)
    week_start = today_start - timedelta(days=7)
    recent_count_result = await db.execute(
        select(func.count(Detection.id)).filter(Detection.created_at >= week_start)
    )
    recent_count = recent_count_result.scalar() or 0
    
    return {
        "scanned_today": scanned_today,
        "threats_total": threats_total,
        "threats_today": threats_today,
        "fake_rate_percent": round(fake_rate, 2),
        "recent_count": recent_count,
        "by_type": by_type,
        "cache_hits": cache_hits,
    }


async def async_detections_to_json(items: list[Detection]) -> str:
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


async def async_detections_to_csv(items: list[Detection]) -> str:
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
