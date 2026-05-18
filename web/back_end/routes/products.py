# web/back_end/routes/products.py
from fastapi import APIRouter, Query, Form, UploadFile, File, Depends
from web.back_end.services.auth_service import get_current_admin
from web.back_end.services.product_service import (
    get_categories,
    create_category,
    update_category,
    delete_category,
    get_subcategories,
    create_subcategory,
    update_subcategory,
    delete_subcategory,
    get_items,
    create_items,
    update_item,
    delete_item,
    export_items,
    import_csv_preview,
    import_csv_execute,
    get_product_stats,
)
from typing import Optional

router = APIRouter(prefix="/api/products", tags=["products"], dependencies=[Depends(get_current_admin)])


# ── Kategori ──
@router.get("/categories")
async def api_categories(page: int = Query(1, ge=1), limit: int = 10):
    offset = (page - 1) * limit
    return await get_categories(limit, offset)


@router.post("/categories")
async def api_create_category(name: str = Form(...)):
    return await create_category(name)


@router.put("/categories/{category_id}")
async def api_update_category(category_id: int, name: str = Form(...)):
    return await update_category(category_id, name)


@router.delete("/categories/{category_id}")
async def api_delete_category(category_id: int):
    return await delete_category(category_id)


# ── Subkategori ──
@router.get("/subcategories")
async def api_subcategories(
    category_id: int = Query(...), page: int = 1, limit: int = 10
):
    offset = (page - 1) * limit
    return await get_subcategories(category_id, limit, offset)


@router.post("/subcategories")
async def api_create_subcategory(
    category_id: int = Form(...), name: str = Form(...), price: int = Form(...)
):
    return await create_subcategory(category_id, name, price)


@router.put("/subcategories/{subcategory_id}")
async def api_update_subcategory(
    subcategory_id: int, name: str = Form(...), price: int = Form(...)
):
    return await update_subcategory(subcategory_id, name, price)


@router.delete("/subcategories/{subcategory_id}")
async def api_delete_subcategory(subcategory_id: int):
    return await delete_subcategory(subcategory_id)


# ── Item ──
@router.get("/items")
async def api_items(subcategory_id: int = Query(...), page: int = 1, limit: int = 10):
    offset = (page - 1) * limit
    return await get_items(subcategory_id, limit, offset)


@router.post("/items")
async def api_create_items(subcategory_id: int = Form(...), codes: str = Form(...)):
    code_list = [c.strip() for c in codes.split("\n") if c.strip()]
    return await create_items(subcategory_id, code_list)


@router.put("/items/{item_id}")
async def api_update_item(item_id: int, new_code: str = Form(...)):
    return await update_item(item_id, new_code)


@router.delete("/items/{item_id}")
async def api_delete_item(item_id: int):
    return await delete_item(item_id)


# ── Ekspor / Impor ──
@router.get("/items/export")
async def api_export_items(subcategory_id: int = Query(...)):
    codes = await export_items(subcategory_id)
    return {"codes": codes}


@router.post("/items/import/preview")
async def api_import_preview(
    subcategory_id: int = Form(...), file: UploadFile = File(...)
):
    content = (await file.read()).decode()
    return await import_csv_preview(subcategory_id, content)


@router.post("/items/import/execute")
async def api_import_execute(subcategory_id: int = Form(...), codes: str = Form(...)):
    code_list = [c.strip() for c in codes.split("\n") if c.strip()]
    return await import_csv_execute(subcategory_id, code_list)


# ── Statistik ──
@router.get("/stats")
async def api_product_stats():
    return await get_product_stats()


# ── Ekspor/Impor Global ──
@router.get("/export-all")
async def api_export_all():
    from source.database.products import export_all_items_data
    import csv
    import io

    items = await export_all_items_data()
    output = io.StringIO()
    writer = csv.writer(output)
    for item in items:
        writer.writerow(item)
    output.seek(0)
    from fastapi.responses import StreamingResponse

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=semua_item.csv"},
    )


@router.post("/import")
async def api_import_global(file: UploadFile = File(...)):
    import csv
    import io

    from source.database.products import (
        add_item,
        get_category_by_name,
        add_category,
        get_subcategory_by_name,
        add_subcategory,
    )

    content = await file.read()
    reader = csv.reader(io.StringIO(content.decode()))
    added = 0
    errors = 0
    for row in reader:
        if not row or len(row) < 4:
            continue
        cat_name, sub_name, code, harga = (
            row[0].strip(),
            row[1].strip(),
            row[2].strip(),
            row[3].strip(),
        )
        if not all([cat_name, sub_name, code, harga]):
            continue
        try:
            harga = int(harga)
        except ValueError:
            errors += 1
            continue
        # Cari atau buat kategori
        cat = await get_category_by_name(cat_name)
        if not cat:
            cat_id = await add_category(cat_name)
        else:
            cat_id = cat[0]
        # Cari atau buat subkategori
        sub = await get_subcategory_by_name(sub_name, cat_id)
        if not sub:
            sub_id = await add_subcategory(cat_id, sub_name, harga)
        else:
            sub_id = sub[0]
        await add_item(sub_id, code)
        added += 1
    return {
        "success": True,
        "message": f"Impor selesai. {added} item ditambahkan, {errors} error.",
    }


@router.get("/summary")
async def api_summary(
    tab: str = Query(...), category_id: int = None, subcategory_id: int = None
):
    from web.back_end.services.product_service import get_summary_stats

    return await get_summary_stats(tab, category_id, subcategory_id)
