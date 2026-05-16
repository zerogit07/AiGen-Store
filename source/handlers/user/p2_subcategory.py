from aiogram import Router, F
from aiogram.types import (CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton)
from aiogram.fsm.context import FSMContext
from source.states.user_state import UserState
from source.database.queries import (
    get_subcategories_by_category,
    get_category_name,
    get_stock_for_subcategory,
    get_subcategory_price_and_stock,
)
from source.utils.helpers import pad_center, format_rupiah

router = Router()
ITEMS_PER_PAGE = 10
BUTTON_COLS = 5
BUTTON_WIDTH = 5


def get_subcategory_keyboard(subcategories, page, total_pages, offset, category_id):
    buttons = []
    for i, (sub_id, _, _) in enumerate(subcategories, start=offset + 1):
        buttons.append(
            InlineKeyboardButton(
                text=pad_center(str(i), BUTTON_WIDTH),
                callback_data=f"sub_{sub_id}",  # aman untuk string "10.1"
            )
        )
    rows = [buttons[i : i + BUTTON_COLS] for i in range(0, len(buttons), BUTTON_COLS)]

    nav = []
    if page > 1:
        nav.append(
            InlineKeyboardButton(
                text="◀", callback_data=f"sub_page_{category_id}_{page - 1}"
            )
        )
    if page < total_pages:
        nav.append(
            InlineKeyboardButton(
                text="▶", callback_data=f"sub_page_{category_id}_{page + 1}"
            )
        )
    if nav:
        rows.append(nav)

    rows.append(
        [InlineKeyboardButton(text="« Kembali", callback_data="back_to_categories")]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def show_subcategories_by_edit(
    callback: CallbackQuery, state: FSMContext, category_id: int, page: int = 1
):
    offset = (page - 1) * ITEMS_PER_PAGE
    subs, total = await get_subcategories_by_category(
        category_id, ITEMS_PER_PAGE, offset
    )
    if not subs:
        await callback.message.answer("Kategori ini belum memiliki subkategori.")
        return

    total_pages = (total + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
    data = await state.get_data()
    has_banner = data.get("has_banner", False)
    cat_name = await get_category_name(category_id)

    separator = "━" * 17

    text = f"📂 *{cat_name} • Page {page}/{total_pages}*\n{separator}\n"
    for i, (sub_id, name, price) in enumerate(subs, start=offset + 1):
        stock = await get_stock_for_subcategory(sub_id)

        text += f"┌ {i}. {name}\n└ 💰 Rp{format_rupiah(price)} | 📦 Stock : {stock}\n"

    text += "\n➡️ Pilih tombol angka di bawah👇"

    keyboard = get_subcategory_keyboard(subs, page, total_pages, offset, category_id)

    if has_banner:
        await callback.message.edit_caption(
            caption=text, parse_mode="Markdown", reply_markup=keyboard
        )
    else:
        await callback.message.edit_text(
            text, parse_mode="Markdown", reply_markup=keyboard
        )

    await state.update_data(
        selected_category_id=category_id, subs=subs, selected_category_name=cat_name
    )


# Handler pagination
@router.callback_query(UserState.selecting_subcategory, F.data.startswith("sub_page_"))
async def sub_page(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    parts = callback.data.split("_")
    category_id = int(parts[2])
    page = int(parts[3])
    await show_subcategories_by_edit(callback, state, category_id, page)


# Handler pilih subkategori (angka)
@router.callback_query(UserState.selecting_subcategory, F.data.startswith("sub_"))
async def select_subcategory(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    sub_id_str = callback.data.split("_", 1)[1]
    try:
        sub_id = int(sub_id_str)
    except ValueError:
        sub_id = sub_id_str  # misal "10.1"

    data = await state.get_data()
    subs = data.get("subs", [])
    sub_name = next(
        (name for sid, name, _ in subs if str(sid) == str(sub_id)), "Produk"
    )

    price, stock = await get_subcategory_price_and_stock(sub_id)
    await state.update_data(
        selected_subcategory_id=sub_id,
        selected_sub_name=sub_name,
        price=price,
        stock=stock,
        qty=1,
    )

    # Panggil P3
    from source.handlers.user.p3_input import send_quantity_message

    await send_quantity_message(callback.message, state)

    # Hapus pesan subkategori
    try:
        await callback.message.delete()
    except Exception as e:
        print(f"Gagal hapus pesan: {e}")

    await state.set_state(UserState.input_quantity)


# Tombol kembali ke kategori
@router.callback_query(F.data == "back_to_categories")
async def back_to_categories(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    from source.handlers.user.p1_category import show_categories

    await show_categories(callback, state, page=1)
