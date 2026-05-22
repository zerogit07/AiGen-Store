from fastapi import (
    APIRouter,
    Form,
    Request
)

from web.back_end.services.auth_service import (
    login,
    logout
)

router = APIRouter(
    prefix="/api/auth",
    tags=["auth"]
)


@router.post("/login")
async def api_login(
    username:str=Form(...),
    password:str=Form(...)
):

    return await login(
        username,
        password
    )


@router.post("/logout")
async def api_logout(
    request:Request
):

    return await logout(
        request
    )