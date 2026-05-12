from aiogram import Router, F
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
    # ── TAMBAHAN BARU ──
    get_order_ids_by_status,
    bulk_update_orders_status,
    hard_delete_orders_by_status,
)
from source.utils.helpers import format_rupiah
from source.config import BOT_TOKEN, ADMIN_ID

router = Router()

# ── Konstanta ─────────────────────────────────
ITEMS_PER_PAGE = 10


# ── Helper Keyboard ───────────────────────────
def main_menu_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📦 Pesanan Pending", callback_data="orders_pending")],
        [InlineKeyboardButton(text="📜 Riwayat Pesanan", callback_data="orders_history")],
        [InlineKeyboardButton(text="« Kembali ke Panel", callback_data="admin_back")]
    ])


def history_filter_keyboard():
    # ❌ "Pending" dihapus dari filter riwayat
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Semua", callback_data="history_all"),
         InlineKeyboardButton(text="Disetujui", callback_data="history_approved"),
         InlineKeyboardButton(text="Ditolak", callback_data="history_rejected")],
        [InlineKeyboardButton(text="« Kembali", callback_data="admin_orders")]
    ])


# ── Entry: Menu Utama ─────────────────────────
@router.callback_query(F.data == "admin_orders")
async def orders_main_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "🛒 *Manajemen Pesanan*\n\nPilih menu:",
        parse_mode="Markdown",        reply_markup=main_menu_keyboard()
    )
    await callback.answer()


# ═══════════════════════════════════════════════
# 📦 PESANAN PENDING (UPDATED)
# ═══════════════════════════════════════════════

@router.callback_query(F.data == "orders_pending")
async def pending_entry(callback: CallbackQuery, state: FSMContext):
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
    keyboard_rows = []

    # ── Render PER ORDER: Detail + 3 Tombol Inline ──
    for order in orders:
        order_id, user_id, item_id, qty, total_price, three_digits, payment_proof, status = order
        sub_name, cat_name = await get_order_details(item_id)
        
        text += (
            f"🔹 `{order_id}` | User: `{user_id}`\n"
            f"   {cat_name} → {sub_name} (x{qty})\n"
            f"   Total: Rp{format_rupiah(total_price)}\n\n"
        )
        # 3 tombol per order dalam 1 baris inline
        keyboard_rows.append([
            InlineKeyboardButton(text="✅ Setujui", callback_data=f"approve_{order_id}"),
            InlineKeyboardButton(text="❌ Tolak", callback_data=f"reject_{order_id}"),
            InlineKeyboardButton(text="📷 Bukti", callback_data=f"view_proof_{order_id}")
        ])
    nav = []
    # ── Navigasi Halaman ──    nav = []
    if page > 1:
        nav.append(InlineKeyboardButton(text="◀", callback_data=f"pending_page_{page-1}"))
    if page < total_pages:
        nav.append(InlineKeyboardButton(text="▶", callback_data=f"pending_page_{page+1}"))
    if nav:
        keyboard_rows.append(nav)

    # ── ⭐ BARU: Bulk Action Buttons ──
    keyboard_rows.append([
        InlineKeyboardButton(text="✅ Setujui Semua", callback_data=f"bulk_approve_{page}"),
        InlineKeyboardButton(text="❌ Tolak Semua", callback_data=f"bulk_reject_{page}")
    ])

    # ── Tombol Kembali ──
    keyboard_rows.append([InlineKeyboardButton(text="« Kembali", callback_data="admin_orders")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_rows)

    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)
    await state.update_data(pending_page=page)
    await callback.answer()


@router.callback_query(F.data.startswith("pending_page_"))
async def pending_nav(callback: CallbackQuery, state: FSMContext):
    page = int(callback.data.split("_")[2])
    await show_pending_page(callback, page, state)


# ── ⭐ BARU: Bulk Action Handlers (Pending) ──

