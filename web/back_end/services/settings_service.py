from source.database.queries import get_config, set_config

async def get_settings():
    banner = await get_config("banner_image_file_id") or ""
    qris = await get_config("qris_image_file_id") or ""
    auto_delete = await get_config("auto_delete_used_days") or "7"
    return {
        "banner": banner,
        "qris": qris,
        "auto_delete_days": auto_delete
    }

async def update_auto_delete(days: int):
    if days < 0:
        return {"success": False, "message": "Angka harus positif (0 untuk nonaktif)."}
    await set_config("auto_delete_used_days", str(days))
    return {"success": True, "message": f"Auto delete diatur ke {days} hari."}
