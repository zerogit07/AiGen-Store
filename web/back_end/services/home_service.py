# web/back_end/services/home_service.py

from source.database.admin import (
    get_total_revenue_month,
    get_order_counts_month,
    get_total_items_sold_month,
    get_remaining_stock,
)
from source.database.orders import (
    get_incoming_orders,
    get_orders_by_status,
    get_report_summary,
    get_top_products,
    get_history,
)


from source.database.products import (
    get_category_count,
    get_subcategory_count,
    get_item_count,
)

from source.database.users import (
    get_dashboard_users,
    search_dashboard_users,
    get_user_detail,
    update_user_ban,
)

from source.utils.helpers import format_rupiah
from datetime import datetime


async def get_home_data(month: str = ""):
    bulan_map = {
        "Januari": "01",
        "Februari": "02",
        "Maret": "03",
        "April": "04",
        "Mei": "05",
        "Juni": "06",
        "Juli": "07",
        "Agustus": "08",
        "September": "09",
        "Oktober": "10",
        "November": "11",
        "Desember": "12",
    }

    bulan_id = [
        "Januari",
        "Februari",
        "Maret",
        "April",
        "Mei",
        "Juni",
        "Juli",
        "Agustus",
        "September",
        "Oktober",
        "November",
        "Desember",
    ]

    bulan = month or bulan_id[datetime.now().month - 1]

    month_num = bulan_map.get(bulan)

    total_revenue = await get_total_revenue_month(month_num)

    _, incoming_total = await get_incoming_orders(limit=1)

    _, pending_total = await get_orders_by_status("pending", limit=1)

    order_counts = await get_order_counts_month(month_num)

    approved = order_counts.get("approved", 0)

    pending = order_counts.get("pending", 0)

    rejected = order_counts.get("rejected", 0)

    total_orders = approved + pending + rejected

    categories = await get_category_count()

    subcategories = await get_subcategory_count()

    items_sold = await get_total_items_sold_month(month_num)

    items_available = await get_remaining_stock()

    items_total = await get_item_count()

    return {
        "bulan": bulan,
        "total_revenue": format_rupiah(total_revenue),
        "incoming_total": incoming_total,
        "pending_total": pending_total,
        "approved": approved,
        "pending": pending,
        "rejected": rejected,
        "total_orders": total_orders,
        "categories": categories,
        "subcategories": subcategories,
        "items_sold": items_sold,
        "items_available": items_available,
        "items_total": items_total,
    }


async def get_home_users(page: int = 1, search: str = ""):
    limit = 10
    offset = (page - 1) * limit

    if search:
        users, total = await search_dashboard_users(search, limit, offset)
    else:
        users, total = await get_dashboard_users(limit, offset)

    total_pages = (total + limit - 1) // limit

    return {
        "data": [
            {
                "user_id": u[0],
                "username": u[1] or "-",
                "order": u[2],
                "total": format_rupiah(u[3]),
                "status": "Banned" if u[4] else "Active",
            }
            for u in users
        ],
        "pagination": {"page": page, "total": total, "total_pages": total_pages},
    }


async def get_user_modal(user_id: int):
    data = await get_user_detail(user_id)

    if not data:
        return {}

    return {
        "user_id": data[0],
        "username": data[1] or "-",
        "order": data[2],
        "total": format_rupiah(data[3]),
        "status": "Banned" if data[4] else "Active",
        "is_banned": data[4],
    }


async def change_user_status(user_id: int, status: int):
    await update_user_ban(user_id, status)

    return {"success": True}


async def get_home_report(
    page: int = 1,
    filter_type: str = ""
):
    limit = 10
    offset = (page - 1) * limit

    summary = await get_report_summary()

    products = await get_top_products(
        limit=3,
        filter_type=filter_type
    )

    history, total = await get_history(
        limit,
        offset,
        filter_type
    )

    total_pages = (total + limit - 1) // limit
    return {
        "summary": {
            "pendapatan": format_rupiah(summary[0]),
            "order": summary[1],
            "approved": summary[2],
            "pending": summary[3],
            "rejected": summary[4],
        },
        "products": [{"name": p[0], "sold": p[1]} for p in products],
        "history": [
            {
                "id": h[0],
                "user_id": h[1],
                "username": h[2],
                "produk": h[3],
                "qty": h[4],
                "total": format_rupiah(h[5]),
                "tanggal": h[6].split(" ")[0].split("-")[2]
                + "/"
                + h[6].split(" ")[0].split("-")[1]
                + "/"
                + h[6].split(" ")[0].split("-")[0]
                if h[6]
                else "-",
                "status": h[7],
            }
            for h in history
        ],
        "pagination": {"page": page, "total": total, "total_pages": total_pages},
    }