@router.callback_query(F.data.startswith("bulk_approve_"))
async def bulk_approve_prompt(callback: CallbackQuery, state: FSMContext):
    """Step 1: Konfirmasi bulk approve"""
    page = int(callback.data.split("_")[2])
    offset = (page - 1) * ITEMS_PER_PAGE
    
    # Ambil order_ids di halaman ini untuk konfirmasi
    order_ids = await get_order_ids_by_status("pending", ITEMS_PER_PAGE, offset)
    
    await state.update_data(
        bulk_action="approve",
        bulk_page=page,
        bulk_order_ids=order_ids  # Simpan untuk eksekusi
    )
    
    await callback.message.edit_text(
        f"⚠️ *Konfirmasi Bulk Approve*\n\n"
        f"Anda akan menyetujui **{len(order_ids)} pesanan** di halaman ini.\n"        f"Tindakan ini tidak bisa dibatalkan.\n\n"
        f"Lanjutkan?",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Ya, Setujui Semua", callback_data="bulk_approve_confirm")],
            [InlineKeyboardButton(text="❌ Batal", callback_data=f"pending_page_{page}")]
        ])
    )
    await callback.answer()


@router.callback_query(F.data == "bulk_approve_confirm")
async def bulk_approve_execute(callback: CallbackQuery, state: FSMContext):
    """Step 2: Eksekusi bulk approve"""
    data = await state.get_data()
    order_ids = data.get("bulk_order_ids", [])
    page = data.get("bulk_page", 1)
    
    if not order_ids:
        await callback.answer("Tidak ada pesanan untuk diproses.", show_alert=True)
        await show_pending_page(callback, page, state)
        return
    
    # Proses satu per satu (dengan safety: cek stok & kirim DM)
    success, failed = 0, 0
    for order_id in order_ids:
        order = await get_order_by_id(order_id)
        if not order or order[7] != 'pending':
            failed += 1
            continue
            
        sub_id = await get_item_subcategory(order[2])
        item = await get_available_item(sub_id)
        if not item:
            failed += 1  # Stok habis
            continue
            
        item_id, code = item
        await mark_item_used(item_id, order_id)
        await update_order_status(order_id, 'approved')
        
        # Kirim DM ke user (dengan fallback aman)
        user_id = order[1]
        try:
            if user_id != ADMIN_ID:  # Skip kalau testing mandiri
                await callback.bot.send_message(
                    user_id, 
                    f"✅ Pesanan {order_id} disetujui!\nKode Anda: {code}",
                    parse_mode="Markdown"
                )            
                success += 1
        except Exception:
            # Gagal kirim DM, tapi order tetap approved
            success += 1  # Hitung sebagai success karena DB sudah update
    
    # ⚡ Langsung refresh UI (sesuai request: no summary)
    await state.clear()  # Cleanup state bulk
    await show_pending_page(callback, page, state)
    await callback.answer(f"✅ {success} disetujui, {failed} gagal")


@router.callback_query(F.data.startswith("bulk_reject_"))
async def bulk_reject_prompt(callback: CallbackQuery, state: FSMContext):
    """Step 1: Konfirmasi bulk reject"""
    page = int(callback.data.split("_")[2])
    offset = (page - 1) * ITEMS_PER_PAGE
    order_ids = await get_order_ids_by_status("pending", ITEMS_PER_PAGE, offset)
    
    await state.update_data(
        bulk_action="reject",
        bulk_page=page,
        bulk_order_ids=order_ids
    )
    
    await callback.message.edit_text(
        f"⚠️ *Konfirmasi Bulk Reject*\n\n"
        f"Anda akan menolak **{len(order_ids)} pesanan** di halaman ini.\n"
        f"Tindakan ini tidak bisa dibatalkan.\n\n"
        f"Lanjutkan?",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Ya, Tolak Semua", callback_data="bulk_reject_confirm")],
            [InlineKeyboardButton(text="❌ Batal", callback_data=f"pending_page_{page}")]
        ])
    )
    await callback.answer()


