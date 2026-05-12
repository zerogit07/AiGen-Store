from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from source.states.user_state import UserState
from source.database.queries import get_all_categories, add_user, get_config
from source.utils.helpers import pad_center

router = Router()
ITEMS_PER_PAGE = 10
BUTTON_COLS = 5
BUTTON_WIDTH = 5

def get_category_keyboard(categories, page, total_pages, offset):
    buttons = []
    for i, (cat_id, _) in enumerate(categories, start=offset+1):
        buttons.append(InlineKeyboardButton(text=pad_center(str(i), BUTTON_WIDTH), callback_data=f"cat_{cat_id}"))
    rows = [buttons[i:i+BUTTON_COLS] for i in range(0, len(buttons), BUTTON_COLS)]
    nav = []
    if page > 1:
        nav.append(InlineKeyboardButton(text="◀", callback_data=f"cat_page_{page-1}"))
    if page < total_pages:
        nav.append(InlineKeyboardButton(text="▶", callback_data=f"cat_page_{page+1}"))
    if nav:
        rows.append(nav)
    return InlineKeyboardMarkup(inline_keyboard=rows)

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    user = message.from_user
    await add_user(user.id, user.username, user.first_name)
    page = 1
    offset = (page-1) * ITEMS_PER_PAGE
    categories, total = await get_all_categories(ITEMS_PER_PAGE, offset)
    if not categories:
        await message.answer("📭 Belum ada kategori.")
        return
    total_pages = (total + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
    banner = await get_config("banner_image_file_id")
    text = f"📦 *Daftar Kategori Produk (Hal {page}/{total_pages})*\n\n"
    for i, (_, name) in enumerate(categories, start=offset+1):
        text += f"{i}. {name}\n"
    text += "\n👇 *Silakan pilih tombol angka di bawah*"
    keyboard = get_category_keyboard(categories, page, total_pages, offset)
    if banner:
        await message.answer_photo(banner, caption=text, parse_mode="Markdown", reply_markup=keyboard)
    else:
        await message.answer(text, parse_mode="Markdown", reply_markup=keyboard)
    await state.update_data(has_banner=bool(banner))
    await state.set_state(UserState.selecting_category)

@router.callback_query(UserState.selecting_category, F.data.startswith("cat_page_"))
async def category_page(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    page = int(callback.data.split("_")[2])
    offset = (page-1) * ITEMS_PER_PAGE
    categories, total = await get_all_categories(ITEMS_PER_PAGE, offset)
    if not categories:
        await callback.answer("Halaman kosong.", show_alert=True)
        return
    total_pages = (total + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
    text = f"📦 *Daftar Kategori Produk (Hal {page}/{total_pages})*\n\n"
    for i, (_, name) in enumerate(categories, start=offset+1):
        text += f"{i}. {name}\n"
    text += "\n👇 *Silakan pilih tombol angka di bawah*"
    keyboard = get_category_keyboard(categories, page, total_pages, offset)
    data = await state.get_data()
    if data.get('has_banner'):
        await callback.message.edit_caption(caption=text, parse_mode="Markdown", reply_markup=keyboard)
    else:
        await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)

async def show_categories(target, state: FSMContext, page: int = 1):
    """Fungsi helper untuk kembali ke kategori (digunakan oleh back dari p2)"""
    data = await state.get_data()
    offset = (page-1) * ITEMS_PER_PAGE
    categories, total = await get_all_categories(ITEMS_PER_PAGE, offset)
    if not categories:
        if isinstance(target, CallbackQuery):
            await target.message.answer("📭 Belum ada kategori.")
        return
    total_pages = (total + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
    text = f"📦 *Daftar Kategori Produk (Hal {page}/{total_pages})*\n\n"
    for i, (_, name) in enumerate(categories, start=offset+1):
        text += f"{i}. {name}\n"
    text += "\n👇 *Silakan pilih tombol angka di bawah*"
    keyboard = get_category_keyboard(categories, page, total_pages, offset)
    if isinstance(target, CallbackQuery):
        if data.get('has_banner'):
            await target.message.edit_caption(caption=text, parse_mode="Markdown", reply_markup=keyboard)
        else:
            await target.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)
    await state.update_data(has_banner=data.get('has_banner', False))
    await state.set_state(UserState.selecting_category)


@router.callback_query(UserState.selecting_category, F.data.startswith("cat_"))
async def category_selected(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    # ── Daftarkan user jika belum ada ──
    user = callback.from_user
    await add_user(user.id, user.username, user.first_name)

    category_id = int(callback.data.split("_")[1])
    await state.update_data(selected_category_id=category_id)
    from source.handlers.user.p2_subcategory import show_subcategories_by_edit
    await show_subcategories_by_edit(callback, state, category_id, page=1)
    await state.set_state(UserState.selecting_subcategory)