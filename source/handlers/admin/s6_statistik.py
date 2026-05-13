from aiogram import Router, F
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from aiogram.enums import ParseMode

from source.database.queries import (
    get_total_revenue,
    get_order_counts,
    get_total_items_sold,
    get_remaining_stock,
    get_category_count,
    get_subcategory_count,
    get_item_count
)

from source.utils.helpers import format_rupiah

router = Router()


def get_stats_keyboard():
    buttons = [
        [
            InlineKeyboardButton(
                text="🔄 Refresh",
                callback_data="refresh_stats"
            )
        ],
        [
            InlineKeyboardButton(
                text="« Kembali",
                callback_data="admin_back"
            )
        ]
    ]

    return InlineKeyboardMarkup(
        inline_keyboard=buttons
    )


@router.callback_query(F.data == "admin_stats")
async def show_statistics(callback: CallbackQuery):
    await send_stats(callback.message)
    await callback.answer()


@router.callback_query(F.data == "refresh_stats")
async def refresh_stats(callback: CallbackQuery):
    await send_stats(callback.message)
    await callback.answer()


async def send_stats(message):

    total_revenue = await get_total_revenue()
    counts = await get_order_counts()

    items_sold = await get_total_items_sold()
    remaining_stock = await get_remaining_stock()

    category_count = await get_category_count()
    subcategory_count = await get_subcategory_count()
    total_items = await get_item_count()

    approved = counts.get("approved", 0)
    pending = counts.get("pending", 0)
    rejected = counts.get("rejected", 0)

    text = (
        "<b>📊 STATISTIK TOKO</b>\n"
        "━━━━━━━━━━━━━━━━━━\n"

        f"💰 <b>Total Pendapatan</b>\n"
        f"<pre>Rp {format_rupiah(total_revenue)}</pre>\n"

        "📦 <b>Pesanan</b>\n"
        "<pre>"
        f"✅ Disetujui : {approved}\n"
        f"⏳ Pending   : {pending}\n"
        f"❌ Ditolak   : {rejected}"
        "</pre>\n"

        "🎫 <b>Penjualan</b>\n"
        "<pre>"
        f"Item Terjual : {items_sold}\n"
        f"Stok Tersisa : {remaining_stock}"
        "</pre>\n"

        "📁 <b>Master Data</b>\n"
        "<pre>"
        f"Kategori    : {category_count}\n"
        f"Subkategori : {subcategory_count}\n"
        f"Total Item  : {total_items}"
        "</pre>"
    )

    await message.edit_text(
        text=text,
        parse_mode=ParseMode.HTML,
        reply_markup=get_stats_keyboard()
    )