from datetime import datetime, timedelta
from typing import Optional, Dict, Any

import jwt

# Simple JWT helpers, replace with real secret management in production
JWT_SECRET = "your-secret-key"
JWT_ALGORITHM = "HS256"
JWT_EXP_DELTA_SECONDS = 3600


def create_token(user_id: int, tenant_id: int, roles: Optional[list[str]] = None, exp_seconds: int = JWT_EXP_DELTA_SECONDS) -> str:
    payload: Dict[str, Any] = {
        "sub": str(user_id),
        "tenant_id": str(tenant_id),
        "exp": datetime.utcnow() + timedelta(seconds=exp_seconds),
        "iat": datetime.utcnow(),
        "roles": roles or [],
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)  # type: ignore


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except Exception:
        return None
