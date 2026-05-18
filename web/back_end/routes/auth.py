from fastapi import APIRouter, Depends, Response, Form
from web.back_end.services.auth_service import check_credentials, logout_session, get_current_admin

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/login")
async def api_login(response: Response, username: str = Form(...), password: str = Form(...)):
    result = await check_credentials(username, password)
    if result == "username":
        return {"success": False, "message": "Username salah"}
    if result == "password":
        return {"success": False, "message": "Password salah"}
    
    # If success (token returned)
    response.set_cookie(key="admin_token", value=result, httponly=True)
    return {"success": True}

@router.post("/logout")
async def api_logout(response: Response, token: str = Depends(get_current_admin)):
    # Note: token extraction from cookie here is simplified for demo
    response.delete_cookie("admin_token")
    return {"success": True}
