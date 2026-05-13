# source/handlers/admin/s5_pesanan.py

from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from source.database.queries import (
    get_orders_by_status,
    get_order_details,
    get_pending_order_ids,
    delete_orders_by_status,
)
from source.utils.helpers import format_rupiah
from source.config import BOT_TOKEN

router = Router()
bot = Bot(token=BOT_TOKEN)

ITEMS_PER_PAGE = 10

# ── Keyboard ──────────────────────────────────
def main_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📦 Pesanan Pending", callback_data="orders_pending")],
        [InlineKeyboardButton(text="📜 Riwayat Pesanan", callback_data="orders_history")],
        [InlineKeyboardButton(text="« Kembali ke Panel", callback_data="admin_back")]
    ])

def history_filter_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Semua", callback_data="history_all"),
         InlineKeyboardButton(text="Disetujui", callback_data="history_approved"),
         InlineKeyboardButton(text="Ditolak", callback_data="history_rejected")],
        [InlineKeyboardButton(text="« Kembali", callback_data="admin_orders")]
    ])

# ── Menu Utama ───────────────────────────────
@router.callback_query(F.data == "admin_orders")
async def orders_main(callback: CallbackQuery):
    await callback.message.edit_text("🛒 *Manajemen Pesanan*\n\nPilih menu:", parse_mode="Markdown", reply_markup=main_menu_kb())
    await callback.answer()

# ═══════════════ PENDING ═════════════════════
@router.callback_query(F.data == "orders_pending")
async def pending_start(callback: CallbackQuery, state: FSMContext):
    await show_pending_page(callback, 1, state)

async def show_pending_page(callback: CallbackQuery, page: int, state: FSMContext):
    offset = (page - 1) * ITEMS_PER_PAGE
    orders, total = await get_orders_by_status("pending", limit=ITEMS_PER_PAGE, offset=offset)
    total_pages = max((total + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE, 1)

    if not orders:
        await callback.message.edit_text(
            "📦 *Pesanan Pending*\n\nTidak ada pesanan pending saat ini.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="« Kembali", callback_data="admin_orders")]
            ])
        )
        return

    text = f"📦 *Pesanan Pending* (Hal {page}/{total_pages})\n\n"
    for order in orders:
        order_id, user_id, item_id, qty, total_price, three_digits, payment_proof, status = order
        sub_name, cat_name = await get_order_details(item_id)
        text += (
            f"🔹 `{order_id}` | User: `{user_id}`\n"
            f"   {cat_name} → {sub_name} (x{qty})\n"
            f"   Total: Rp{format_rupiah(total_price)}\n\n"
        )

    rows = []
    nav = []
    if page > 1:
        nav.append(InlineKeyboardButton(text="◀", callback_data=f"pending_page_{page-1}"))
    if page < total_pages:
        nav.append(InlineKeyboardButton(text="▶", callback_data=f"pending_page_{page+1}"))
    if nav:
        rows.append(nav)

    rows.append([InlineKeyboardButton(text="🗑️ Hapus Semua Pending", callback_data="delete_pending")])
    rows.append([InlineKeyboardButton(text="« Kembali", callback_data="admin_orders")])

    kb = InlineKeyboardMarkup(inline_keyboard=rows)
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=kb)
    await state.update_data(pending_page=page)
    await callback.answer()

@router.callback_query(F.data.startswith("pending_page_"))
async def pending_page_nav(callback: CallbackQuery, state: FSMContext):
    page = int(callback.data.split("_")[2])
    await show_pending_page(callback, page, state)

@router.callback_query(F.data == "delete_pending")
async def delete_pending_prompt(callback: CallbackQuery):
    _, total = await get_orders_by_status("pending", limit=1, offset=0)
    if total == 0:
        await callback.answer("Tidak ada pesanan pending.", show_alert=True)
        return
    await callback.message.edit_text(
        f"⚠️ Hapus **seluruh pesanan pending** ({total} pesanan)?",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Ya, hapus semua", callback_data="confirm_delete_pending")],
            [InlineKeyboardButton(text="❌ Batal", callback_data="orders_pending")]
        ])
    )
    await callback.answer()

