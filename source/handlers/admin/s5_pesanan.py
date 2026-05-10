# source/handlers/admin/s5_pesanan.py
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from source.config import ADMIN_ID, BOT_TOKEN
from source.database.queries import (
    get_orders_by_status, get_order_by_id, get_available_item,
    mark_item_used, update_order_status, get_order_details,
    get_product_variant
)
from source.utils.helpers import format_rupiah

router = Router()
bot = Bot(token=BOT_TOKEN)
ITEMS_PER_PAGE = 5

# ========== MENU UTAMA ==========
@router.callback_query(F.data == "admin_orders")
async def orders_menu(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📦 Pesanan Pending", callback_data="orders_pending")],
        [InlineKeyboardButton(text="📜 Riwayat Pesanan", callback_data="orders_history")],
        [InlineKeyboardButton(text="« Kembali", callback_data="admin_back")]
    ])
    await callback.message.edit_text("📋 *Manajemen Pesanan*", parse_mode="Markdown", reply_markup=keyboard)
    await callback.answer()

# ========== PESANAN PENDING (TAMPIL PER ORDER) ==========
@router.callback_query(F.data == "orders_pending")
async def pending_orders(callback: CallbackQuery, page: int = 1):
    offset = (page - 1) * ITEMS_PER_PAGE
    orders, total = await get_orders_by_status('pending', ITEMS_PER_PAGE, offset)
    total_pages = (total + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
    if not orders:
        await callback.message.edit_text("📭 Tidak ada pesanan pending.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="« Kembali", callback_data="admin_orders")]]))
        await callback.answer()
        return
    # Tampilkan satu per satu (bisa juga daftar singkat, tapi lebih baik daftar untuk pending)
    # Agar tidak terlalu panjang, kita buat daftar dengan tombol aksi di setiap pesan
    for order in orders:
        order_id, user_id, variant_id, qty, total_price, three_digits, proof, status, created_at = order
        variant = await get_product_variant(variant_id)
        product_name = variant[1] if variant else "?"
        variant_name = variant[2] if variant else "?"
        text = (
            f"🆔 *Order:* `{order_id}`\n"
            f"👤 *User:* `{user_id}`\n"
            f"📦 *Produk:* {product_name} - {variant_name}\n"
            f"🔢 *Jumlah:* {qty}\n"
            f"💰 *Total:* Rp{format_rupiah(total_price)}\n"
            f"🔑 *Kode Unik:* {three_digits}\n"
            f"🕒 *Waktu:* {created_at[:16]}"
        )
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Setujui", callback_data=f"admin_approve_{order_id}"),
             InlineKeyboardButton(text="❌ Tolak", callback_data=f"admin_reject_{order_id}"),
             InlineKeyboardButton(text="📸 Bukti", callback_data=f"admin_proof_{order_id}")]
        ])
        await callback.message.answer(text, parse_mode="Markdown", reply_markup=keyboard)
    # Tambahkan navigasi halaman jika diperlukan
    if total_pages > 1:
        nav = []
        if page > 1:
            nav.append(InlineKeyboardButton(text="◀ Sebelumnya", callback_data=f"pending_page_{page-1}"))
        if page < total_pages:
            nav.append(InlineKeyboardButton(text="Berikutnya ▶", callback_data=f"pending_page_{page+1}"))
        if nav:
            await callback.message.answer("Navigasi:", reply_markup=InlineKeyboardMarkup(inline_keyboard=[nav]))
    await callback.answer()

@router.callback_query(F.data.startswith("pending_page_"))
async def pending_page(callback: CallbackQuery):
    page = int(callback.data.split("_")[2])
    await pending_orders(callback, page)

# ========== RIWAYAT PESANAN (FILTER) ==========
@router.callback_query(F.data == "orders_history")
async def history_filter(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Semua", callback_data="orders_filter_all")],
        [InlineKeyboardButton(text="⏳ Pending", callback_data="orders_filter_pending")],
        [InlineKeyboardButton(text="✅ Disetujui", callback_data="orders_filter_approved")],
        [InlineKeyboardButton(text="❌ Ditolak", callback_data="orders_filter_rejected")],
        [InlineKeyboardButton(text="« Kembali", callback_data="admin_orders")]
    ])
    await callback.message.edit_text("📜 *Riwayat Pesanan*\nPilih filter:", parse_mode="Markdown", reply_markup=keyboard)
    await callback.answer()

