# web/routes/broadcast.py
from fastapi import APIRouter, Form
from web.back_end.services.broadcast_service import get_targets, send_broadcast

router = APIRouter(prefix="/api/broadcast", tags=["broadcast"])

@router.get("/targets")
async def api_targets():
    return await get_targets()

@router.post("/send")
async def api_send(target: str = Form(...), text: str = Form(...)):
    return await send_broadcast(target, text)