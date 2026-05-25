from typing import Callable, Optional

from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .jwt import decode_token


class JWTAuth:
    scheme = HTTPBearer()

    def __init__(self, get_user: Optional[Callable] = None):
        self.get_user = get_user

    async def __call__(self, request: Request):
        token = None
        # Prefer Authorization header; fallback to cookie 'access_token'
        try:
            credentials: HTTPAuthorizationCredentials = await self.scheme.__call__(request)
            token = credentials.credentials
        except Exception:
            token = request.cookies.get("access_token")

        payload = decode_token(token) if token else None
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid authentication token")
        request.state.user = payload
        return payload
