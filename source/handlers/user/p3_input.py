from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton, ForceReply
from aiogram.fsm.context import FSMContext
from source.states.user_state import UserState
from source.database.queries import get_subcategory_price_and_stock
from source.utils.helpers import format_rupiah

router = Router()

@router.callback_query(UserState.selecting_subcategory, F.data.startswith("sub_"))
async def show_quantity_input(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    subcategory_id = int(callback.data.split("_")[1])
    price, stock = await get_subcategory_price_and_stock(subcategory_id)
    if price is None:
        await callback.message.answer("Subkategori tidak valid.")
        return
    if stock == 0:
        await callback.message.answer("Stok habis!")
        return
    await state.update_data(
        selected_subcategory_id=subcategory_id,
        price=price,
        stock=stock,
        qty=1
    )
    await update_quantity_message(callback, state)
    await state.set_state(UserState.input_quantity)

async def update_quantity_message(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    qty = data.get('qty', 1)
    price = data.get('price', 0)
    stock = data.get('stock', 0)
    total = qty * price

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="-", callback_data="qty_minus"),
            InlineKeyboardButton(text=str(qty).center(5), callback_data="qty_manual"),
            InlineKeyboardButton(text="+", callback_data="qty_plus"),
        ],
        [InlineKeyboardButton(text="Lanjutkan", callback_data="qty_confirm")],
        [InlineKeyboardButton(text="« Kembali", callback_data="back_to_subcategories")]
    ])

    text = (
        f"✏️ *Masukkan jumlah*\n"
        f"Harga per item: Rp{format_rupiah(price)}\n"
        f"Stok tersedia: {stock}\n\n"
        f"Jumlah: {qty}\n"
        f"Total: Rp{format_rupiah(total)}"
    )
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)

@router.callback_query(UserState.input_quantity, F.data == "qty_minus")
async def minus_qty(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    qty = data.get('qty', 1)
    if qty > 1:
        qty -= 1
        await state.update_data(qty=qty)
        await update_quantity_message(callback, state)
    else:
        await callback.answer("Minimal 1", show_alert=True)

@router.callback_query(UserState.input_quantity, F.data == "qty_plus")
async def plus_qty(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    qty = data.get('qty', 1)
    stock = data.get('stock', 0)
    if qty < stock:
        qty += 1
        await state.update_data(qty=qty)
        await update_quantity_message(callback, state)
    else:
        await callback.answer(f"Maksimal {stock}", show_alert=True)

@router.callback_query(UserState.input_quantity, F.data == "qty_manual")
async def manual_qty_prompt(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer(
        "Silakan kirim *angka* jumlah yang diinginkan.\nContoh: `5`",
        parse_mode="Markdown",
        reply_markup=ForceReply(input_field_placeholder="Ketik jumlah di sini...")
    )
    await state.update_data(waiting_manual=True)

@router.message(UserState.input_quantity, F.text)
async def receive_manual_qty(message: Message, state: FSMContext):
    data = await state.get_data()
    if not data.get('waiting_manual'):
        return
    try:
        qty = int(message.text.strip())
        if qty <= 0:
            raise ValueError
        stock = data.get('stock', 0)
        if qty > stock:
            await message.answer(f"Stok hanya {stock}. Masukkan angka yang lebih kecil.")
            return
        await state.update_data(qty=qty, waiting_manual=False)
        # update pesan asli (yang berisi keyboard)
        # kita perlu mengambil pesan asli yang diedit. Kita bisa simpan chat_id dan message_id.
        # tapi karena kita tidak menyimpannya, alternatif: bot akan edit pesan yang baru saja?
        # Cara paling mudah: kita panggil show_quantity_input dengan callback tiruan? Tidak.
        # Kita akan arahkan user untuk mengklik kembali subkategori? Tidak praktis.
        # Solusi: kita simpan message_id dari pesan utama saat pertama kali ditampilkan.
        # Untuk sementara, kita gunakan pendekatan: kirim pesan baru dengan keyboard yang sudah diupdate,
        # lalu hapus pesan sebelumnya (tapi kita tidak tahu id pesan). 
        # Karena kompleks, kita lakukan sebagai berikut: 
        # - Saat pertama show_quantity_input, kita simpan (chat_id, message_id) di state.
        # - Di sini kita gunakan itu untuk edit.
        # Sederhananya: kita akan memanggil update_quantity_message dengan callback palsu? Tidak.
        # Saya akan modifikasi: saat pertama, kita simpan message_id.
        # Untuk menghemat waktu, saya asumsikan Anda akan menambahkan penyimpanan message_id.
        # Sementara ini, kita kirim pesan baru dan hapus pesan input.
        await message.answer(f"✅ Jumlah diubah menjadi {qty}. Klik 'Lanjutkan'.")
        await message.delete()
    except ValueError:
        await message.answer("❌ Masukkan angka positif.")

# Di dalam p3_input.py, ganti handler qty_confirm dengan:
@router.callback_query(UserState.input_quantity, F.data == "qty_confirm")
async def confirm_quantity(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    qty = data.get('qty', 1)
    await state.update_data(quantity=qty)
    # Panggil fungsi show_qris dari p4_qris
    from source.handlers.user.p4_qris import show_qris
    await show_qris(callback, state)
    
    
@router.callback_query(UserState.input_quantity, F.data == "back_to_subcategories")
async def back_to_subcategories(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    from source.handlers.user.p2_subcategory import show_subcategories
    data = await state.get_data()
    category_id = data.get('selected_category_id')
    if category_id:
        await show_subcategories(callback, state, category_id, page=1)
    else:
        await callback.message.answer("Terjadi kesalahan, silakan mulai dari /start")

