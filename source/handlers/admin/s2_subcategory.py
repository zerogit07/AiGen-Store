# source/handlers/admin/s2_subcategory.py
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from source.states.admin_state import SubcategoryState
from source.database.products import (
    get_all_categories, get_subcategories_by_category, add_subcategory,
    update_subcategory, delete_subcategory, get_category_name, get_subcategory_by_id
)
from source.utils.helpers import pad_center, format_rupiah

router = Router()
ITEMS_PER_PAGE = 10
BUTTON_COLS = 5
BUTTON_WIDTH = 12

# ========== HALAMAN 1: DAFTAR KATEGORI ==========
@router.callback_query(F.data == "admin_subcategory")
async def list_categories_page(callback: CallbackQuery, page: int = 1):
    offset = (page - 1) * ITEMS_PER_PAGE
    categories, total = await get_all_categories(ITEMS_PER_PAGE, offset)
    total_pages = (total + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
    if not categories:
        text = "📭 Belum ada kategori."
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="« Kembali", callback_data="admin_back")]
        ])
        await callback.message.edit_text(text, reply_markup=keyboard)
        await callback.answer()
        return

    text = f"📁 *Pilih Kategori (Halaman {page}/{total_pages})*\n\n"
    row_angka = []
    for i in range(offset + 1, offset + len(categories) + 1):
        row_angka.append(InlineKeyboardButton(text=pad_center(str(i), BUTTON_WIDTH), callback_data=f"sub_cat_page_{i}"))
    rows = [row_angka[i:i+BUTTON_COLS] for i in range(0, len(row_angka), BUTTON_COLS)]
    nav = []
    if page > 1:
        nav.append(InlineKeyboardButton(text="◀ Sebelumnya", callback_data=f"cat_list_page_{page-1}"))
    if page < total_pages:
        nav.append(InlineKeyboardButton(text="Berikutnya ▶", callback_data=f"cat_list_page_{page+1}"))
    if nav:
        rows.append(nav)
    rows.append([InlineKeyboardButton(text="« Kembali", callback_data="admin_back")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=rows)
    for i, (cat_id, name) in enumerate(categories, start=offset+1):
        text += f"{i}. {name}\n"
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)
    await callback.answer()

@router.callback_query(F.data.startswith("cat_list_page_"))
async def category_list_page(callback: CallbackQuery):
    page = int(callback.data.split("_")[3])
    await list_categories_page(callback, page)

@router.callback_query(F.data.startswith("sub_cat_page_"))
async def select_category_from_number(callback: CallbackQuery, state: FSMContext):
    index = int(callback.data.split("_")[3])
    page = (index - 1) // ITEMS_PER_PAGE + 1
    offset = (page - 1) * ITEMS_PER_PAGE
    categories, _ = await get_all_categories(ITEMS_PER_PAGE, offset)
    pos = index - offset - 1
    if 0 <= pos < len(categories):
        category_id = categories[pos][0]
        await state.update_data(selected_category_id=category_id)
        await list_subcategories(callback, state, page=1)
    else:
        await callback.answer("Kategori tidak ditemukan.", show_alert=True)
    await callback.answer()

