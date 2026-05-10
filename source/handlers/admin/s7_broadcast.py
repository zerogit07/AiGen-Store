# source/handlers/admin/s7_broadcast.py
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from source.config import ADMIN_ID, BOT_TOKEN
from source.database.queries import get_all_users, get_users_ever_ordered
import asyncio

router = Router()
bot = Bot(token=BOT_TOKEN)

class BroadcastState(StatesGroup):
    waiting_target = State()
    waiting_message = State()

def get_broadcast_menu():
    buttons = [
        [InlineKeyboardButton(text="📢 Broadcast", callback_data="bc_manual")],
        [InlineKeyboardButton(text="« Kembali", callback_data="admin_back")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_target_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 Semua User", callback_data="bc_target_all")],
         [InlineKeyboardButton(text="🛒 Pernah Order", callback_data="bc_target_ordered")]
    ])

@router.callback_query(F.data == "admin_broadcast")
async def broadcast_menu(callback: CallbackQuery):
    await callback.message.edit_text("📢 *Broadcast Message*", parse_mode="Markdown", reply_markup=get_broadcast_menu())
    await callback.answer()

# ========== BROADCAST MANUAL ==========
@router.callback_query(F.data == "bc_manual")
async def manual_target(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Pilih target broadcast:", reply_markup=get_target_keyboard())
    await state.set_state(BroadcastState.waiting_target)
    await callback.answer()

@router.callback_query(BroadcastState.waiting_target, F.data.startswith("bc_target_"))
async def manual_message(callback: CallbackQuery, state: FSMContext):
    target = callback.data.split("_")[2]  # 'all' or 'ordered'
    await state.update_data(bc_target=target)
    await callback.message.answer("Kirimkan *pesan* yang akan di-broadcast (teks biasa, bisa dengan emoji).", parse_mode="Markdown")
    await state.set_state(BroadcastState.waiting_message)
    await callback.answer()

@router.message(BroadcastState.waiting_message)
async def manual_confirm(message: Message, state: FSMContext):
    text = message.text or message.caption
    if not text:
        await message.answer("❌ Pesan tidak boleh kosong.")
        return
    data = await state.get_data()
    target = data.get('bc_target')
    await state.update_data(bc_message=text)
    target_label = "SEMUA USER" if target == 'all' else "USER PERNAH ORDER"
    confirm_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Kirim", callback_data="bc_send")],
         [InlineKeyboardButton(text="❌ Batal", callback_data="bc_cancel")]
    ])
    await message.answer(f"📢 Konfirmasi Broadcast\nTarget: {target_label}\n\nPesan:\n{text}\n\nKirim sekarang?", parse_mode="Markdown", reply_markup=confirm_kb)

@router.callback_query(F.data == "bc_send")
async def execute_broadcast(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    target = data.get('bc_target')
    text = data.get('bc_message')
    if target == 'all':
        users = await get_all_users()
        if not users:
            users = await get_users_ever_ordered()
    else:
        users = await get_users_ever_ordered()
    if not users:
        await callback.message.answer("Tidak ada user yang ditemukan.")
        await state.clear()
        await broadcast_menu(callback)
        return
    success = 0
    for uid in users:
        try:
            await bot.send_message(uid, text)
            success += 1
            await asyncio.sleep(0.05)
        except Exception:
            pass
    await callback.message.answer(f"✅ Broadcast selesai.\nBerhasil: {success} dari {len(users)} user.")
    await state.clear()
    await broadcast_menu(callback)

@router.callback_query(F.data == "bc_cancel")
async def cancel_broadcast(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Broadcast dibatalkan.")
    await state.clear()
    await broadcast_menu(callback)