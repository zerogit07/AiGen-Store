from fastapi import APIRouter, Form, UploadFile, File
from web.back_end.services.settings_service import get_settings, update_auto_delete, upload_banner, upload_qris
from source.database.admin import set_config

router = APIRouter(prefix="/api/settings", tags=["settings"])

@router.get("")
async def api_get_settings():
    return await get_settings()

@router.post("/auto-delete")
async def api_auto_delete(days: int = Form(...)):
    return await update_auto_delete(days)

@router.delete("/banner")
async def api_delete_banner():
    await set_config("banner_image_file_id", "")
    return {"success": True, "message": "Banner dihapus."}

@router.delete("/qris")
async def api_delete_qris():
    await set_config("qris_image_file_id", "")
    return {"success": True, "message": "QRIS dihapus."}

@router.post("/banner")
async def api_upload_banner(file: UploadFile = File(...)):
    content = await file.read()
    return await upload_banner(content, file.filename)

@router.post("/qris")
async def api_upload_qris(file: UploadFile = File(...)):
    content = await file.read()
    return await upload_qris(content, file.filename)
    
# ── Manual Delete ──
@router.post("/manual-delete")
async def api_manual_delete():
    from source.database.products import get_used_items_count, delete_all_used_items
    count = await get_used_items_count()
    if count == 0:
        return {"success": False, "message": "Tidak ada item terpakai."}
    deleted = await delete_all_used_items()
    return {"success": True, "message": f"{deleted} item terpakai dihapus."}

@router.get("/manual-delete/count")
async def api_manual_delete_count():
    from source.database.products import get_used_items_count
    count = await get_used_items_count()
    return {"count": count}

