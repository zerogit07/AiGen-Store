from fastapi import APIRouter
from web.back_end.services.profile_service import get_admin_profile

router = APIRouter(prefix="/api", tags=["profile"])

@router.get("/profile")
async def api_profile():
    return await get_admin_profile()
