# web/back_end/services/home_service.py
from source.database.admin import (
    get_total_revenue,
    get_order_counts,
    get_total_items_sold,
    get_remaining_stock,
)
from source.database.orders import (
    get_incoming_orders,
    get_orders_by_status,
)
from source.database.products import (
    get_category_count,
    get_subcategory_count,
    get_item_count,
)
from source.utils.helpers import format_rupiah


async def get_home_data():
    # Pendapatan
    total_revenue = await get_total_revenue()

    # Masuk & Pending
    _, incoming_total = await get_incoming_orders(limit=1)
    _, pending_total = await get_orders_by_status("pending", limit=1)

    # Statistik Pesanan
    order_counts = await get_order_counts()
    approved = order_counts.get("approved", 0)
    rejected = order_counts.get("rejected", 0)
    total_orders = approved + rejected + pending_total

    # Statistik Data
    categories = await get_category_count()
    subcategories = await get_subcategory_count()
    items_sold = await get_total_items_sold()
    items_available = await get_remaining_stock()
    items_total = await get_item_count()

    return {
        "total_revenue": format_rupiah(total_revenue),
        "incoming_total": incoming_total,
        "pending_total": pending_total,
        "approved": approved,
        "rejected": rejected,
        "total_orders": total_orders,
        "categories": categories,
        "subcategories": subcategories,
        "items_sold": items_sold,
        "items_available": items_available,
        "items_total": items_total,
    }
