# s5_pesanan.py

from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from source.database.queries import (
    get_orders_by_status,
    get_order_by_id,
    get_available_item,
    mark_item_used,
    update_order_status,
    get_order_details,
    get_item_subcategory,
)
from source.utils.helpers import format_rupiah
from source.config import BOT_TOKEN

router = Router()
bot = Bot(token=BOT_TOKEN)

ORDERS_PER_PAGE = 5


# ── Helper Keyboard ────────────────────────────
def main_menu_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📦 Pesanan Pending", callback_data="orders_pending")],
        [InlineKeyboardButton(text="📜 Riwayat Pesanan", callback_data="orders_history")],
        [InlineKeyboardButton(text="« Kembali ke Panel", callback_data="admin_back")]
    ])


def history_filter_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Semua", callback_data="history_all"),
         InlineKeyboardButton(text="Pending", callback_data="history_pending")],
        [InlineKeyboardButton(text="Disetujui", callback_data="history_approved"),
         InlineKeyboardButton(text="Ditolak", callback_data="history_rejected")],
        [InlineKeyboardButton(text="« Kembali", callback_data="admin_orders")]
    ])


# ── Entry: Menu Utama Pesanan ─────────────────
@router.callback_query(F.data == "admin_orders")
async def orders_main_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "🛒 *Manajemen Pesanan*\n\nPilih menu:",
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard()
    )
    await callback.answer()


# ── PESANAN PENDING ───────────────────────────
@router.callback_query(F.data == "orders_pending")
async def show_pending_orders(callback: CallbackQuery, state: FSMContext, page: int = 1):
    await show_pending_page(callback, page, state)


async def show_pending_page(callback: CallbackQuery, page: int, state: FSMContext):
    offset = (page - 1) * ORDERS_PER_PAGE
    orders, total = await get_orders_by_status("pending", limit=ORDERS_PER_PAGE, offset=offset)
    total_pages = max((total + ORDERS_PER_PAGE - 1) // ORDERS_PER_PAGE, 1)

    if not orders:
        text = "📦 *Pesanan Pending*\n\nTidak ada pesanan pending saat ini."
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="« Kembali", callback_data="admin_orders")]
        ])
        await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)
        return

    text = f"📦 *Pesanan Pending* (Hal {page}/{total_pages})\n\n"
    for order in orders:
        # Unpack 9 kolom (sesuai schema tabel orders)
        order_id, user_id, item_id, qty, total_price, three_digits, payment_proof, status, created_at = order
        sub_name, cat_name = await get_order_details(item_id)
        text += (
            f"🔹 `{order_id}` | User: `{user_id}`\n"
            f"   {cat_name} → {sub_name} (x{qty})\n"
            f"   Total: Rp{format_rupiah(total_price)}\n\n"
        )

    # Tombol navigasi halaman
    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton(text="◀", callback_data=f"pendinglist_page_{page-1}"))
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton(text="▶", callback_data=f"pendinglist_page_{page+1}"))

    keyboard_rows = []
    if nav_buttons:
        keyboard_rows.append(nav_buttons)
    keyboard_rows.append([InlineKeyboardButton(text="« Kembali", callback_data="admin_orders")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_rows)

    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)
    await state.update_data(pending_page=page)


@router.callback_query(F.data.startswith("pendinglist_page_"))
async def pending_list_page(callback: CallbackQuery, state: FSMContext):
    page = int(callback.data.split("_")[2])
    await show_pending_page(callback, page, state)


# ── DETAIL ORDER + AKSI ─────────────────────
@router.callback_query(F.data.startswith("order_detail_"))
async def order_detail(callback: CallbackQuery, state: FSMContext):
    order_id = callback.data.split("_")[2]
    order = await get_order_by_id(order_id)
    if not order or order[7] != 'pending':
        await callback.answer("Pesanan tidak valid atau sudah diproses.", show_alert=True)
        data = await state.get_data()
        page = data.get("pending_page", 1)
        await show_pending_page(callback, page, state)
        return

    # Unpack 9 kolom dari fungsi get_order_by_id (harus mengembalikan 9 kolom)
    user_id, item_id, qty, total, three_digits, status, = order[1], order[2], order[3], order[4], order[5], order[6], order[7], order[8]
    sub_name, cat_name = await get_order_details(item_id)
    text = (
        f"📋 *Detail Pesanan*\n"
        f"Order ID: `{order_id}`\n"
        f"User ID: `{user_id}`\n"
        f"Produk: {cat_name} → {sub_name}\n"
        f"Jumlah: {qty}\n"
        f"Total: Rp{format_rupiah(total)}\n"
        f"Kode Unik: {three_digits}\n"
        f"Status: {status}\n"
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Setujui", callback_data=f"approve_{order_id}"),
         InlineKeyboardButton(text="❌ Tolak", callback_data=f"reject_{order_id}")],
        [InlineKeyboardButton(text="📷 Lihat Bukti", callback_data=f"view_proof_{order_id}")],
        [InlineKeyboardButton(text="« Kembali", callback_data="orders_pending")]
    ])
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)
    await state.update_data(current_order_id=order_id)


