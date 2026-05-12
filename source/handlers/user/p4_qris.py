import uuid
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from source.states.user_state import UserState
from source.database.queries import (
    get_subcategory_name, get_category_name_by_subcategory,
    create_order, get_config
)
from source.utils.helpers import format_rupiah, generate_three_digits
from source.config import BOT_TOKEN

router = Router()
bot = Bot(token=BOT_TOKEN)

async def send_qris_message(message, state: FSMContext):
    """Kirim pesan baru untuk halaman QRIS (bisa foto atau teks)"""
    data = await state.get_data()
    subcategory_id = data.get('selected_subcategory_id')
    qty = data.get('quantity', data.get('qty', 1))
    price = data.get('price', 0)
    total = price * qty
    three_digits = generate_three_digits()
    nominal = total + int(three_digits)
    order_id = str(uuid.uuid4())[:8]
    user_id = message.from_user.id

    await create_order(order_id, user_id, subcategory_id, qty, total, three_digits)

    sub_name = await get_subcategory_name(subcategory_id)
    cat_name = await get_category_name_by_subcategory(subcategory_id)
    qris_file_id = await get_config("qris_image_file_id")

    caption = (
        f"📋 *Ringkasan Pesanan*\n"
        f"Kategori: {cat_name}\n"
        f"Subkategori: {sub_name}\n"
        f"Jumlah: {qty}\n"
        f"Total: Rp{format_rupiah(total)}\n"
        f"Kode Unik: {three_digits}\n\n"
        f"Silakan transfer ke rekening berikut:\n"
        f"**Nominal: Rp{format_rupiah(nominal)}**\n"
        f"(sudah termasuk kode unik)\n\n"
        f"Setelah transfer, klik tombol Kirim Bukti."
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📸 Kirim Bukti", callback_data=f"proof_{order_id}")],
        [InlineKeyboardButton(text="« Kembali", callback_data="back_to_quantity_from_qris")]
    ])

    if qris_file_id and qris_file_id.strip():
        await message.answer_photo(qris_file_id, caption=caption, parse_mode="Markdown", reply_markup=keyboard)
    else:
        await message.answer(caption, parse_mode="Markdown", reply_markup=keyboard)

    await state.update_data(order_id=order_id)
    await state.set_state(UserState.confirming)

@router.callback_query(UserState.confirming, F.data.startswith("proof_"))
async def proof_prompt(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    order_id = callback.data.split("_")[1]
    await state.update_data(waiting_proof_order_id=order_id)
    await callback.message.answer("📸 Silakan kirim *foto bukti transfer* (file gambar).", parse_mode="Markdown")
    await state.set_state(UserState.waiting_proof)

@router.callback_query(UserState.confirming, F.data == "back_to_quantity_from_qris")
async def back_to_quantity(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    # Hapus pesan P4 lalu kirim ulang P3
    await callback.message.delete()
    from source.handlers.user.p3_input import send_quantity_message
    # Pastikan data qty, price, stock masih ada di state
    await send_quantity_message(callback.message, state)
    await state.set_state(UserState.input_quantity)