# ========== HALAMAN 2: DAFTAR SUBKATEGORI ==========
async def list_subcategories(callback: CallbackQuery, state: FSMContext, page: int = 1):
    data = await state.get_data()
    category_id = data.get('selected_category_id')
    if not category_id:
        await callback.answer("Sesi kadaluarsa, pilih kategori ulang.", show_alert=True)
        return
    offset = (page - 1) * ITEMS_PER_PAGE
    subs, total = await get_subcategories_by_category(category_id, ITEMS_PER_PAGE, offset)
    total_pages = (total + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
    cat_name = await get_category_name(category_id)
    if not subs:
        text = f"📂 *{cat_name}*\nBelum ada subkategori."
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Tambah Subkategori", callback_data="add_subcategory")],
            [InlineKeyboardButton(text="« Kembali", callback_data="admin_subcategory")]
        ])
        await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)
        await callback.answer()
        return
    text = f"📂 *{cat_name} (Halaman {page}/{total_pages})*\n\n"
    for i, (sub_id, name, price) in enumerate(subs, start=offset+1):
        text += f"{i}. {name} - Rp{format_rupiah(price)}\n"
    row_angka = []
    for i in range(offset + 1, offset + len(subs) + 1):
        row_angka.append(InlineKeyboardButton(text=pad_center(str(i), BUTTON_WIDTH), callback_data=f"admin_sub_{i}"))
    rows = [row_angka[i:i+BUTTON_COLS] for i in range(0, len(row_angka), BUTTON_COLS)]
    nav = []
    if page > 1:
        nav.append(InlineKeyboardButton(text="◀ Sebelumnya", callback_data=f"sub_page_{category_id}_{page-1}"))
    if page < total_pages:
        nav.append(InlineKeyboardButton(text="Berikutnya ▶", callback_data=f"sub_page_{category_id}_{page+1}"))
    if nav:
        rows.append(nav)
    rows.append([InlineKeyboardButton(text="➕ Tambah Subkategori", callback_data="add_subcategory")])
    rows.append([InlineKeyboardButton(text="« Kembali", callback_data="admin_subcategory")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=rows)
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)
    await callback.answer()

@router.callback_query(F.data.startswith("sub_page_"))
async def sub_page_callback(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    category_id = int(parts[2])
    page = int(parts[3])
    await state.update_data(selected_category_id=category_id)
    await list_subcategories(callback, state, page)

# ========== KLIK ANGKA SUBKATEGORI (MENU AKSI) ==========
@router.callback_query(F.data.startswith("admin_sub_"))
async def select_sub_action(callback: CallbackQuery, state: FSMContext):
    index = int(callback.data.split("_")[2])
    data = await state.get_data()
    category_id = data.get('selected_category_id')
    if not category_id:
        await callback.answer("Sesi kadaluarsa.", show_alert=True)
        return
    page = (index - 1) // ITEMS_PER_PAGE + 1
    offset = (page - 1) * ITEMS_PER_PAGE
    subs, _ = await get_subcategories_by_category(category_id, ITEMS_PER_PAGE, offset)
    pos = index - offset - 1
    if 0 <= pos < len(subs):
        sub_id = subs[pos][0]
        sub_name = subs[pos][1]
        sub_price = subs[pos][2]
        cat_name = await get_category_name(category_id)
        await state.update_data(edit_sub_id=sub_id)
        text = f"📌 *Kategori:* {cat_name}\n📌 *Subkategori:* {sub_name} - Rp{format_rupiah(sub_price)}\n\nPilih aksi:"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✏️ Edit Nama", callback_data="edit_sub_name"),
            InlineKeyboardButton(text="💰 Edit Harga", callback_data="edit_sub_price")],
            [InlineKeyboardButton(text="🗑️ Hapus", callback_data="delete_sub"),
            InlineKeyboardButton(text="« Kembali", callback_data="admin_subcategory")]
        ])
        await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)
    else:
        await callback.answer("Subkategori tidak ditemukan.", show_alert=True)
    await callback.answer()

