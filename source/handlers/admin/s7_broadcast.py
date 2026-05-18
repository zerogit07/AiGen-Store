import asyncio
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from source.database.users import (
    get_all_user_ids,
    get_buyer_user_ids,
    get_nonbuyer_user_ids,
)
from source.config import BOT_TOKEN

router = Router()
bot = Bot(token=BOT_TOKEN)

class BroadcastState(StatesGroup):
    waiting_content = State()


async def send_broadcast_to_users(user_ids, content_type, text, file_id, caption):
    success, failed = 0, 0
    total = len(user_ids)
    for i, uid in enumerate(user_ids, 1):
        try:
            if content_type == "text":
                await bot.send_message(uid, text)
            elif content_type == "photo":
                await bot.send_photo(uid, file_id, caption=caption)
            elif content_type == "video":
                await bot.send_video(uid, file_id, caption=caption)
            elif content_type == "document":
                await bot.send_document(uid, file_id, caption=caption)
            success += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.05)
        if i % 10 == 0 or i == total:
            yield i, success, failed


def target_label(key: str) -> str:
    return {"all": "Semua User", "buyers": "Pernah Beli", "nonbuyers": "Belum Pernah Beli"}.get(key, "Unknown")


# ── Step 1: Pilih Target ──────────────────────────────────────
@router.callback_query(F.data == "admin_broadcast")
async def broadcast_start(callback: CallbackQuery):
    text = "📣 *Broadcast*\n\nPilih target pengiriman:"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 Semua User", callback_data="broadcast_all")],
        [InlineKeyboardButton(text="👥 Pernah Beli", callback_data="broadcast_buyers")],
        [InlineKeyboardButton(text="👥 Belum Pernah Beli", callback_data="broadcast_nonbuyers")],
        [InlineKeyboardButton(text="« Kembali ke Panel", callback_data="admin_back")],
    ])
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)
    await callback.answer()


# ── Step 2: Admin pilih target → instruksi input konten ──────
@router.callback_query(F.data.startswith("broadcast_"))
async def broadcast_choose_target(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    target = callback.data.split("_")[1]

    if target == "all":
        ids = await get_all_user_ids()
    elif target == "buyers":
        ids = await get_buyer_user_ids()
    else:
        ids = await get_nonbuyer_user_ids()

    if not ids:
        await callback.message.edit_text(
            "❌ Tidak ada user untuk target ini.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="« Kembali", callback_data="admin_broadcast")]
            ])
        )
        return

    await state.update_data(
        broadcast_target=target,
        broadcast_ids=ids,
        broadcast_msg_id=callback.message.message_id
    )

    text = (
        f"📣 *Broadcast*\n"
        f"Target: {target_label(target)}\n"
        f"Jumlah: {len(ids)} user\n\n"
        "Silakan kirim konten (teks / foto / video / dokumen)."
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="« Kembali", callback_data="admin_broadcast")]
    ])
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)
    await state.set_state(BroadcastState.waiting_content)


# ── Step 3: Admin mengirim konten → pratinjau ─────────────────
@router.message(BroadcastState.waiting_content, F.content_type.in_({"text", "photo", "video", "document"}))
async def receive_broadcast_content(message: Message, state: FSMContext):
    data = await state.get_data()
    msg_id = data.get("broadcast_msg_id")
    ids = data.get("broadcast_ids", [])
    target = data.get("broadcast_target", "all")

    content_type = message.content_type
    file_id = None
    caption = message.caption or ""
    text = message.text or ""

    if content_type == "photo":
        file_id = message.photo[-1].file_id
    elif content_type == "video":
        file_id = message.video.file_id
    elif content_type == "document":
        file_id = message.document.file_id

    await state.update_data(
        broadcast_content_type=content_type,
        broadcast_file_id=file_id,
        broadcast_caption=caption,
        broadcast_text=text
    )

    # Hapus pesan konten yang baru dikirim admin
    await message.delete()

    # Matikan state waiting_content segera – tidak boleh menerima input lagi
    await state.set_state(None)

    # Buat preview
    if content_type == "text":
        preview = text[:500] + ("..." if len(text) > 500 else "")
    else:
        preview = f"[Konten {content_type}]" + (f"\nCaption: {caption[:200]}" if caption else "")

    preview_text = (
        f"📣 *Konfirmasi Broadcast*\n"
        f"Target: {target_label(target)}\n"
        f"Jumlah: {len(ids)} user\n\n"
        f"Pratinjau:\n{preview}\n\n"
        "Kirim sekarang?"
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Kirim", callback_data="send_broadcast")],
        [InlineKeyboardButton(text="❌ Batal", callback_data="admin_back")],
        # Tidak ada tombol kembali ke input – admin bisa batalkan & ulangi
    ])

    # Edit pesan instruksi menjadi pratinjau
    if msg_id:
        try:
            await bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=msg_id,
                text=preview_text,
                parse_mode="Markdown",
                reply_markup=keyboard
            )
        except Exception:
            sent = await message.answer(preview_text, parse_mode="Markdown", reply_markup=keyboard)
            await state.update_data(broadcast_msg_id=sent.message_id)
    else:
        sent = await message.answer(preview_text, parse_mode="Markdown", reply_markup=keyboard)
        await state.update_data(broadcast_msg_id=sent.message_id)


# ── Step 4: Tombol Kirim → eksekusi broadcast ─────────────────
@router.callback_query(F.data == "send_broadcast")
async def broadcast_send(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    ids = data.get("broadcast_ids", [])
    content_type = data.get("broadcast_content_type")
    file_id = data.get("broadcast_file_id")
    caption = data.get("broadcast_caption")
    text = data.get("broadcast_text")

    # Bersihkan state sepenuhnya, tidak ada lagi kemungkinan input ulang
    await state.clear()

    msg = callback.message
    await msg.edit_text("📣 Mengirim... 0/" + str(len(ids)))

    success, failed = 0, 0
    async for i, s, f in send_broadcast_to_users(ids, content_type, text, file_id, caption):
        success, failed = s, f
        try:
            await msg.edit_text(f"📣 Mengirim... {i}/{len(ids)}")
        except Exception:
            pass

    # Laporan akhir
    target = data.get("broadcast_target", "all")
    final_text = (
        f"✅ *Broadcast Selesai*\n"
        f"Target: {target_label(target)}\n"
        f"Terkirim: {success}\n"
        f"Gagal: {failed}"
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="« Kembali ke Panel", callback_data="admin_back")]
    ])
    await msg.edit_text(final_text, parse_mode="Markdown", reply_markup=keyboard)