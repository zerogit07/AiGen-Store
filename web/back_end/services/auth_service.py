from fastapi import HTTPException, Request, Response
from source.config import DASHBOARD_USER, DASHBOARD_PASS
import secrets

# In-memory session store
sessions = {}

async def check_credentials(user, password):
    if user != DASHBOARD_USER:
        return "username"
    if password != DASHBOARD_PASS:
        return "password"
    token = secrets.token_hex(32)
    sessions[token] = True
    return token

def logout_session(token):
    if token in sessions:
        del sessions[token]

async def get_current_admin(request: Request):
    token = request.cookies.get("admin_token")
    if not token or token not in sessions:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return True