@router.callback_query(F.data == "bulk_reject_confirm")
async def bulk_reject_execute(callback: CallbackQuery, state: FSMContext):
    """Step 2: Eksekusi bulk reject"""
    data = await state.get_data()
    order_ids = data.get("bulk_order_ids", [])
    page = data.get("bulk_page", 1)
    
    if not order_ids:
        await callback.answer("Tidak ada pesanan untuk diproses.", show_alert=True)
        await show_pending_page(callback, page, state)
        return
        success, failed = 0, 0
    for order_id in order_ids:
        order = await get_order_by_id(order_id)
        if not order or order[7] != 'pending':
            failed += 1
            continue
            
        await update_order_status(order_id, 'rejected')
        
        # Kirim DM reject (dengan fallback)
        user_id = order[1]
        try:
            if user_id != ADMIN_ID:
                await callback.bot.send_message(
                    user_id,
                    f"❌ Pesanan {order_id} ditolak. Hubungi admin.",
                    parse_mode="Markdown"
                )
            success += 1
        except Exception:
            success += 1  # Tetap hitung success
    
    await state.clear()
    await show_pending_page(callback, page, state)
    await callback.answer(f"✅ {success} ditolak, {failed} gagal")


# ═══════════════════════════════════════════════
# 📜 RIWAYAT PESANAN (UPDATED)
# ═══════════════════════════════════════════════

@router.callback_query(F.data == "orders_history")
async def history_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "📜 *Riwayat Pesanan*\n\nPilih filter:",
        parse_mode="Markdown",
        reply_markup=history_filter_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("history_"))
async def history_filter(callback: CallbackQuery, state: FSMContext):
    status = callback.data.split("_")[1]
    status = None if status == "all" else status
    await show_history_page(callback, status, 1, state)


async def show_history_page(callback: CallbackQuery, status, page: int, state: FSMContext):
    offset = (page - 1) * ITEMS_PER_PAGE
    orders, total = await get_orders_by_status(status, limit=ITEMS_PER_PAGE, offset=offset)
    
    # ✅ GANTI BARIS INI DENGAN RUMUS ASLI:
    total_pages = max((total + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE, 1)

    if not orders:
        await callback.message.edit_text(
            "📜 Tidak ada pesanan.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="« Kembali", callback_data="orders_history")]
            ])
        )
        return

    # ... sisa kode render text & keyboard ...

    filter_label = "Semua" if status is None else status.capitalize()
    text = f"📜 *Riwayat Pesanan* (Filter: {filter_label}) (Hal {page}/{total_pages})\n\n"
    
    for order in orders:
        order_id, user_id, item_id, qty, total_price, three_digits, proof, order_status = order
        sub_name, cat_name = await get_order_details(item_id)
        status_icon = "✅" if order_status == "approved" else "❌"
        text += (
            f"🔹 `{order_id}` | User: `{user_id}` | {status_icon} {order_status}\n"
            f"   {cat_name} → {sub_name} (x{qty}) - Rp{format_rupiah(total_price)}\n\n"
        )

    # Navigasi
    nav = []
    if page > 1:
        nav.append(InlineKeyboardButton(text="◀", callback_data=f"histpage_{status or 'all'}_{page-1}"))
    if page < total_pages:
        nav.append(InlineKeyboardButton(text="▶", callback_data=f"histpage_{status or 'all'}_{page+1}"))
    
    keyboard_rows = [nav] if nav else []
    
    # ── ⭐ BARU: Tombol Hapus Riwayat ──
    keyboard_rows.append([
        InlineKeyboardButton(text="🗑️ Hapus Riwayat", callback_data=f"delete_history_{status or 'all'}_{page}")
    ])
    
    keyboard_rows.append([InlineKeyboardButton(text="« Kembali", callback_data="orders_history")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_rows)

    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)
    await state.update_data(history_status=status, history_page=page)
    await callback.answer()


@router.callback_query(F.data.startswith("histpage_"))
async def history_nav(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    status = parts[1] if parts[1] != 'all' else None  # ✅ Indentasi 4 spasi
    page = int(parts[2])                               # ✅ Indentasi 4 spasi
    await show_history_page(callback, status, page, state)  # ✅ Indentasi 4 spasi

# ── ⭐ BARU: Hard Delete History Handler ──

@router.callback_query(F.data.startswith("delete_history_"))
async def delete_history_prompt(callback: CallbackQuery, state: FSMContext):
    """Step 1: Konfirmasi hapus riwayat"""
    parts = callback.data.split("_")
    status = parts[2] if parts[2] != 'all' else None
    page = int(parts[3])
    
    await state.update_data(
        delete_action="hard_delete",
        delete_filter=status,
        delete_page=page
    )
    
    filter_label = "SEMUA" if status is None else status
    await callback.message.edit_text(
        f"🗑️ *Konfirmasi Hapus Riwayat*\n\n"
        f"Anda akan menghapus **permanen** semua riwayat dengan filter:\n"
        f"📌 Status: `{filter_label}`\n"
        f"📌 Halaman ini saja (10 data terakhir)\n\n"
        f"⚠️ Tindakan ini TIDAK BISA dikembalikan!\n\n"
        f"Lanjutkan?",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🗑️ Ya, Hapus Permanen", callback_data="delete_history_confirm")],
            [InlineKeyboardButton(text="❌ Batal", callback_data=f"histpage_{status or 'all'}_{page}")]
        ])
    )
    await callback.answer()


