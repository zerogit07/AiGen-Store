from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from source.states.user_state import UserState
from source.database.queries import get_all_categories
from source.utils.helpers import pad_center

router = Router()
ITEMS_PER_PAGE = 10
BUTTON_COLS = 5
BUTTON_WIDTH = 12

def get_category_keyboard(categories, page, total_pages, offset):
    # Tombol kategori (horizontal, BUTTON_COLS kolom)
    category_buttons = []
    for i, (cat_id, _) in enumerate(categories, start=offset+1):
        category_buttons.append(InlineKeyboardButton(text=pad_center(str(i), BUTTON_WIDTH), callback_data=f"cat_{cat_id}"))
    rows = [category_buttons[i:i+BUTTON_COLS] for i in range(0, len(category_buttons), BUTTON_COLS)]
    
    # Tombol navigasi halaman (baris terpisah)
    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton(text="◀ Sebelumnya", callback_data=f"cat_page_{page-1}"))
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton(text="Berikutnya ▶", callback_data=f"cat_page_{page+1}"))
    if nav_buttons:
        rows.append(nav_buttons)
    
    return InlineKeyboardMarkup(inline_keyboard=rows)

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    page = 1
    offset = (page - 1) * ITEMS_PER_PAGE
    categories, total = await get_all_categories(ITEMS_PER_PAGE, offset)
    if not categories:
        await message.answer("📭 Belum ada kategori.")
        return
    total_pages = (total + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
    keyboard = get_category_keyboard(categories, page, total_pages, offset)
    text = f"📦 *Daftar Kategori (Halaman {page}/{total_pages})*\n\n"
    for i, (_, name) in enumerate(categories, start=offset+1):
        text += f"{i}. {name}\n"
    await message.answer(text, parse_mode="Markdown", reply_markup=keyboard)
    await state.set_state(UserState.selecting_category)

@router.callback_query(UserState.selecting_category, F.data.startswith("cat_page_"))
async def category_page(callback: CallbackQuery, state: FSMContext):
    page = int(callback.data.split("_")[2])
    offset = (page - 1) * ITEMS_PER_PAGE
    categories, total = await get_all_categories(ITEMS_PER_PAGE, offset)
    if not categories:
        await callback.answer("Halaman kosong.", show_alert=True)
        return
    total_pages = (total + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
    keyboard = get_category_keyboard(categories, page, total_pages, offset)
    text = f"📦 *Daftar Kategori (Halaman {page}/{total_pages})*\n\n"
    for i, (_, name) in enumerate(categories, start=offset+1):
        text += f"{i}. {name}\n"
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)
    await callback.answer()
    
# Tambahkan di akhir file p1_category.py
async def show_categories(target, state: FSMContext, page: int = 1):
    offset = (page - 1) * ITEMS_PER_PAGE
    categories, total = await get_all_categories(ITEMS_PER_PAGE, offset)
    if not categories:
        if isinstance(target, CallbackQuery):
            await target.message.answer("📭 Belum ada kategori.")
        else:
            await target.answer("📭 Belum ada kategori.")
        return
    total_pages = (total + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
    keyboard = get_category_keyboard(categories, page, total_pages, offset)
    text = f"📦 *Daftar Kategori (Halaman {page}/{total_pages})*\n\n"
    for i, (_, name) in enumerate(categories, start=offset+1):
        text += f"{i}. {name}\n"
    if isinstance(target, CallbackQuery):
        await target.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)
    else:
        await target.answer(text, parse_mode="Markdown", reply_markup=keyboard)
    await state.set_state(UserState.selecting_category)