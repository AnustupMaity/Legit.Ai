from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from db.database import get_db
from db.user import User
from db.tenant import Tenant

# Auth is disabled per user request
def auth_dependency():
    pass


def get_current_tenant(request: Request, db: Session = Depends(get_db)) -> Tenant:
    """Mock tenant resolution since auth is disabled."""
    tenant = db.query(Tenant).filter(Tenant.id == 1).first()
    if not tenant:
        tenant = Tenant(id=1, name="Default Tenant")
        db.add(tenant)
        db.commit()
    request.state.tenant = tenant
    return tenant


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """Mock user resolution since auth is disabled."""
    user = db.query(User).filter(User.id == 1).first()
    if not user:
        user = User(id=1, username="admin", email="admin@legit.ai", password_hash="mock", tenant_id=1, active=True)
        db.add(user)
        db.commit()
    return user
