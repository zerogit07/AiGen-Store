import uuid
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from source.states.user_state import UserState
from source.database.products import ( get_subcategory_name, get_category_name_by_subcategory, get_available_item)
from source.database.orders import create_order
from source.database.admin import get_config
from source.utils.helpers import format_rupiah, generate_three_digits
from source.config import BOT_TOKEN, ADMIN_ID

router = Router()
bot = Bot(token=BOT_TOKEN)

async def send_qris_message(message, state: FSMContext, user_id: int = None):
    # ── Tentukan user_id dengan prioritas ─────────────────
    if user_id is None:
        user_id = message.from_user.id

    # ── Ambil data dari state ─────────────────────────
    data = await state.get_data()
    subcategory_id = data.get('selected_subcategory_id')
    qty = data.get('quantity', data.get('qty', 1))
    price = data.get('price', 0)
    total = price * qty
    
    available_items = await get_available_item(subcategory_id, 1)
    if not available_items:
        await message.answer("❌ Stok habis untuk produk ini.")
        return
    item_id = available_items[0][0]   # ID item pertama yang tersedia

    three_digits = generate_three_digits()
    nominal = total + int(three_digits)
    order_id = str(uuid.uuid4())[:8]

    # ── Buat order di database ─────────────────────────
    # ✅ Hanya buat order jika BUKAN admin
    if user_id != ADMIN_ID:
        await create_order(order_id, user_id, item_id, qty, total, three_digits)
    # ── Informasi produk (TANPA LABEL SIMULASI) ───────
    sub_name = await get_subcategory_name(subcategory_id)
    cat_name = await get_category_name_by_subcategory(subcategory_id)
    qris_file_id = await get_config("qris_image_file_id")

    title = "TOTAL PEMBAYARAN".center(32)
    nominal_text = f"Rp{format_rupiah(nominal)}".center(32)
    separator_a= "━" * 17
    
    
    caption = (
    "🧾 <b>RINGKASAN PESANAN</b>\n"
    f"{separator_a}\n"
    "<pre>"
    f"📂 Kategori : {cat_name}\n"
    f"📦 Produk   : {sub_name}\n"
    f"🛒 Jumlah   : {qty}\n"
    f"💵 Harga    : Rp{format_rupiah(price)}\n"
    f"🔑 Kode     : {three_digits}\n"
    f"{title}\n"
    f"{nominal_text}"
    "</pre>"
    "➡️ Setelah pembayaran selesai,\n"
    "klik tombol <b>Kirim Bukti</b>👇")

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📸 Kirim Bukti", callback_data=f"proof_{order_id}")],
        [InlineKeyboardButton(text="« Kembali", callback_data="back_to_quantity_from_qris")]
    ])

    # ── Kirim pesan QRIS ──────────────────────────────
    if qris_file_id and qris_file_id.strip():
        await message.answer_photo(qris_file_id, caption=caption,
    parse_mode="HTML", reply_markup=keyboard)
    else:
        await message.answer(caption, parse_mode="HTML", reply_markup=keyboard)

    # ── Simpan order_id ke state ──────────────────────
    await state.update_data(order_id=order_id)
    await state.set_state(UserState.confirming)

# ── Handler untuk tombol "Kirim Bukti" ─────────────────
@router.callback_query(UserState.confirming, F.data.startswith("proof_"))
async def proof_prompt(callback: CallbackQuery, state: FSMContext):

    # Pengaman admin
    if callback.from_user.id == ADMIN_ID:
        await callback.answer(
            "👑 Admin tidak dapat mengirim bukti pembayaran.",
            show_alert=True
        )
        return

    await callback.answer()

    order_id = callback.data.split("_")[1]

    await state.update_data(waiting_proof_order_id=order_id)

    await callback.message.answer(
        "📸 Silakan kirim *foto bukti transfer* (file gambar).",
        parse_mode="Markdown"
    )

    await state.set_state(UserState.waiting_proof)

# ── Handler untuk tombol "Kembali" ─────────────────────
@router.callback_query(UserState.confirming, F.data == "back_to_quantity_from_qris")
async def back_to_quantity(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.delete()
    from source.handlers.user.p3_input import send_quantity_message
    await send_quantity_message(callback.message, state)
    await state.set_state(UserState.input_quantity)