@router.callback_query(F.data.startswith("orders_filter_"))
async def show_orders_by_filter(callback: CallbackQuery, page: int = 1):
    filter_status = callback.data.split("_")[2]
    if filter_status == "all":
        status = None
    else:
        status = filter_status
    offset = (page - 1) * ITEMS_PER_PAGE
    orders, total = await get_orders_by_status(status, ITEMS_PER_PAGE, offset)
    total_pages = (total + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
    if not orders:
        await callback.message.edit_text("📭 Tidak ada pesanan.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="« Kembali", callback_data="admin_orders")]]))
        await callback.answer()
        return
    text = f"📜 *Riwayat Pesanan* (Halaman {page}/{total_pages})\n\n"
    for order in orders:
        order_id, user_id, variant_id, qty, total_price, three_digits, proof, status, created_at = order
        variant = await get_product_variant(variant_id)
        product_name = variant[1] if variant else "?"
        variant_name = variant[2] if variant else "?"
        text += (
            f"🆔 `{order_id}` | {status}\n"
            f"👤 {user_id}\n"
            f"📦 {product_name} - {variant_name}\n"
            f"💰 Rp{format_rupiah(total_price)} | Jml: {qty}\n"
            f"🕒 {created_at[:16]}\n\n"
        )
    # Navigasi halaman
    nav = []
    if page > 1:
        nav.append(InlineKeyboardButton(text="◀ Sebelumnya", callback_data=f"history_page_{filter_status}_{page-1}"))
    if page < total_pages:
        nav.append(InlineKeyboardButton(text="Berikutnya ▶", callback_data=f"history_page_{filter_status}_{page+1}"))
    keyboard = InlineKeyboardMarkup(inline_keyboard=[nav, [InlineKeyboardButton(text="« Kembali", callback_data="admin_orders")]]) if nav else InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="« Kembali", callback_data="admin_orders")]])
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)
    await callback.answer()

@router.callback_query(F.data.startswith("history_page_"))
async def history_page(callback: CallbackQuery):
    parts = callback.data.split("_")
    filter_status = parts[2]
    page = int(parts[3])
    # Simulasi callback palsu
    class DummyCallback:
        data = f"orders_filter_{filter_status}"
    await show_orders_by_filter(DummyCallback(), page)

# ========== LIHAT BUKTI ==========
@router.callback_query(F.data.startswith("admin_proof_"))
async def show_proof(callback: CallbackQuery):
    order_id = callback.data.split("_")[2]
    order = await get_order_by_id(order_id)
    if not order or not order[6]:
        await callback.answer("Bukti tidak ditemukan.", show_alert=True)
        return
    await bot.send_photo(callback.from_user.id, order[6], caption=f"📸 Bukti pembayaran untuk order {order_id}")
    await callback.answer()

# ========== SETUJUI ==========
@router.callback_query(F.data.startswith("admin_approve_"))
async def admin_approve(callback: CallbackQuery):
    order_id = callback.data.split("_")[2]
    order = await get_order_by_id(order_id)
    if not order or order[7] != 'pending':
        await callback.answer("❌ Pesanan tidak valid atau sudah diproses.", show_alert=True)
        return
    variant_id = order[2]
    item = await get_available_item(variant_id)
    if not item:
        await callback.message.answer(f"❌ Stok habis untuk pesanan {order_id}. Tidak dapat menyetujui.")
        await callback.answer("Stok habis", show_alert=True)
        return
    item_id, code = item
    await mark_item_used(item_id, order_id)
    await update_order_status(order_id, 'approved')
    user_id = order[1]
    try:
        await bot.send_message(user_id, f"✅ *Pesanan {order_id} disetujui!*\n\nKode Anda: `{code}`\nTerima kasih telah berbelanja.", parse_mode="Markdown")
        await callback.message.edit_text(f"✅ Pesanan {order_id} telah disetujui. Kode sudah dikirim ke user.", reply_markup=None)
    except Exception as e:
        await callback.message.edit_text(f"✅ Pesanan {order_id} disetujui, tetapi gagal mengirim kode: {e}", reply_markup=None)
    await callback.answer()

# ========== TOLAK ==========
@router.callback_query(F.data.startswith("admin_reject_"))
async def admin_reject(callback: CallbackQuery):
    order_id = callback.data.split("_")[2]
    order = await get_order_by_id(order_id)
    if not order or order[7] != 'pending':
        await callback.answer("❌ Pesanan tidak valid atau sudah diproses.", show_alert=True)
        return
    await update_order_status(order_id, 'rejected')
    user_id = order[1]
    try:
        await bot.send_message(user_id, f"❌ *Pesanan {order_id} ditolak.*\nSilakan hubungi admin untuk informasi lebih lanjut.", parse_mode="Markdown")
        await callback.message.edit_text(f"❌ Pesanan {order_id} ditolak. User sudah diberi tahu.", reply_markup=None)
    except Exception as e:
        await callback.message.edit_text(f"❌ Pesanan {order_id} ditolak, tetapi gagal notifikasi user: {e}", reply_markup=None)
    await callback.answer()