@router.callback_query(F.data == "delete_history_confirm")
async def delete_history_execute(callback: CallbackQuery, state: FSMContext):
    """Step 2: Eksekusi hard delete"""
    data = await state.get_data()
    status = data.get("delete_filter")
    page = data.get("delete_page", 1)
    
    offset = (page - 1) * ITEMS_PER_PAGE
    deleted_count = await hard_delete_orders_by_status(status, ITEMS_PER_PAGE, offset)
    
    await state.clear()
    await show_history_page(callback, status, page, state)    
    await callback.answer(f"🗑️ {deleted_count} riwayat dihapus permanen")


# ═══════════════════════════════════════════════
# APPROVE / REJECT / BUKTI (PER ORDER - TETAP)
# ═══════════════════════════════════════════════

@router.callback_query(F.data.startswith("approve_"))
async def approve_handler(callback: CallbackQuery, state: FSMContext):
    # Skip kalau ini callback dari bulk action
    if callback.data in ["bulk_approve_confirm", "bulk_reject_confirm", "delete_history_confirm"]:
        return
        
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

    # Testing mandiri (admin order ke diri sendiri)
    if user_id == ADMIN_ID:
        try:
            await callback.bot.send_message(ADMIN_ID, f"🧪 [SIMULASI] Pesanan {order_id} disetujui.\nKode: {code}")
        except Exception:
            pass
        data = await state.get_data()
        page = data.get("pending_page", 1)
        await show_pending_page(callback, page, state)
        return

    # Kirim ke user asli
    try:
        await callback.bot.send_message(user_id, f"✅ Pesanan {order_id} disetujui!\nKode Anda: {code}")
    except Exception as e:
        print(f"⚠️ Gagal kirim DM ke {user_id}: {e}")
    
    # Refresh UI
    data = await state.get_data()
    page = data.get("pending_page", 1)
    await show_pending_page(callback, page, state)


@router.callback_query(F.data.startswith("reject_"))
async def reject_handler(callback: CallbackQuery, state: FSMContext):
    if callback.data in ["bulk_approve_confirm", "bulk_reject_confirm", "delete_history_confirm"]:
        return
        
    order_id = callback.data.split("_")[1]
    order = await get_order_by_id(order_id)
    if not order or order[7] != 'pending':
        await callback.answer("Pesanan tidak valid.", show_alert=True)
        return
    await update_order_status(order_id, 'rejected')
    user_id = order[1]

    if user_id == ADMIN_ID:
        try:
            await callback.bot.send_message(ADMIN_ID, f"🧪 [SIMULASI] Pesanan {order_id} ditolak.")
        except Exception:
            pass
        data = await state.get_data()
        page = data.get("pending_page", 1)
        await show_pending_page(callback, page, state)
        return

    try:
        await callback.bot.send_message(user_id, f"❌ Pesanan {order_id} ditolak. Hubungi admin.")
    except Exception as e:
        print(f"⚠️ Gagal kirim notif ke {user_id}: {e}")
    
    data = await state.get_data()
    page = data.get("pending_page", 1)
    await show_pending_page(callback, page, state)


@router.callback_query(F.data.startswith("view_proof_"))
async def view_proof_handler(callback: CallbackQuery):
    order_id = callback.data.split("_")[2]
    order = await get_order_by_id(order_id)
    if not order or not order[6]:
        await callback.answer("Bukti tidak tersedia.", show_alert=True)
        return
    file_id = order[6]
    await callback.message.answer_photo(file_id, caption=f"Bukti pembayaran untuk {order_id}")
    await callback.answer()