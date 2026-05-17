# web/back_end/services/notification_service.py

from source.database.queries import (
    get_notifications,
    get_unread_notification_count,
    mark_notification_read,
)


async def get_notifications_data():
    """
    Ambil semua notifikasi
    urutan terbaru → terlama
    """

    rows = await get_notifications()

    result = []

    for n in rows:
        result.append(
            {
                "id": n[0],
                "type": n[1],
                "title": n[2],
                "message": n[3],
                "page": n[4],
                "tab": n[5],
                "related_id": n[6],
                "is_read": bool(n[7]),
                "created_at": n[8],
            }
        )

    return result


async def get_notification_badge():
    """
    Ambil jumlah notif belum dibaca
    untuk badge 🔔
    """

    total = await get_unread_notification_count()

    return total


async def read_notification(notif_id):
    """
    Tandai notif sudah dibaca
    """

    await mark_notification_read(notif_id)

    return {"success": True}
