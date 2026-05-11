from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from source.database.queries import get_config, set_config
from source.config import BOT_TOKEN

router = Router()
bot = Bot(token=BOT_TOKEN)

class SettingsState(StatesGroup):
    waiting_banner = State()
    waiting_qris = State()
    waiting_auto_delete = State()

@router.callback_query(F.data == "admin_settings")
async def settings_menu(callback: CallbackQuery):
    banner_id = await get_config("banner_image_file_id")
    qris_id = await get_config("qris_image_file_id")
    auto_days = await get_config("auto_delete_used_days") or "7"
    text = (
        f"⚙️ *Pengaturan Toko*\n\n"
        f"🖼️ *Banner Toko:* {'✅ Ada' if banner_id else '❌ Belum diatur'}\n"
        f"💳 *QRIS:* {'✅ Ada' if qris_id else '❌ Belum diatur'}\n"
        f"🗑️ *Auto Delete Kode Terpakai:* {auto_days} hari\n\n"
        f"Pilih tindakan:"
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🖼️ Upload Banner Toko", callback_data="settings_upload_banner")],
        [InlineKeyboardButton(text="💳 Upload QRIS", callback_data="settings_upload_qris")],
        [InlineKeyboardButton(text="🕒 Atur Auto Delete", callback_data="settings_auto_delete")],
        [InlineKeyboardButton(text="« Kembali ke Panel", callback_data="admin_back")]
    ])
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)
    await callback.answer()

@router.callback_query(F.data == "settings_upload_banner")
async def upload_banner_prompt(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("📸 Kirimkan *foto banner* untuk toko Anda.", parse_mode="Markdown")
    await state.set_state(SettingsState.waiting_banner)
    await callback.answer()

@router.message(SettingsState.waiting_banner, F.photo)
async def receive_banner(message: Message, state: FSMContext):
    file_id = message.photo[-1].file_id
    await set_config("banner_image_file_id", file_id)
    await message.answer("✅ Banner toko berhasil diupload.")
    await state.clear()
    from .admin import admin_cmd
    await admin_cmd(message)

@router.callback_query(F.data == "settings_upload_qris")
async def upload_qris_prompt(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("💳 Kirimkan *foto QRIS* untuk pembayaran.", parse_mode="Markdown")
    await state.set_state(SettingsState.waiting_qris)
    await callback.answer()

@router.message(SettingsState.waiting_qris, F.photo)
async def receive_qris(message: Message, state: FSMContext):
    file_id = message.photo[-1].file_id
    await set_config("qris_image_file_id", file_id)
    await message.answer("✅ QRIS berhasil diupload.")
    await state.clear()
    from .admin import admin_cmd
    await admin_cmd(message)

@router.callback_query(F.data == "settings_auto_delete")
async def auto_delete_prompt(callback: CallbackQuery, state: FSMContext):
    current = await get_config("auto_delete_used_days") or "7"
    await callback.message.answer(f"Saat ini auto delete: *{current} hari*.\nKirimkan angka baru (0 untuk nonaktif).", parse_mode="Markdown")
    await state.set_state(SettingsState.waiting_auto_delete)
    await callback.answer()

@router.message(SettingsState.waiting_auto_delete)
async def set_auto_delete(message: Message, state: FSMContext):
    try:
        days = int(message.text.strip())
        if days < 0:
            raise ValueError
    except Exception:
        await message.answer("❌ Masukkan angka positif (0 untuk nonaktif).")
        return
    await set_config("auto_delete_used_days", str(days))
    await message.answer(f"✅ Auto delete diatur menjadi {days} hari.")
    await state.clear()
    from .admin import admin_cmd
    await admin_cmd(message)