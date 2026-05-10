from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from source.states.user_state import UserState
from source.database.queries import get_subcategories_by_category, get_category_name
from source.utils.helpers import pad_center
from source.handlers.user.p1_category import show_categories

router = Router()
ITEMS_PER_PAGE = 10
BUTTON_COLS = 5
BUTTON_WIDTH = 12

def get_subcategory_keyboard(subcategories, page, total_pages, offset, category_id):
    sub_buttons = []
    for i, (sub_id, name, price) in enumerate(subcategories, start=offset+1):
        text = pad_center(str(i), BUTTON_WIDTH)
        sub_buttons.append(InlineKeyboardButton(text=text, callback_data=f"sub_{sub_id}"))
    rows = [sub_buttons[i:i+BUTTON_COLS] for i in range(0, len(sub_buttons), BUTTON_COLS)]
    nav = []
    if page > 1:
        nav.append(InlineKeyboardButton(text="◀ Sebelumnya", callback_data=f"sub_page_{category_id}_{page-1}"))
    if page < total_pages:
        nav.append(InlineKeyboardButton(text="Berikutnya ▶", callback_data=f"sub_page_{category_id}_{page+1}"))
    if nav:
        rows.append(nav)
    rows.append([InlineKeyboardButton(text="« Kembali", callback_data="back_to_categories")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

async def show_subcategories(target, state: FSMContext, category_id: int, page: int = 1):
    """Fungsi helper untuk menampilkan subkategori (bisa dipanggil dari handler atau dari p3)"""
    await state.update_data(selected_category_id=category_id)
    offset = (page - 1) * ITEMS_PER_PAGE
    subs, total = await get_subcategories_by_category(category_id, ITEMS_PER_PAGE, offset)
    if not subs:
        if isinstance(target, CallbackQuery):
            await target.message.answer("Kategori ini belum memiliki subkategori.")
            await target.answer()
        else:
            await target.answer("Kategori ini belum memiliki subkategori.")
        return
    total_pages = (total + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
    keyboard = get_subcategory_keyboard(subs, page, total_pages, offset, category_id)
    cat_name = await get_category_name(category_id)
    text = f"📂 *{cat_name}*\nPilih subkategori (Halaman {page}/{total_pages}):\n\n"
    for i, (_, name, price) in enumerate(subs, start=offset+1):
        text += f"{i}. {name} - Rp{price:,}\n"
    if isinstance(target, CallbackQuery):
        await target.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)
    else:
        await target.answer(text, parse_mode="Markdown", reply_markup=keyboard)
    await state.set_state(UserState.selecting_subcategory)

@router.callback_query(UserState.selecting_category, F.data.startswith("cat_"))
async def show_subcategories_handler(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    category_id = int(callback.data.split("_")[1])
    await show_subcategories(callback, state, category_id, page=1)

@router.callback_query(UserState.selecting_subcategory, F.data.startswith("sub_page_"))
async def subcategory_page(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    category_id = int(parts[2])
    page = int(parts[3])
    await show_subcategories(callback, state, category_id, page)
    await callback.answer()

@router.callback_query(F.data == "back_to_categories")
async def back_to_categories(callback: CallbackQuery, state: FSMContext):
    await show_categories(callback, state, page=1)