# ── LIHAT BUKTI ────────────────────────────
@router.callback_query(F.data.startswith("view_proof_"))
async def view_proof(callback: CallbackQuery):
    order_id = callback.data.split("_")[2]
    order = await get_order_by_id(order_id)
    if not order or not order[6]:
        await callback.answer("Bukti tidak tersedia.", show_alert=True)
        return
    file_id = order[6]
    await callback.message.answer_photo(file_id, caption=f"Bukti pembayaran untuk {order_id}")
    await callback.answer()


# ── APPROVE ────────────────────────────────
@router.callback_query(F.data.startswith("approve_"))
async def approve_order_handler(callback: CallbackQuery, state: FSMContext):
    order_id = callback.data.split("_")[1]
    order = await get_order_by_id(order_id)
    if not order or order[7] != 'pending':
        await callback.answer("Pesanan tidak valid.", show_alert=True)
        return

    sub_id = await get_item_subcategory(order[2])
    item = await get_available_item(sub_id)
    if not item:
        await callback.answer("Stok item habis.", show_alert=True)
        return
    item_id, code = item
    await mark_item_used(item_id, order_id)
    await update_order_status(order_id, 'approved')

    user_id = order[1]
    try:
        await bot.send_message(user_id, f"✅ Pesanan {order_id} disetujui!\nKode Anda: {code}")
    except Exception:
        pass
    await callback.message.edit_text(f"✅ Pesanan {order_id} disetujui.")
    data = await state.get_data()
    page = data.get("pending_page", 1)
    await show_pending_page(callback, page, state)


# ── REJECT ─────────────────────────────────
@router.callback_query(F.data.startswith("reject_"))
async def reject_order_handler(callback: CallbackQuery, state: FSMContext):
    order_id = callback.data.split("_")[1]
    order = await get_order_by_id(order_id)
    if not order or order[7] != 'pending':
        await callback.answer("Pesanan tidak valid.", show_alert=True)
        return
    await update_order_status(order_id, 'rejected')
    user_id = order[1]
    try:
        await bot.send_message(user_id, f"❌ Pesanan {order_id} ditolak. Hubungi admin.")
    except Exception:
        pass
    await callback.message.edit_text(f"❌ Pesanan {order_id} ditolak.")
    data = await state.get_data()
    page = data.get("pending_page", 1)
    await show_pending_page(callback, page, state)


# ── RIWAYAT PESANAN ───────────────────────
@router.callback_query(F.data == "orders_history")
async def history_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "📜 *Riwayat Pesanan*\n\nPilih filter:",
        parse_mode="Markdown",
        reply_markup=history_filter_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("history_"))
async def history_show(callback: CallbackQuery, state: FSMContext, page: int = 1):
    filter_status = callback.data.split("_")[1]
    if filter_status == "all":
        status = None
    else:
        status = filter_status
    await show_history_page(callback, status, page, state)


async def show_history_page(callback: CallbackQuery, status, page: int, state: FSMContext):
    offset = (page - 1) * ORDERS_PER_PAGE
    orders, total = await get_orders_by_status(status, ORDERS_PER_PAGE, offset)
    total_pages = max((total + ORDERS_PER_PAGE - 1) // ORDERS_PER_PAGE, 1)

    if not orders:
        text = "📜 Tidak ada pesanan."
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="« Kembali", callback_data="orders_history")]
        ])
        await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)
        return

    text = f"📜 *Riwayat Pesanan* (Hal {page}/{total_pages})\n\n"
    for order in orders:
        # Unpack 9 kolom
        order_id, user_id, item_id, qty, total_price, three_digits, proof, order_status, created_at = order
        sub_name, cat_name = await get_order_details(item_id)
        text += (
            f"🔹 `{order_id}` | User: `{user_id}` | Status: {order_status}\n"
            f"   {cat_name} → {sub_name} (x{qty}) - Rp{format_rupiah(total_price)}\n\n"
        )

    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton(text="◀", callback_data=f"histpage_{status or 'all'}_{page-1}"))
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton(text="▶", callback_data=f"histpage_{status or 'all'}_{page+1}"))
    rows = [nav_buttons] if nav_buttons else []
    rows.append([InlineKeyboardButton(text="« Kembali", callback_data="orders_history")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=rows)
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)
    await state.update_data(history_status=status, history_page=page)


@router.callback_query(F.data.startswith("histpage_"))
async def history_page_nav(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    status = parts[1] if parts[1] != 'all' else None
    page = int(parts[2])
    await show_history_page(callback, status, page, state)