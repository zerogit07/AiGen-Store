from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from source.states.user_state import UserState
from source.database.queries import (
    update_order_payment_proof, get_order_by_id, get_order_details,
    get_available_item, mark_item_used, update_order_status, is_user_registered
)
from source.utils.helpers import format_rupiah
from source.config import ADMIN_ID, BOT_TOKEN

router = Router()
bot = Bot(token=BOT_TOKEN)

@router.message(UserState.waiting_proof, F.photo)
async def receive_proof(message: Message, state: FSMContext):
    data = await state.get_data()
    order_id = data.get('waiting_proof_order_id')
    if not order_id:
        await message.answer("❌ Sesi tidak valid. Silakan mulai pesanan ulang dengan /start")
        await state.clear()
        return

    # ── Ambil order dulu untuk validasi ──
    order = await get_order_by_id(order_id)
    if not order:
        await message.answer("❌ Pesanan tidak ditemukan.")
        await state.clear()
        return

    order_user_id = order[1]  # indeks 1 = user_id

    # ── PAGAR VALIDASI ────────────────
    if not await is_user_registered(order_user_id):
        await message.answer("⚠️ Anda belum terdaftar. Silakan ketik /start terlebih dahulu.")
        await state.clear()
        return

    if message.from_user.id != order_user_id:
        await message.answer("❌ Anda tidak memiliki akses ke pesanan ini.")
        await state.clear()
        return
    # ──────────────────────────────────

    # ── Simpan bukti pembayaran ────────
    file_id = message.photo[-1].file_id
    await update_order_payment_proof(order_id, file_id)

    # ── Siapkan notifikasi untuk admin ──
    user_id = order_user_id
    qty = order[3]
    total = order[4]
    three_digits = order[5]
    sub_name, cat_name = await get_order_details(order[2])

    caption = (
        f"🆕 *Pesanan Baru!*\n\n"
        f"📦 Order ID: `{order_id}`\n"
        f"👤 User ID: `{user_id}`\n"
        f"📂 Kategori: {cat_name}\n"
        f"📦 Subkategori: {sub_name}\n"
        f"🔢 Jumlah: {qty}\n"
        f"💰 Total: Rp{format_rupiah(total)}\n"
        f"🔑 Kode Unik: {three_digits}"
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Setujui", callback_data=f"approve_{order_id}"),
         InlineKeyboardButton(text="❌ Tolak", callback_data=f"reject_{order_id}")]
    ])

    # Kirim ke admin
    await bot.send_photo(ADMIN_ID, photo=file_id, caption=caption,
                         parse_mode="Markdown", reply_markup=keyboard)

    await message.answer("✅ Bukti pembayaran telah diterima. Admin akan segera memproses. Terima kasih!")
    await state.clear()


@router.callback_query(F.data.startswith("approve_"))
async def approve_order(callback: CallbackQuery):

    # Validasi admin
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Unauthorized", show_alert=True)
        return

    # Ambil order_id dari callback
    order_id = callback.data.split("_", 1)[1]

    # Ambil data order
    order = await get_order_by_id(order_id)

    # Validasi order
    if not order or order[7] != 'pending':
        await callback.answer(
            "❌ Pesanan tidak valid atau sudah diproses.",
            show_alert=True
        )
        return

    # Data order
    user_id = order[1]
    subcategory_id = order[2]
    qty = order[3]

    # Ambil stok sesuai qty
    items = await get_available_item(subcategory_id, qty)

    # Validasi stok
    if len(items) < qty:
        await callback.message.edit_reply_markup(reply_markup=None)

        await callback.message.answer(
            f"❌ Stok tidak cukup untuk pesanan {order_id}.\n\n"
            f"📦 Diminta: {qty}\n"
            f"📦 Tersedia: {len(items)}"
        )

        await callback.answer("Stok tidak cukup", show_alert=True)
        return

    # Hilangkan tombol approve/reject agar tidak double click
    await callback.message.edit_reply_markup(reply_markup=None)

    codes = []

    # Tandai semua item sebagai used
    for item_id, code in items:
        await mark_item_used(item_id, order_id)
        codes.append(code)

    # Update status order
    await update_order_status(order_id, 'approved')

    # Format semua kode
    codes_text = "\n".join(
        [f"{i+1}. `{code}`" for i, code in enumerate(codes)]
    )

    # Kirim kode ke user
    try:
        await bot.send_message(
            user_id,
            f"✅ *Pesanan {order_id} disetujui!*\n\n"
            f"📦 Jumlah: {qty}\n\n"
            f"🔑 Kode Anda:\n{codes_text}\n\n"
            f"Terima kasih telah berbelanja.",
            parse_mode="Markdown"
        )

        await callback.message.answer(
            f"✅ Pesanan {order_id} telah DISETUJUI.\n"
            f"📦 {qty} item berhasil dikirim ke user."
        )

    except Exception as e:
        await callback.message.answer(
            f"⚠️ Pesanan {order_id} disetujui, "
            f"tetapi gagal mengirim kode ke user:\n{e}"
        )

    await callback.answer()

@router.callback_query(F.data.startswith("reject_"))
async def reject_order(callback: CallbackQuery):
    order_id = callback.data.split("_")[1]
    order = await get_order_by_id(order_id)
    if not order or order[7] != 'pending':
        await callback.answer("❌ Pesanan tidak valid atau sudah diproses.", show_alert=True)
        return

    await update_order_status(order_id, 'rejected')
    user_id = order[1]  # indeks 1 = user_id

    try:
        await bot.send_message(user_id,
            f"❌ *Pesanan {order_id} ditolak.*\nSilakan hubungi admin untuk informasi lebih lanjut.",
            parse_mode="Markdown")
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.answer(f"❌ Pesanan {order_id} telah DITOLAK.")
    except Exception as e:
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.answer(f"⚠️ Pesanan {order_id} ditolak, tetapi gagal notifikasi user: {e}")
    await callback.answer()
