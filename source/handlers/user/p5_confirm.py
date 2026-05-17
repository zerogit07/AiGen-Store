from aiogram import Router, F, Bot
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.fsm.context import FSMContext
from source.states.user_state import UserState
from source.database.queries import (
    update_order_payment_proof,
    get_order_by_id,
    get_order_details_by_item_id,
    get_available_item,
    mark_item_used,
    update_order_status,
    is_user_registered,
    get_item_subcategory,
    add_notification,
)
from source.utils.helpers import format_rupiah
from source.config import ADMIN_ID, BOT_TOKEN

router = Router()
bot = Bot(token=BOT_TOKEN)


@router.message(UserState.waiting_proof, F.photo)
async def receive_proof(message: Message, state: FSMContext):
    data = await state.get_data()
    order_id = data.get("waiting_proof_order_id")
    if not order_id:
        await message.answer(
            "❌ Sesi tidak valid. Silakan mulai pesanan ulang dengan /start"
        )
        await state.clear()
        return

    order = await get_order_by_id(order_id)
    if not order:
        await message.answer("❌ Pesanan tidak ditemukan.")
        await state.clear()
        return

    order_user_id = order[1]

    if not await is_user_registered(order_user_id):
        await message.answer(
            "⚠️ Anda belum terdaftar. Silakan ketik /start terlebih dahulu."
        )
        await state.clear()
        return

    if message.from_user.id != order_user_id:
        await message.answer("❌ Anda tidak memiliki akses ke pesanan ini.")
        await state.clear()
        return

    photo = message.photo[-1]

    file_id = photo.file_id

    file = await bot.get_file(file_id)

    image_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file.file_path}"

    await update_order_payment_proof(order_id, image_url)
    user_id = order_user_id
    qty = order[3]
    total = order[4]
    three_digits = order[5]
    nominal = total + int(three_digits)  # total yang harus dibayar

    # order[2] sekarang adalah item_id
    sub_name, cat_name = await get_order_details_by_item_id(order[2])

    caption = (
        f"🆕 *Pesanan Baru!*\n\n"
        f"📦 Order ID: `{order_id}`\n"
        f"👤 User ID: `{user_id}`\n"
        f"📂 Produk: {cat_name} → {sub_name}\n"
        f"🔢 Jumlah: {qty}\n"
        f"💰 Total : Rp{format_rupiah(nominal)}"
    )
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Setujui", callback_data=f"approve_{order_id}"
                ),
                InlineKeyboardButton(
                    text="❌ Tolak", callback_data=f"reject_{order_id}"
                ),
            ]
        ]
    )

    await bot.send_photo(
        ADMIN_ID,
        photo=file_id,
        caption=caption,
        parse_mode="Markdown",
        reply_markup=keyboard,
    )

    # notif dashboard
    await add_notification(
        type="order",
        title="📦 Pesanan baru",
        message=f"#{order_id}",
        page="orders",
        tab="masuk",
        related_id=str(order_id),
    )

    await message.answer(
        "✅ Bukti pembayaran telah diterima. Admin akan segera memproses. Terima kasih!"
    )
    await state.clear()


@router.callback_query(F.data.startswith("approve_"))
async def approve_order(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Unauthorized", show_alert=True)
        return

    order_id = callback.data.split("_", 1)[1]
    order = await get_order_by_id(order_id)

    if not order or order[7] != "pending":
        await callback.answer(
            "❌ Pesanan tidak valid atau sudah diproses.", show_alert=True
        )
        return

    user_id = order[1]
    item_id = order[2]
    qty = order[3]
    subcategory_id = await get_item_subcategory(item_id)

    items = await get_available_item(subcategory_id, qty)

    if len(items) < qty:
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.answer(
            f"❌ Stok tidak cukup untuk pesanan {order_id}.\n\n"
            f"📦 Diminta: {qty}\n"
            f"📦 Tersedia: {len(items)}"
        )
        await callback.answer("Stok tidak cukup", show_alert=True)
        return

    await callback.message.edit_reply_markup(reply_markup=None)

    codes = []
    for iid, code in items:
        await mark_item_used(iid, order_id)
        codes.append(code)

    await update_order_status(order_id, "approved")

    # Ambil detail produk berdasarkan item_id
    sub_name, cat_name = await get_order_details_by_item_id(item_id)
    codes_text = "\n".join([f"{i + 1}. {c}" for i, c in enumerate(codes)])

    # Kirim notifikasi ke user TANPA parse_mode (teks biasa)
    try:
        await bot.send_message(
            user_id,
            f"✅ Pesanan Disetujui!\n\n"
            f"📦 Order ID: {order_id}\n"
            f"📂 Produk: {cat_name} → {sub_name}\n"
            f"🔢 Jumlah: {qty}\n\n"
            f"🎫 Item:\n{codes_text}\n\n"
            f"Terima kasih telah berbelanja!",
        )
        await callback.message.answer(
            f"✅ Pesanan Disetujui\n\n"
            f"📦 Order ID : {order_id}\n"
            f"📂 Produk   : {cat_name} → {sub_name}\n"
            f"🔢 Jumlah   : {qty} item\n"
            f"📤 Status   : Kode terkirim ke user."
        )
    except Exception as e:
        await callback.message.answer(
            f"⚠️ Pesanan {order_id} disetujui, tetapi gagal mengirim kode ke user:\n{e}"
        )

    await callback.answer()


@router.callback_query(F.data.startswith("reject_"))
async def reject_order(callback: CallbackQuery):
    order_id = callback.data.split("_")[1]
    order = await get_order_by_id(order_id)

    if not order or order[7] != "pending":
        await callback.answer(
            "❌ Pesanan tidak valid atau sudah diproses.", show_alert=True
        )
        return

    await update_order_status(order_id, "rejected")

    user_id = order[1]
    item_id = order[2]
    qty = order[3]

    sub_name, cat_name = await get_order_details_by_item_id(item_id)

    try:
        await bot.send_message(
            user_id,
            f"❌ Pesanan Ditolak!\n\n"
            f"📦 Order ID: {order_id}\n"
            f"📂 Produk: {cat_name} → {sub_name}\n"
            f"🔢 Jumlah: {qty}\n\n"
            f"Silakan hubungi admin untuk informasi lebih lanjut.",
        )
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.answer(
            f"❌ Pesanan Ditolak\n\n"
            f"📦 Order ID : {order_id}\n"
            f"📂 Produk   : {cat_name} → {sub_name}\n"
            f"🔢 Jumlah   : {qty} item\n"
            f"📤 Status   : User telah diberi notifikasi"
        )
    except Exception as e:
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.answer(
            f"⚠️ Pesanan {order_id} ditolak, tetapi gagal notifikasi user: {e}"
        )

    await callback.answer()
