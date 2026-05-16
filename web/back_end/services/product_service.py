# web/back_end/services/product_service.py
import csv
import io
import aiosqlite
from source.config import DB_PATH
from source.database.queries import (
    get_all_categories,
    get_subcategories_by_category,
    get_available_items_by_subcategory,
    add_category,
    add_subcategory,
    add_item,
    update_category_name,
    update_subcategory_details,
    edit_item_code,
    delete_single_item,
    delete_category_by_id,
    delete_subcategory_by_id,
    get_category_count,
    get_subcategory_count,
    get_item_count,
)
from source.utils.helpers import format_rupiah


async def get_categories(limit=10, offset=0):
    categories, total = await get_all_categories(limit, offset)
    return {
        "data": [{"id": c[0], "name": c[1]} for c in categories],
        "total": total
    }

async def create_category(name: str):
    await add_category(name)
    return {"success": True, "message": f"Kategori '{name}' ditambahkan."}

async def update_category(category_id: int, name: str):
    await update_category_name(category_id, name)
    return {"success": True, "message": f"Kategori diubah menjadi '{name}'."}

async def delete_category(category_id: int):
    await delete_category_by_id(category_id)
    return {"success": True, "message": "Kategori dihapus."}


async def get_subcategories(category_id: int, limit=10, offset=0):
    subs, total = await get_subcategories_by_category(category_id, limit, offset)
    result = []
    for sub in subs:
        sub_id, name, price = sub
        result.append({
            "id": sub_id,
            "name": name,
            "price": format_rupiah(price),
            "price_raw": price
        })
    return {"data": result, "total": total}

async def create_subcategory(category_id: int, name: str, price: int):
    await add_subcategory(category_id, name, price)
    return {"success": True, "message": f"Subkategori '{name}' ditambahkan."}

async def update_subcategory(subcategory_id: int, name: str, price: int):
    await update_subcategory_details(subcategory_id, name, price)
    return {"success": True, "message": "Subkategori diperbarui."}

async def delete_subcategory(subcategory_id: int):
    await delete_subcategory_by_id(subcategory_id)
    return {"success": True, "message": "Subkategori dihapus."}


async def get_items(subcategory_id: int, limit=10, offset=0):
    items, total = await get_available_items_by_subcategory(subcategory_id, limit, offset)
    data = []
    for item in items:
        item_id, code, is_used = item
        data.append({"id": item_id, "code": code, "is_used": bool(is_used)})
    return {"data": data, "total": total}

async def create_items(subcategory_id: int, codes: list):
    added = 0
    for code in codes:
        await add_item(subcategory_id, code.strip())
        added += 1
    return {"success": True, "message": f"{added} item ditambahkan."}

async def update_item(item_id: int, new_code: str):
    success = await edit_item_code(item_id, new_code)
    if success:
        return {"success": True, "message": "Kode item diperbarui."}
    return {"success": False, "message": "Kode sudah ada atau item tidak valid."}

async def delete_item(item_id: int):
    success = await delete_single_item(item_id)
    if success:
        return {"success": True, "message": "Item dihapus."}
    return {"success": False, "message": "Item tidak dapat dihapus (mungkin sudah terpakai)."}


async def export_items(subcategory_id: int):
    items, _ = await get_available_items_by_subcategory(subcategory_id, limit=10000, offset=0)
    codes = [item[1] for item in items]
    return codes

async def import_csv_preview(subcategory_id: int, content: str):
    reader = csv.reader(io.StringIO(content))
    codes = []
    for row in reader:
        if row:
            codes.append(row[0].strip())
    existing_items, _ = await get_available_items_by_subcategory(subcategory_id, limit=10000, offset=0)
    existing_codes = {item[1] for item in existing_items}
    preview = []
    for code in codes:
        if code in existing_codes:
            preview.append({"code": code, "status": "duplicate"})
        else:
            preview.append({"code": code, "status": "new"})
    return preview

async def import_csv_execute(subcategory_id: int, codes: list):
    added = 0
    for code in codes:
        await add_item(subcategory_id, code.strip())
        added += 1
    return {"success": True, "message": f"{added} item berhasil diimpor."}


async def get_product_stats():
    return {
        "total_categories": await get_category_count(),
        "total_subcategories": await get_subcategory_count(),
        "total_items": await get_item_count()
    }


# ── Fungsi baru untuk Grid Ringkasan ─────────────────────
async def get_summary_stats(tab: str, category_id: int = None, subcategory_id: int = None):
    if tab == 'kategori':
        total = await get_category_count()
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("PRAGMA foreign_keys = ON")
            cursor = await db.execute("SELECT COUNT(DISTINCT category_id) FROM subcategories")
            terisi = (await cursor.fetchone())[0]
        return {"total": total, "terisi": terisi, "kosong": total - terisi}

    elif tab == 'subkategori':
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("PRAGMA foreign_keys = ON")
            if category_id:
                cursor = await db.execute("SELECT COUNT(*) FROM subcategories WHERE category_id = ?", (category_id,))
                total = (await cursor.fetchone())[0]
                cursor = await db.execute(
                    "SELECT COUNT(DISTINCT subcategory_id) FROM items WHERE subcategory_id IN (SELECT id FROM subcategories WHERE category_id = ?)",
                    (category_id,))
                terisi = (await cursor.fetchone())[0]
            else:
                cursor = await db.execute("SELECT COUNT(*) FROM subcategories")
                total = (await cursor.fetchone())[0]
                cursor = await db.execute("SELECT COUNT(DISTINCT subcategory_id) FROM items")
                terisi = (await cursor.fetchone())[0]
        return {"total": total, "terisi": terisi, "kosong": total - terisi}

    elif tab == 'item':
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("PRAGMA foreign_keys = ON")
            if subcategory_id:
                cursor = await db.execute("SELECT COUNT(*) FROM items WHERE subcategory_id = ?", (subcategory_id,))
                total = (await cursor.fetchone())[0]
                cursor = await db.execute("SELECT COUNT(*) FROM items WHERE subcategory_id = ? AND is_used = 0", (subcategory_id,))
                tersedia = (await cursor.fetchone())[0]
            else:
                cursor = await db.execute("SELECT COUNT(*) FROM items")
                total = (await cursor.fetchone())[0]
                cursor = await db.execute("SELECT COUNT(*) FROM items WHERE is_used = 0")
                tersedia = (await cursor.fetchone())[0]
        return {"total": total, "tersedia": tersedia, "terpakai": total - tersedia}