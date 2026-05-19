# web/back_end/routes/home.py
from fastapi import APIRouter
from web.back_end.services.home_service import get_home_data

router = APIRouter(prefix="/api", tags=["home"])

@router.get("/home")
async def api_home():
    return await get_home_data()