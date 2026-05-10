from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from source.config import ADMIN_ID

router = Router()

def get_main_admin_keyboard():
    buttons = [
        [InlineKeyboardButton(text="📦 Manajemen Kategori", callback_data="admin_category"),
        InlineKeyboardButton(text="📁 Manajemen Subkategori", callback_data="admin_subcategory")],
        [InlineKeyboardButton(text="🎫 Manajemen Item", callback_data="admin_item"),
        InlineKeyboardButton(text="📊 Manajemen Stok", callback_data="admin_stock")],
        [InlineKeyboardButton(text="📋 Manajemen Pesanan", callback_data="admin_orders"),
        InlineKeyboardButton(text="📈 Statistik", callback_data="admin_stats")],
        [InlineKeyboardButton(text="📢 Broadcast", callback_data="admin_broadcast")]
    ]

    return InlineKeyboardMarkup(inline_keyboard=buttons)

@router.message(Command("admin"))
async def admin_cmd(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ Anda tidak memiliki akses.")
        return
    await message.answer("🔧 *Panel Admin*", parse_mode="Markdown", reply_markup=get_main_admin_keyboard())

@router.callback_query(F.data == "admin_back")
async def back_to_admin(callback: CallbackQuery):
    await callback.message.edit_text("🔧 *Panel Admin*", parse_mode="Markdown", reply_markup=get_main_admin_keyboard())
    await callback.answer()