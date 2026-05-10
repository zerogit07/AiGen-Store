from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from source.states.user_state import UserState
from source.database.queries import (
    update_order_payment_proof, get_order_by_id, get_order_details,
    get_available_item, mark_item_used, update_order_status
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

    file_id = message.photo[-1].file_id
    await update_order_payment_proof(order_id, file_id)

    order = await get_order_by_id(order_id)
    if order:
        user_id = order[1]
        qty = order[3]
        total = order[4]
        three_digits = order[5]
        sub_name, cat_name = await get_order_details(order[2])
        text = (
            f"🆕 *Pesanan Baru!*\n"
            f"Order ID: `{order_id}`\n"
            f"User ID: `{user_id}`\n"
            f"Kategori: {cat_name}\n"
            f"Subkategori: {sub_name}\n"
            f"Jumlah: {qty}\n"
            f"Total: Rp{format_rupiah(total)}\n"
            f"Kode Unik: {three_digits}\n\n"
            f"Klik tombol di bawah untuk memproses."
        )
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Setujui", callback_data=f"approve_{order_id}"),
             InlineKeyboardButton(text="❌ Tolak", callback_data=f"reject_{order_id}")]
        ])
        # Kirim foto bukti terlebih dahulu
        await bot.send_photo(ADMIN_ID, photo=file_id, caption="📸 *Bukti Pembayaran*", parse_mode="Markdown")
        # Kirim pesan teks dengan keyboard
        await bot.send_message(ADMIN_ID, text, parse_mode="Markdown", reply_markup=keyboard)

    await message.answer("✅ Bukti pembayaran telah diterima. Admin akan segera memproses. Terima kasih!")
    await state.clear()

@router.callback_query(F.data.startswith("approve_"))
async def approve_order(callback: CallbackQuery):
    order_id = callback.data.split("_")[1]
    order = await get_order_by_id(order_id)
    if not order or order[7] != 'pending':
        await callback.answer("❌ Pesanan tidak valid atau sudah diproses.", show_alert=True)
        return
    subcategory_id = order[2]
    item = await get_available_item(subcategory_id)
    if not item:
        await callback.message.edit_text(f"❌ Stok habis untuk pesanan {order_id}. Tidak dapat menyetujui.", reply_markup=None)
        await callback.answer("Stok habis", show_alert=True)
        return
    item_id, code = item
    await mark_item_used(item_id, order_id)
    await update_order_status(order_id, 'approved')
    user_id = order[1]
    try:
        await bot.send_message(user_id, f"✅ *Pesanan {order_id} disetujui!*\n\nKode Anda:\n `{code}`\nTerima kasih telah berbelanja.", parse_mode="Markdown")
        await callback.message.edit_text(f"✅ *Pesanan {order_id} telah DISETUJUI.*\nKode sudah dikirim ke user.", parse_mode="Markdown", reply_markup=None)
    except Exception as e:
        await callback.message.edit_text(f"⚠️ Pesanan {order_id} disetujui, tetapi gagal mengirim kode ke user: {e}", reply_markup=None)
        await bot.send_message(ADMIN_ID, f"❌ Gagal mengirim kode untuk pesanan {order_id}. Error: {e}")
    await callback.answer()

@router.callback_query(F.data.startswith("reject_"))
async def reject_order(callback: CallbackQuery):
    order_id = callback.data.split("_")[1]
    order = await get_order_by_id(order_id)
    if not order or order[7] != 'pending':
        await callback.answer("❌ Pesanan tidak valid atau sudah diproses.", show_alert=True)
        return
    await update_order_status(order_id, 'rejected')
    user_id = order[1]
    try:
        await bot.send_message(user_id, f"❌ *Pesanan {order_id} ditolak.*\nSilakan hubungi admin untuk informasi lebih lanjut.", parse_mode="Markdown")
        await callback.message.edit_text(f"❌ *Pesanan {order_id} telah DITOLAK.*", parse_mode="Markdown", reply_markup=None)
    except Exception as e:
        await callback.message.edit_text(f"⚠️ Pesanan {order_id} ditolak, tetapi gagal notifikasi user: {e}", reply_markup=None)
        await bot.send_message(ADMIN_ID, f"❌ Gagal mengirim notifikasi penolakan untuk pesanan {order_id}. Error: {e}")
    await callback.answer()