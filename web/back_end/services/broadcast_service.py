# web/services/broadcast_service.py
import asyncio
from aiogram import Bot
from source.config import BOT_TOKEN
from source.database.queries import (
    get_all_user_ids,
    get_buyer_user_ids,
    get_nonbuyer_user_ids,
)

bot = Bot(token=BOT_TOKEN)

TARGET_LABELS = {
    "all": "Semua User",
    "buyers": "Pernah Beli",
    "nonbuyers": "Belum Pernah Beli"
}

async def get_targets():
    """Mengembalikan daftar target dengan jumlah user."""
    all_ids = await get_all_user_ids()
    buyer_ids = await get_buyer_user_ids()
    nonbuyer_ids = await get_nonbuyer_user_ids()

    return [
        {"key": "all", "label": TARGET_LABELS["all"], "count": len(all_ids)},
        {"key": "buyers", "label": TARGET_LABELS["buyers"], "count": len(buyer_ids)},
        {"key": "nonbuyers", "label": TARGET_LABELS["nonbuyers"], "count": len(nonbuyer_ids)},
    ]

async def send_broadcast(target: str, text: str) -> dict:
    """Mengirim broadcast ke target yang dipilih."""
    if target == "all":
        user_ids = await get_all_user_ids()
    elif target == "buyers":
        user_ids = await get_buyer_user_ids()
    elif target == "nonbuyers":
        user_ids = await get_nonbuyer_user_ids()
    else:
        return {"success": False, "message": "Target tidak valid."}

    if not user_ids:
        return {"success": False, "message": "Tidak ada user untuk target ini."}

    success, failed = 0, 0
    total = len(user_ids)

    for uid in user_ids:
        try:
            await bot.send_message(uid, text)
            success += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.05)  # hindari rate limit

    return {
        "success": True,
        "message": f"Broadcast selesai. Terkirim: {success}, Gagal: {failed}",
        "total": total,
        "sent": success,
        "failed": failed
    }