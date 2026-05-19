# web/back_end/routes/notification.py

from fastapi import APIRouter
from web.back_end.services.notification_service import (
    get_notifications_data,
    get_notification_badge,
    read_notification,
)

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("")
async def notifications():
    """
    List notif
    """
    return await get_notifications_data()


@router.get("/badge")
async def notification_badge():

    """
    Jumlah badge
    """

    count = await get_notification_badge()

    return {
        "count": count
    }


@router.post("/read/{notif_id}")
async def notification_read(notif_id: int):
    """
    Baca notif
    """
    return await read_notification(notif_id)