# ========== TAMBAH SUBKATEGORI ==========
@router.callback_query(F.data == "add_subcategory")
async def add_sub_prompt(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Masukkan *nama subkategori* baru:", parse_mode="Markdown")
    await state.set_state(SubcategoryState.waiting_new_name)
    await callback.answer()

@router.message(SubcategoryState.waiting_new_name)
async def get_sub_name(message: Message, state: FSMContext):
    name = message.text.strip()
    if not name:
        await message.answer("❌ Nama tidak boleh kosong.")
        return
    await state.update_data(new_sub_name=name)
    await message.answer("Masukkan *harga* (angka):", parse_mode="Markdown")
    await state.set_state(SubcategoryState.waiting_new_price)

@router.message(SubcategoryState.waiting_new_price)
async def get_sub_price(message: Message, state: FSMContext):
    try:
        price = int(message.text.strip())
        if price <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Harga harus angka positif.")
        return
    data = await state.get_data()
    cat_id = data.get('selected_category_id')
    name = data.get('new_sub_name')
    await add_subcategory(cat_id, name, price)
    await message.answer(f"✅ Subkategori '{name}' (Rp{format_rupiah(price)}) berhasil ditambahkan.")
    await state.clear()
    await list_subcategories(message, state, page=1)

# ========== EDIT NAMA ==========
@router.callback_query(F.data == "edit_sub_name")
async def edit_sub_name_prompt(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Masukkan *nama baru* untuk subkategori ini:", parse_mode="Markdown")
    await state.set_state(SubcategoryState.waiting_edit_name)
    await callback.answer()

@router.message(SubcategoryState.waiting_edit_name)
async def update_sub_name(message: Message, state: FSMContext):
    new_name = message.text.strip()
    if not new_name:
        await message.answer("❌ Nama tidak boleh kosong.")
        return
    data = await state.get_data()
    sub_id = data.get('edit_sub_id')
    await update_subcategory(sub_id, new_name=new_name)
    await message.answer(f"✅ Nama subkategori berhasil diubah menjadi '{new_name}'.")
    await show_sub_action_menu(message, state, sub_id)
    await state.clear()

# ========== EDIT HARGA ==========
@router.callback_query(F.data == "edit_sub_price")
async def edit_sub_price_prompt(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Masukkan *harga baru* (angka):", parse_mode="Markdown")
    await state.set_state(SubcategoryState.waiting_edit_price)
    await callback.answer()

@router.message(SubcategoryState.waiting_edit_price)
async def update_sub_price(message: Message, state: FSMContext):
    try:
        new_price = int(message.text.strip())
        if new_price <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Harga harus angka positif.")
        return
    data = await state.get_data()
    sub_id = data.get('edit_sub_id')
    await update_subcategory(sub_id, new_price=new_price)
    await message.answer(f"✅ Harga subkategori berhasil diubah menjadi Rp{format_rupiah(new_price)}.")
    await show_sub_action_menu(message, state, sub_id)
    await state.clear()

# ========== HAPUS SUBKATEGORI ==========
@router.callback_query(F.data == "delete_sub")
async def delete_sub_prompt(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("⚠️ Ketik *YA* untuk menghapus subkategori ini. Semua item terkait akan ikut terhapus.", parse_mode="Markdown")
    await state.set_state(SubcategoryState.waiting_delete_id)
    await callback.answer()

@router.message(SubcategoryState.waiting_delete_id)
async def confirm_delete_sub(message: Message, state: FSMContext):
    if message.text.strip().upper() != "YA":
        await message.answer("Penghapusan dibatalkan.")
        await state.clear()
        return
    data = await state.get_data()
    sub_id = data.get('edit_sub_id')
    success = await delete_subcategory(sub_id)
    if success:
        await message.answer("✅ Subkategori beserta semua item (voucher) berhasil dihapus.")
        # Kembali ke daftar subkategori (refresh)
        await list_subcategories(message, state, page=1)
    else:
        await message.answer("❌ Gagal menghapus subkategori.")
    await state.clear()

# ========== FUNGSI BANTU: TAMPILKAN MENU AKSI ==========
async def show_sub_action_menu(target, state: FSMContext, sub_id: int):
    sub = await get_subcategory_by_id(sub_id)
    if not sub:
        await target.answer("Subkategori tidak ditemukan.")
        return
    sub_id, cat_id, name, price = sub
    cat_name = await get_category_name(cat_id)
    text = f"📌 *Kategori:* {cat_name}\n📌 *Subkategori:* {name} - Rp{format_rupiah(price)}\n\nPilih aksi:"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Edit Nama", callback_data="edit_sub_name"),
        InlineKeyboardButton(text="💰 Edit Harga", callback_data="edit_sub_price"),
        InlineKeyboardButton(text="🗑️ Hapus", callback_data="delete_sub")],
        [InlineKeyboardButton(text="« Kembali", callback_data="admin_subcategory")]
    ])
    await state.update_data(edit_sub_id=sub_id, selected_category_id=cat_id)
    if isinstance(target, CallbackQuery):
        await target.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)
    else:
        await target.answer(text, parse_mode="Markdown", reply_markup=keyboard)