from fastapi import (
    HTTPException,
    Request
)

from fastapi.responses import (
    JSONResponse
)

from source.config import (
    DASHBOARD_USER,
    DASHBOARD_PASS
)

import secrets


sessions = {}


async def login(
    username: str,
    password: str
):

    if username != DASHBOARD_USER:

        return {
            "success": False,
            "message": "Username salah"
        }

    if password != DASHBOARD_PASS:

        return {
            "success": False,
            "message": "Password salah"
        }

    token = secrets.token_hex(32)

    sessions[token] = True

    response = JSONResponse(
        {
            "success": True
        }
    )

    response.set_cookie(
        key="admin_token",
        value=token,
        httponly=True
    )

    return response


async def logout(
    request: Request
):

    token = request.cookies.get(
        "admin_token"
    )

    if token:

        sessions.pop(
            token,
            None
        )

    response = JSONResponse(
        {
            "success": True
        }
    )

    response.delete_cookie(
        "admin_token"
    )

    return response


async def get_current_admin(
    request: Request
):

    token = request.cookies.get(
        "admin_token"
    )

    if (
        not token
        or
        token not in sessions
    ):

        raise HTTPException(
            status_code=401,
            detail="Unauthorized"
        )

    return token