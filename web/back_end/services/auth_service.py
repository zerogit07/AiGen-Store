from fastapi import HTTPException, Request, Response
from source.config import DASHBOARD_USER, DASHBOARD_PASS
import secrets

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
    return True
