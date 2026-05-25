from fastapi import HTTPException, Security, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets
import os

security = HTTPBasic()


def admin_auth(request: Request, creds: HTTPBasicCredentials = Security(security)):
    """Allow admin access via HTTP Basic credentials.

    Env vars supported: ADMIN_BASIC_USER, ADMIN_BASIC_PASS
    """
    env_user = os.getenv("ADMIN_BASIC_USER")
    env_pass = os.getenv("ADMIN_BASIC_PASS")
    if env_user and env_pass:
        if secrets.compare_digest(creds.username, env_user) and secrets.compare_digest(creds.password, env_pass):
            return True

    raise HTTPException(status_code=401, detail="Unauthorized admin access")
