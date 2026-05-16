from fastapi import APIRouter, Query
from web.back_end.services.order_service import (
    fetch_orders, approve_order_service, reject_order_service,
    approve_all_incoming, reject_all_incoming,
    delete_pending, delete_history
)

router = APIRouter(prefix="/api/orders", tags=["orders"])

@router.get("/{tab}")
async def api_orders(tab: str, page: int = 1, limit: int = 10, filter: str = None):
    offset = (page - 1) * limit
    status_map = {
        "masuk": "incoming",
        "pending": "pending",
        "riwayat": "history"
    }
    status = status_map.get(tab)
    if tab == "riwayat" and filter:
        status = filter  # approved / rejected
    return await fetch_orders(status, limit, offset)

@router.post("/approve/{order_id}")
async def api_approve(order_id: str):
    return await approve_order_service(order_id)

@router.post("/reject/{order_id}")
async def api_reject(order_id: str):
    return await reject_order_service(order_id)

@router.post("/approve-all")
async def api_approve_all():
    return await approve_all_incoming()

@router.post("/reject-all")
async def api_reject_all():
    return await reject_all_incoming()

@router.delete("/pending")
async def api_delete_pending():
    return await delete_pending()

@router.delete("/history")
async def api_delete_history(filter: str = ""):
    # Konversi string kosong menjadi None
    filter = filter if filter else None
    return await delete_history(filter)