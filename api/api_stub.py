from fastapi import FastAPI
from api.auth.jwt import create_token

app = FastAPI(title="Legit AI API - Auth Stub")

@app.post('/token')
def token():
    return {"access_token": create_token(1, 1, ["user"]) }
