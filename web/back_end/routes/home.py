# web/back_end/routes/home.py

from fastapi import APIRouter
from pydantic import BaseModel

from web.back_end.services.home_service import (
    get_home_data,
    get_home_users,
    get_home_report,
    get_user_modal,
    change_user_status,
)

router = APIRouter(prefix="/api", tags=["home"])


class UserStatusRequest(BaseModel):
    user_id: int
    status: int


@router.get("/home")
async def api_home(month: str = ""):
    return await get_home_data(month)


@router.get("/home/users")
async def api_users(page: int = 1, search: str = ""):
    return await get_home_users(page, search)


@router.get("/home/user-detail")
async def api_user_detail(user_id: int):
    return await get_user_modal(user_id)


@router.post("/home/user-status")
async def api_user_status(data: UserStatusRequest):
    return await change_user_status(data.user_id, data.status)


@router.get("/home/report")
async def api_report(
    page: int = 1,
    filter_type: str = "",
    custom_type: str = "",
    start_date: str = "",
    end_date: str = "",
):
    return await get_home_report(page, filter_type, custom_type, start_date, end_date)
