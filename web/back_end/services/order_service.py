import asyncio
import logging
from aiogram import Bot
from aiogram.enums import ParseMode
from source.config import BOT_TOKEN
from source.database.queries import (
    get_incoming_orders, get_orders_by_status, get_order_by_id,
    get_available_item, mark_item_used, update_order_status,
    get_order_details, delete_orders_by_status, get_riwayat_orders,
    get_item_subcategory, get_order_details_by_item_id
)
from source.utils.helpers import format_rupiah

bot = Bot(token=BOT_TOKEN)
logger = logging.getLogger("order_service")

async def fetch_orders(status=None, limit=10, offset=0):
    if status == 'incoming':
        orders, total = await get_incoming_orders(limit=limit, offset=offset)
    elif status == 'history':
        orders, total = await get_riwayat_orders(status=None, limit=limit, offset=offset)
        if orders:
            logger.info(f"DEBUG order[0]: {orders[0]}")
    else:
        orders, total = await get_orders_by_status(status, limit=limit, offset=offset)
    return {"data": await _format_orders(orders), "total": total}

async def approve_order_service(order_id: str):
    order = await get_order_by_id(order_id)
    if not order or order[7] != 'pending':
        return {"success": False, "message": "Pesanan tidak valid."}
    item_id = order[2]
    sub_id = await get_item_subcategory(item_id)
    qty = order[3] 
    user_id = order[1]
    item_ids, codes = [], []
    for _ in range(qty):
        items = await get_available_item(sub_id, 1)
        if not items:
            return {"success": False, "message": f"Stok tidak cukup (butuh {qty}, baru {len(codes)})."}
        item_ids.append(items[0][0])
        codes.append(items[0][1])
        await mark_item_used(items[0][0], order_id)
    await update_order_status(order_id, 'approved')
    try:
        codes_text = "\n".join(f"`{c}`" for c in codes)
        await bot.send_message(user_id, f"✅ Pesanan {order_id} disetujui!\nKode Anda:\n{codes_text}", parse_mode=ParseMode.MARKDOWN)
    except Exception: 
        pass
    return {"success": True, "message": f"Disetujui. {qty} kode dikirim."}

async def reject_order_service(order_id: str):
    order = await get_order_by_id(order_id)
    if not order or order[7] != 'pending':
        return {"success": False, "message": "Pesanan tidak valid."}
    await update_order_status(order_id, 'rejected')
    try:
        await bot.send_message(order[1], f"❌ Pesanan {order_id} ditolak.", parse_mode=ParseMode.MARKDOWN)
    except Exception: 
        pass
    return {"success": True, "message": "Pesanan ditolak."}

async def approve_all_incoming():
    orders, _ = await get_incoming_orders(limit=1000, offset=0)
    success, failed = 0, 0
    for order in orders:
        order_id = order[0]
        res = await approve_order_service(order_id)
        if res['success']: 
            success += 1
        else: 
            failed += 1
    return {"success": True, "message": f"Bulk approve: {success} berhasil, {failed} gagal."}

async def reject_all_incoming():
    orders, _ = await get_incoming_orders(limit=1000, offset=0)
    success, failed = 0, 0
    for order in orders:
        order_id = order[0]
        res = await reject_order_service(order_id)
        if res['success']: 
            success += 1
        else: 
            failed += 1
    return {"success": True, "message": f"Bulk reject: {success} berhasil, {failed} gagal."}

async def delete_pending():
    count = await delete_orders_by_status("pending")
    return {"success": True, "message": f"{count} pesanan pending dihapus."}

async def delete_history(status=None):
    count = await delete_orders_by_status(status)
    label = status or "semua"
    return {"success": True, "message": f"{count} riwayat ({label}) dihapus."}

async def _format_orders(orders):
    result = []
    for order in orders:
        # URUTAN KOLOM DARI QUERY:
        # id(0), user_id(1), item_id(2), quantity(3), total_price(4),
        # three_digits(5), payment_proof_file_id(6), status(7)
        order_id = order[0]
        user_id = order[1]
        item_id = order[2]
        qty = order[3]
        total_price = order[4]
        payment_proof = order[6] if len(order) > 6 else None
        status = order[7] if len(order) > 7 else None
        
        logger.info(f"FORMAT: id={order_id}, status={status}, proof={payment_proof}")
        
        sub_name, cat_name = await get_order_details_by_item_id(item_id)
        result.append({
            "order_id": order_id,
            "user_id": user_id,
            "product": f"{cat_name} → {sub_name}",
            "qty": qty,
            "total": format_rupiah(total_price),
            "proof": payment_proof or "",
            "status": status.lower() if status else "unknown"
        })
    return result
