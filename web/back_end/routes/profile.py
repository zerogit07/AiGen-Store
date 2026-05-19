from fastapi import APIRouter, Depends
from web.back_end.services.auth_service import get_current_admin
from web.back_end.services.profile_service import get_admin_profile

router = APIRouter(prefix="/api", tags=["profile"], dependencies=[Depends(get_current_admin)])

@router.get("/profile")
async def api_profile():
    return await get_admin_profile()
