# source/handlers/admin/s1_category.py
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from source.states.admin_state import CategoryState
from source.database.products import (
    get_all_categories, add_category, update_category, delete_category, get_category_by_id
)
from source.utils.helpers import pad_center

router = Router()
ITEMS_PER_PAGE = 10
BUTTON_COLS = 5
BUTTON_WIDTH = 12

@router.callback_query(F.data == "admin_category")
async def list_categories(callback: CallbackQuery, page: int = 1):
    offset = (page - 1) * ITEMS_PER_PAGE
    categories, total = await get_all_categories(ITEMS_PER_PAGE, offset)
    total_pages = (total + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
    if not categories:
        text = "📭 *Daftar Kategori Produk*\nBelum ada kategori."
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Tambah Kategori", callback_data="add_category")],
            [InlineKeyboardButton(text="« Kembali", callback_data="admin_back")]
        ])
        await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)
        await callback.answer()
        return

    text = f"📦 *Daftar Kategori Profuk (Hal {page}/{total_pages})*\n\n"
    row_angka = []
    for i in range(offset + 1, offset + len(categories) + 1):
        row_angka.append(InlineKeyboardButton(text=pad_center(str(i), BUTTON_WIDTH), callback_data=f"admin_cat_{i}"))
    rows = [row_angka[i:i+BUTTON_COLS] for i in range(0, len(row_angka), BUTTON_COLS)]

    nav = []
    if page > 1:
        nav.append(InlineKeyboardButton(text="◀ Sebelumnya", callback_data=f"cat_page_{page-1}"))
    if page < total_pages:
        nav.append(InlineKeyboardButton(text="Berikutnya ▶", callback_data=f"cat_page_{page+1}"))
    if nav:
        rows.append(nav)

    rows.append([InlineKeyboardButton(text="➕ Tambah Kategori", callback_data="add_category")])
    rows.append([InlineKeyboardButton(text="« Kembali", callback_data="admin_back")])

    keyboard = InlineKeyboardMarkup(inline_keyboard=rows)
    for i, (_, name) in enumerate(categories, start=offset+1):
        text += f"{i}. {name}\n"
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)
    await callback.answer()

@router.callback_query(F.data.startswith("cat_page_"))
async def category_page(callback: CallbackQuery):
    page = int(callback.data.split("_")[2])
    await list_categories(callback, page)

@router.callback_query(F.data.startswith("admin_cat_"))
async def select_category_action(callback: CallbackQuery, state: FSMContext):
    index = int(callback.data.split("_")[2])
    page = (index - 1) // ITEMS_PER_PAGE + 1
    offset = (page - 1) * ITEMS_PER_PAGE
    categories, _ = await get_all_categories(ITEMS_PER_PAGE, offset)
    pos = index - offset - 1
    if 0 <= pos < len(categories):
        cat_id = categories[pos][0]
        cat_name = categories[pos][1]
        await state.update_data(edit_cat_id=cat_id)
        text = f"📌 *Kategori:* {cat_name}\n\nPilih aksi:"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✏️ Edit Nama", callback_data="edit_cat_name"),
            InlineKeyboardButton(text="🗑️ Hapus", callback_data="delete_cat")],
            [InlineKeyboardButton(text="« Kembali", callback_data="admin_category")]
        ])
        await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)
    else:
        await callback.answer("Kategori tidak ditemukan.", show_alert=True)
    await callback.answer()

@router.callback_query(F.data == "add_category")
async def add_category_prompt(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Masukkan *nama kategori* baru:", parse_mode="Markdown")
    await state.set_state(CategoryState.waiting_new_name)
    await callback.answer()

@router.message(CategoryState.waiting_new_name)
async def add_category_name(message: Message, state: FSMContext):
    name = message.text.strip()
    if not name:
        await message.answer("❌ Nama tidak boleh kosong.")
        return
    await add_category(name)
    await message.answer(f"✅ Kategori '{name}' berhasil ditambahkan.")
    await state.clear()
    # Kembali ke daftar kategori
    from .admin_main import admin_cmd
    await admin_cmd(message)  # Sederhananya, kembali ke menu utama

@router.callback_query(F.data == "edit_cat_name")
async def edit_cat_prompt(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Masukkan *nama baru* untuk kategori ini:", parse_mode="Markdown")
    await state.set_state(CategoryState.waiting_edit_name)
    await callback.answer()

@router.message(CategoryState.waiting_edit_name)
async def update_category_name(message: Message, state: FSMContext):
    new_name = message.text.strip()
    if not new_name:
        await message.answer("❌ Nama tidak boleh kosong.")
        return
    data = await state.get_data()
    cat_id = data.get('edit_cat_id')
    await update_category(cat_id, new_name)
    await message.answer(f"✅ Kategori berhasil diubah menjadi '{new_name}'.")
    # Tampilkan kembali menu aksi dengan nama baru
    cat = await get_category_by_id(cat_id)
    if cat:
        _, cat_name = cat
        text = f"📌 *Kategori:* {cat_name}\n\nPilih aksi:"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✏️ Edit Nama", callback_data="edit_cat_name"),
            InlineKeyboardButton(text="🗑️ Hapus", callback_data="delete_cat")],
            [InlineKeyboardButton(text="« Kembali", callback_data="admin_category")]
        ])
        await message.answer(text, parse_mode="Markdown", reply_markup=keyboard)
    else:
        await message.answer("Kategori tidak ditemukan.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="« Kembali", callback_data="admin_category")]]))
    await state.clear()

@router.callback_query(F.data == "delete_cat")
async def delete_cat_prompt(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("⚠️ Ketik *YA* untuk menghapus kategori ini. Semua subkategori dan item akan ikut terhapus.", parse_mode="Markdown")
    await state.set_state(CategoryState.waiting_delete_id)
    await callback.answer()

@router.message(CategoryState.waiting_delete_id)
async def confirm_delete_category(message: Message, state: FSMContext):
    if message.text.strip().upper() != "YA":
        await message.answer("Penghapusan dibatalkan.")
        await state.clear()
        return
    data = await state.get_data()
    cat_id = data.get('edit_cat_id')
    success = await delete_category(cat_id)
    if success:
        await message.answer("✅ Kategori beserta semua subkategori dan item berhasil dihapus.")
        # Kembali ke daftar kategori (refresh)
        await list_categories(message, page=1)
    else:
        await message.answer("❌ Gagal menghapus kategori. Terjadi kesalahan database.")
    await state.clear()