from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from db.database import get_db
import db.crud as db_crud
from api.auth.auth import JWTAuth

router = APIRouter()
jwt_auth = JWTAuth()

class TrainerCreateRequest(BaseModel):
    username: str
    password: str

class TrainerUpdateRequest(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    active: Optional[bool] = None

@router.get("/")
def list_trainers(db: Session = Depends(get_db), token_payload=Depends(jwt_auth)):
    if "admin" not in token_payload.get("roles", []):
        raise HTTPException(status_code=403, detail="Admin privileges required")
    from db.user import User
    # Return all users with role 'trainer'
    # For simplicity, we just return all users who are not admin
    rows = db.query(User).all()
    trainers = []
    for r in rows:
        roles = db_crud.get_roles_for_user(db, r.id)
        if "trainer" in roles:
            trainers.append({
                "id": str(r.id),
                "username": r.username,
                "status": "Active" if r.active else "Stalled"
            })
    return trainers

@router.post("/")
def create_trainer(req: TrainerCreateRequest, db: Session = Depends(get_db), token_payload=Depends(jwt_auth)):
    if "admin" not in token_payload.get("roles", []):
        raise HTTPException(status_code=403, detail="Admin privileges required")
    
    existing = db_crud.get_user_by_username(db, req.username)
    if existing:
        raise HTTPException(status_code=400, detail="Username already taken")
    
    new_user = db_crud.create_user(db, username=req.username, email=None, password=req.password, tenant_id=0)
    db_crud.assign_role_to_user(db, new_user.id, "trainer")
    
    return {
        "id": str(new_user.id),
        "username": new_user.username,
        "status": "Active" if new_user.active else "Stalled"
    }

@router.patch("/{trainer_id}")
def update_trainer(trainer_id: int, req: TrainerUpdateRequest, db: Session = Depends(get_db), token_payload=Depends(jwt_auth)):
    if "admin" not in token_payload.get("roles", []):
        raise HTTPException(status_code=403, detail="Admin privileges required")
    
    user = db_crud.get_user_by_id(db, trainer_id)
    if not user:
        raise HTTPException(status_code=404, detail="Trainer not found")
    
    if req.username is not None:
        user.username = req.username
    if req.password is not None:
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        user.password_hash = pwd_context.hash(req.password)
    if req.active is not None:
        user.active = req.active
        
    db.commit()
    return {
        "id": str(user.id),
        "username": user.username,
        "status": "Active" if user.active else "Stalled"
    }

@router.delete("/{trainer_id}")
def delete_trainer(trainer_id: int, db: Session = Depends(get_db), token_payload=Depends(jwt_auth)):
    if "admin" not in token_payload.get("roles", []):
        raise HTTPException(status_code=403, detail="Admin privileges required")
    
    user = db_crud.get_user_by_id(db, trainer_id)
    if not user:
        raise HTTPException(status_code=404, detail="Trainer not found")
        
    db.delete(user)
    db.commit()
    return {"status": "deleted"}
