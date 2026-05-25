from typing import List, Optional

from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from db.database import get_db
import db.crud as db_crud
from api.auth.admin_auth import admin_auth
import config


router = APIRouter()


@router.get("/me")
def me():
    # Authentication removed for user flows; /me is not applicable
    return {"status": "no_auth"}


@router.post("/admin/assign-role")
def admin_assign_role(user_id: int, role: str, db: Session = Depends(get_db), _=Depends(admin_auth)):
    # Small endpoint to assign a role to a user (intended for admin site usage)
    db_crud.assign_role_to_user(db, user_id, role)
    return {"status": "ok"}


@router.get("/admin/users")
def admin_list_users(db: Session = Depends(get_db), _=Depends(admin_auth)):
    from db.user import User

    rows = db.query(User).all()
    return [{"id": r.id, "username": r.username, "email": r.email, "tenant_id": r.tenant_id, "active": r.active} for r in rows]


@router.get("/admin/roles")
def admin_list_roles(db: Session = Depends(get_db), _=Depends(admin_auth)):
    return {"roles": db_crud.list_roles(db)}


@router.get("/csrf-token")
def csrf_token():
    import secrets

    token = secrets.token_urlsafe(16)
    # return token; client should also receive cookie from login/refresh, but provide endpoint for explicit fetch
    return {"csrf_token": token}


class TokenRequest(BaseModel):
    user_id: int
    tenant_id: int
    roles: Optional[List[str]] = None


class SignupRequest(BaseModel):
    username: str
    email: Optional[str] = None


class LoginRequest(BaseModel):
    username: str
    password: str

@router.post("/login")
def login(req: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = db_crud.get_user_by_username(db, req.username)
    if not user or not db_crud.verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    if not user.active:
        raise HTTPException(status_code=403, detail="Account is stalled")

    roles = db_crud.get_roles_for_user(db, user.id)
    
    from api.auth.jwt import create_token
    token = create_token(user_id=user.id, tenant_id=user.tenant_id, roles=roles)
    
    response.set_cookie(key="access_token", value=token, httponly=True, max_age=3600, samesite="lax")
    return {
        "access_token": token,
        "roles": roles,
        "user": {
            "id": user.id,
            "username": user.username,
            "status": "Active" if user.active else "Stalled"
        }
    }
