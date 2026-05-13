from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from source.states.user_state import UserState
from source.utils.helpers import format_rupiah
from source.database.queries import get_config

router = Router()

def build_product_keyboard(qty: int):
    """Keyboard dengan plus/minus, tombol lanjutkan, dan kembali"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="➖", callback_data="qty_minus"),
            InlineKeyboardButton(text=str(qty), callback_data="qty_ignore"),   # hanya angka
            InlineKeyboardButton(text="➕", callback_data="qty_plus"),
        ],
        [
            InlineKeyboardButton(text="✅ Lanjutkan", callback_data="go_confirm"),
        ],
        [
            InlineKeyboardButton(text="« Kembali", callback_data="back_to_subcategories"),
        ]
    ])

async def send_quantity_message(message: Message, state: FSMContext):
    """Kirim pesan P3 (bisa dengan banner)"""
    data = await state.get_data()
    has_banner = data.get('has_banner', False)
    banner_id = await get_config("banner_image_file_id")
    cat_name = data.get('selected_category_name', 'Kategori')
    sub_name = data.get('selected_sub_name', 'Produk')
    price = data.get('price', 0)
    stock = data.get('stock', 0)
    qty = data.get('qty', 1)
    total = price * qty

    text = (
    "🛒 <b>ATUR JUMLAH PESANAN</b>\n"
    "━━━━━━━━━━━━━━\n"

    "<pre>"
    f"📂 Kategori : {cat_name}\n"
    f"📦 Produk   : {sub_name}\n"
    f"💵 Harga    : Rp{format_rupiah(price)}\n"
    f"📦 Stock    : {stock}\n"
    f"💰 Total    : Rp{format_rupiah(total)}\n"
    "</pre>"
    
    "➡️ Atur jumlah pesanan dengan tombol di bawah👇")
    
    keyboard = build_product_keyboard(qty)

    if has_banner and banner_id:
        await message.answer_photo(banner_id, caption=text, parse_mode="HTML", reply_markup=keyboard)
    else:
        await message.answer(text, parse_mode="HTML", reply_markup=keyboard)

    await state.update_data(qty=qty, total_price=total)
    await state.set_state(UserState.input_quantity)


# ===== HANDLER PLUS / MINUS =====
@router.callback_query(UserState.input_quantity, F.data.in_({"qty_plus", "qty_minus", "qty_ignore"}))
async def adjust_quantity(callback: CallbackQuery, state: FSMContext):
    if callback.data == "qty_ignore":
        await callback.answer()   # hanya hilangkan loading
        return

    await callback.answer()
    data = await state.get_data()
    qty = data.get('qty', 1)
    stock = data.get('stock', 0)
    price = data.get('price', 0)

    if callback.data == "qty_plus":
        if qty < stock:
            qty += 1
    elif callback.data == "qty_minus":
        if qty > 1:
            qty -= 1

    total = price * qty
    await state.update_data(qty=qty, total_price=total)

    cat_name = data.get('selected_category_name', 'Kategori')
    sub_name = data.get('selected_sub_name', 'Produk')

    text = (
    "🛒 <b>ATUR JUMLAH PESANAN</b>\n"
    "━━━━━━━━━━━━━━\n"

    "<pre>"
    f"📂 Kategori : {cat_name}\n"
    f"📦 Produk   : {sub_name}\n"
    f"💵 Harga    : Rp{format_rupiah(price)}\n"
    f"📦 Stock    : {stock}\n"
    f"💰 Total    : Rp{format_rupiah(total)}\n"
    "</pre>"
    
    "👇 Atur jumlah pesanan dengan tombol di bawah")
    
    keyboard = build_product_keyboard(qty)
    
    if callback.message.photo:
        await callback.message.edit_caption(
            caption=text,
            parse_mode="HTML",
            reply_markup=keyboard)
    else:
        await callback.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=keyboard)

# ===== TOMBOL LANJUTKAN =====
@router.callback_query(UserState.input_quantity, F.data == "go_confirm")
async def go_to_confirm(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    # Hapus pesan P3
    await callback.message.delete()

    # Panggil P4 – langsung fungsi send_qris_message dari p4_confirm
    from source.handlers.user.p4_qris import send_qris_message
    await send_qris_message(callback.message, state, user_id=callback.from_user.id)
    await state.set_state(UserState.confirming)   # pastikan state berubah

# ===== TOMBOL KEMBALI =====
@router.callback_query(UserState.input_quantity, F.data == "back_to_subcategories")
async def back_to_subcategories(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    category_id = data.get('selected_category_id')

    # Render ulang subkategori (edit pesan saat ini)
    from source.handlers.user.p2_subcategory import show_subcategories_by_edit
    await show_subcategories_by_edit(callback, state, category_id, page=1)

    # Kembalikan state agar tombol angka/pagination berfungsi
    await state.set_state(UserState.selecting_subcategory)