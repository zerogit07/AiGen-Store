# web/back_end/services/settings_service.py
import aiohttp
from source.database.admin import get_config, set_config
from source.config import BOT_TOKEN, ADMIN_ID   # ← tambahkan ADMIN_ID

async def get_settings():
    banner = await get_config("banner_image_file_id") or ""
    qris = await get_config("qris_image_file_id") or ""
    auto_delete = await get_config("auto_delete_used_days") or "7"
    return {
        "banner": banner,
        "qris": qris,
        "auto_delete_days": auto_delete
    }

async def delete_banner():
    await set_config("banner_image_file_id", "")
    return {"success": True, "message": "Banner dihapus."}

async def delete_qris():
    await set_config("qris_image_file_id", "")
    return {"success": True, "message": "QRIS dihapus."}

async def upload_banner(file_bytes: bytes, filename: str):
    return await _upload_photo_to_telegram(file_bytes, filename, "banner_image_file_id", "Banner")

async def upload_qris(file_bytes: bytes, filename: str):
    return await _upload_photo_to_telegram(file_bytes, filename, "qris_image_file_id", "QRIS")

async def update_auto_delete(days: int):
    if days < 0:
        return {"success": False, "message": "Angka harus positif (0 untuk nonaktif)."}
    await set_config("auto_delete_used_days", str(days))
    return {"success": True, "message": f"Auto delete diatur ke {days} hari."}

async def _upload_photo_to_telegram(file_bytes: bytes, filename: str, config_key: str, label: str):
    """Unggah foto ke Telegram via Bot API, dapatkan file_id, simpan ke database."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    data = aiohttp.FormData()
    data.add_field("photo", file_bytes, filename=filename)
    data.add_field("chat_id", str(ADMIN_ID))

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=data) as resp:
                result = await resp.json()
                if result.get("ok"):
                    # Ambil foto dengan ukuran terbesar
                    photos = result["result"]["photo"]
                    file_id = photos[-1]["file_id"]
                    await set_config(config_key, file_id)
                    return {"success": True, "message": f"{label} berhasil diunggah."}
                else:
                    return {"success": False, "message": f"Gagal upload: {result.get('description')}"}
    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}