@router.callback_query(F.data == "confirm_delete_pending")
async def process_delete_pending(callback: CallbackQuery):
    count = await delete_orders_by_status("pending")
    await callback.message.edit_text(
        f"✅ {count} pesanan pending berhasil dihapus.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="« Kembali", callback_data="orders_pending")]
        ])
    )
    await callback.answer()

# ═══════════════ RIWAYAT ═════════════════════
@router.callback_query(F.data == "orders_history")
async def history_menu(callback: CallbackQuery):
    await callback.message.edit_text("📜 *Riwayat Pesanan*\n\nPilih filter:", parse_mode="Markdown", reply_markup=history_filter_kb())
    await callback.answer()

@router.callback_query(F.data.startswith("history_"))
async def history_filter_handler(callback: CallbackQuery, state: FSMContext):
    filter_val = callback.data.split("_")[1]  # 'all', 'approved', 'rejected'
    status = None if filter_val == "all" else filter_val
    await state.update_data(history_status=status)
    await show_history_page(callback, status, 1, state)

async def show_history_page(callback: CallbackQuery, status, page: int, state: FSMContext):
    offset = (page - 1) * ITEMS_PER_PAGE
    orders, total = await get_orders_by_status(status, limit=ITEMS_PER_PAGE, offset=offset)
    total_pages = max((total + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE, 1)

    if not orders:
        await callback.message.edit_text("📜 Tidak ada pesanan.", parse_mode="Markdown",
                                          reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                              [InlineKeyboardButton(text="« Kembali", callback_data="orders_history")]
                                          ]))
        return

    text = f"📜 *Riwayat Pesanan* (Hal {page}/{total_pages})\n\n"
    for order in orders:
        order_id, user_id, item_id, qty, total_price, three_digits, proof, order_status = order
        sub_name, cat_name = await get_order_details(item_id)
        text += (
            f"🔹 `{order_id}` | User: `{user_id}` | Status: {order_status}\n"
            f"   {cat_name} → {sub_name} (x{qty}) - Rp{format_rupiah(total_price)}\n\n"
        )

    nav = []
    if page > 1:
        nav.append(InlineKeyboardButton(text="◀", callback_data=f"histpage_{status or 'all'}_{page-1}"))
    if page < total_pages:
        nav.append(InlineKeyboardButton(text="▶", callback_data=f"histpage_{status or 'all'}_{page+1}"))
    rows = [nav] if nav else []
    rows.append([InlineKeyboardButton(text="🗑️ Hapus Riwayat", callback_data="delete_history")])
    rows.append([InlineKeyboardButton(text="« Kembali", callback_data="orders_history")])
    kb = InlineKeyboardMarkup(inline_keyboard=rows)

    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=kb)
    await state.update_data(history_status=status, history_page=page)
    await callback.answer()

@router.callback_query(F.data.startswith("histpage_"))
async def history_page_nav(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    status = None if parts[1] == 'all' else parts[1]
    page = int(parts[2])
    await show_history_page(callback, status, page, state)

@router.callback_query(F.data == "delete_history")
async def delete_history_prompt(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    status = data.get("history_status")  # None, 'approved', 'rejected'
    label = status or "semua"
    await callback.message.edit_text(
        f"⚠️ Hapus **{label}** riwayat?",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Ya", callback_data=f"confirm_delete_history_{status or 'all'}")],
            [InlineKeyboardButton(text="❌ Batal", callback_data="orders_history")]
        ])
    )
    await callback.answer()

@router.callback_query(F.data.startswith("confirm_delete_history_"))
async def process_delete_history(callback: CallbackQuery):
    status = callback.data.split("_")[3]
    if status == "all":
        status = None
    count = await delete_orders_by_status(status)
    await callback.message.edit_text(
        f"✅ Riwayat dihapus ({count} pesanan).",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="« Kembali", callback_data="orders_history")]
        ])
    )
    await callback.answer()