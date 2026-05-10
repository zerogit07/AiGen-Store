# source/handlers/admin/s3_item.py
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton, BufferedInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from source.database.queries import (
    get_all_categories, get_subcategories_by_category, get_category_name,
    get_subcategory_by_id, get_items_by_subcategory, add_item,
    delete_used_items, export_items_csv, get_auto_delete_days, set_auto_delete_days,
    get_subcategory_name
)
from source.utils.helpers import pad_center, format_rupiah
import csv, io

router = Router()
ITEMS_PER_PAGE = 10
BUTTON_COLS = 5
BUTTON_WIDTH = 12

class ItemState(StatesGroup):
    waiting_manual_codes = State()
    waiting_import_file = State()
    waiting_auto_delete = State()

# ========== HALAMAN 1: DAFTAR KATEGORI ==========
@router.callback_query(F.data == "admin_item")
async def list_categories_page(callback: CallbackQuery, state: FSMContext, page: int = 1):
    offset = (page - 1) * ITEMS_PER_PAGE
    categories, total = await get_all_categories(ITEMS_PER_PAGE, offset)
    total_pages = (total + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
    if not categories:
        text = "📭 Belum ada kategori."
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="« Kembali", callback_data="admin_back")]])
        await callback.message.edit_text(text, reply_markup=keyboard)
        await callback.answer()
        return
    text = f"📁 *Pilih Kategori (Halaman {page}/{total_pages})*\n\n"
    row_angka = [InlineKeyboardButton(text=pad_center(str(i), BUTTON_WIDTH), callback_data=f"item_cat_{i}") for i in range(offset+1, offset+len(categories)+1)]
    rows = [row_angka[i:i+BUTTON_COLS] for i in range(0, len(row_angka), BUTTON_COLS)]
    nav = []
    if page > 1:
        nav.append(InlineKeyboardButton(text="◀ Sebelumnya", callback_data=f"item_cat_page_{page-1}"))
    if page < total_pages:
        nav.append(InlineKeyboardButton(text="Berikutnya ▶", callback_data=f"item_cat_page_{page+1}"))
    if nav:
        rows.append(nav)
    rows.append([InlineKeyboardButton(text="« Kembali", callback_data="admin_back")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=rows)
    for i, (_, name) in enumerate(categories, start=offset+1):
        text += f"{i}. {name}\n"
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)
    await callback.answer()
    await state.update_data(current_item_page=page)

@router.callback_query(F.data.startswith("item_cat_page_"))
async def item_cat_page(callback: CallbackQuery, state: FSMContext):
    page = int(callback.data.split("_")[3])
    await list_categories_page(callback, state, page)

# ========== HALAMAN 2: DAFTAR SUBKATEGORI ==========
@router.callback_query(F.data.startswith("item_cat_"))
async def list_subcategories_for_item(callback: CallbackQuery, state: FSMContext, page: int = 1):
    index = int(callback.data.split("_")[2])
    # dapatkan page kategori yang sedang aktif dari state
    cat_page = (await state.get_data()).get('current_item_page', 1)
    offset_cat = (cat_page - 1) * ITEMS_PER_PAGE
    categories, _ = await get_all_categories(ITEMS_PER_PAGE, offset_cat)
    pos = index - offset_cat - 1
    if pos < 0 or pos >= len(categories):
        await callback.answer("Kategori tidak ditemukan.", show_alert=True)
        return
    category_id = categories[pos][0]
    await state.update_data(selected_category_id=category_id)
    offset = (page - 1) * ITEMS_PER_PAGE
    subs, total = await get_subcategories_by_category(category_id, ITEMS_PER_PAGE, offset)
    total_pages = (total + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
    cat_name = await get_category_name(category_id)
    if not subs:
        text = f"📂 *{cat_name}*\nBelum ada subkategori."
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="« Kembali", callback_data="admin_item")]
        ])
        await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)
        await callback.answer()
        return
    text = f"📂 *{cat_name} (Halaman {page}/{total_pages})*\n\n"
    row_angka = [InlineKeyboardButton(text=pad_center(str(i), BUTTON_WIDTH), callback_data=f"item_sub_{i}") for i in range(offset+1, offset+len(subs)+1)]
    rows = [row_angka[i:i+BUTTON_COLS] for i in range(0, len(row_angka), BUTTON_COLS)]
    nav = []
    if page > 1:
        nav.append(InlineKeyboardButton(text="◀ Sebelumnya", callback_data=f"item_sub_page_{category_id}_{page-1}"))
    if page < total_pages:
        nav.append(InlineKeyboardButton(text="Berikutnya ▶", callback_data=f"item_sub_page_{category_id}_{page+1}"))
    if nav:
        rows.append(nav)
    rows.append([InlineKeyboardButton(text="« Kembali", callback_data="admin_item")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=rows)
    for i, (_, name, price) in enumerate(subs, start=offset+1):
        text += f"{i}. {name} - Rp{format_rupiah(price)}\n"
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)
    await callback.answer()
    await state.update_data(selected_subcategory_page=page)

@router.callback_query(F.data.startswith("item_sub_page_"))
async def item_sub_page(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    category_id = int(parts[3])
    page = int(parts[4])
    await state.update_data(selected_category_id=category_id)
    await list_subcategories_for_item(callback, state, page)

# ========== SUBKATEGORI DIPILIH => MENU ITEM ==========
@router.callback_query(F.data.startswith("item_sub_"))
async def select_subcategory(callback: CallbackQuery, state: FSMContext):
    index = int(callback.data.split("_")[2])
    data = await state.get_data()
    category_id = data.get('selected_category_id')
    if not category_id:
        await callback.answer("Sesi kadaluarsa.", show_alert=True)
        return
    page = data.get('selected_subcategory_page', 1)
    offset = (page - 1) * ITEMS_PER_PAGE
    subs, _ = await get_subcategories_by_category(category_id, ITEMS_PER_PAGE, offset)
    pos = index - offset - 1
    if 0 <= pos < len(subs):
        sub_id = subs[pos][0]
        sub_name = subs[pos][1]
        await state.update_data(selected_subcategory_id=sub_id)
        cat_name = await get_category_name(category_id)
        text = f"🎫 *Manajemen Item*\nKategori: {cat_name}\nSubkategori: {sub_name}\n\nPilih aksi:"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📥 Impor Item (CSV)", callback_data="item_import"),
            InlineKeyboardButton(text="✏️ Tambah Item Manual", callback_data="item_manual")],
            [InlineKeyboardButton(text="📤 Ekspor Item (CSV)", callback_data="item_export"),
            InlineKeyboardButton(text="🗑️ Hapus Item Terpakai", callback_data="item_delete_used")],
            [InlineKeyboardButton(text="📋 Lihat Daftar Item", callback_data="item_list"),
            InlineKeyboardButton(text="⚙️ Atur Auto Delete", callback_data="item_auto")],
            [InlineKeyboardButton(text="« Kembali", callback_data="admin_item")]
        ])
        await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)
    else:
        await callback.answer("Subkategori tidak ditemukan.", show_alert=True)
    await callback.answer()

# ========== FUNCTION UNTUK MENAMPILKAN MENU ITEM (DIPAKAI UNTUK BACK) ==========
async def show_item_menu(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    sub_id = data.get('selected_subcategory_id')
    cat_id = data.get('selected_category_id')
    if not sub_id or not cat_id:
        await callback.answer("Sesi kadaluarsa, silakan pilih ulang.", show_alert=True)
        return
    cat_name = await get_category_name(cat_id)
    sub_name = await get_subcategory_name(sub_id)
    text = f"🎫 *Manajemen Item*\nKategori: {cat_name}\nSubkategori: {sub_name}\n\nPilih aksi:"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📥 Impor Item (CSV)", callback_data="item_import"),
        InlineKeyboardButton(text="✏️ Tambah Item Manual", callback_data="item_manual")],
        [InlineKeyboardButton(text="📤 Ekspor Item (CSV)", callback_data="item_export"),
        InlineKeyboardButton(text="🗑️ Hapus Item Terpakai", callback_data="item_delete_used")],
        [InlineKeyboardButton(text="📋 Lihat Daftar Item", callback_data="item_list"),
        InlineKeyboardButton(text="⚙️ Atur Auto Delete", callback_data="item_auto")],
        [InlineKeyboardButton(text="« Kembali", callback_data="admin_item")]
    ])
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)

# ========== HANDLER BACK ==========
@router.callback_query(F.data == "item_back")
async def back_to_item_menu(callback: CallbackQuery, state: FSMContext):
    await show_item_menu(callback, state)

# ========== IMPOR CSV ==========
@router.callback_query(F.data == "item_import")
async def import_csv_prompt(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Kirimkan file CSV (satu kolom `code`).")
    await state.set_state(ItemState.waiting_import_file)
    await callback.answer()

@router.message(ItemState.waiting_import_file, F.document)
async def import_csv_file(message: Message, state: FSMContext):
    if not message.document.file_name.endswith('.csv'):
        await message.answer("Harap kirim file CSV.")
        return
    data = await state.get_data()
    sub_id = data.get('selected_subcategory_id')
    if not sub_id:
        await message.answer("Sesi kadaluarsa, silakan pilih ulang subkategori.")
        return
    file = await message.bot.get_file(message.document.file_id)
    file_bytes = await message.bot.download_file(file.file_path)
    content = file_bytes.read().decode('utf-8')
    reader = csv.reader(io.StringIO(content))
    next(reader, None)  # skip header
    codes = [row[0].strip() for row in reader if row]
    if not codes:
        await message.answer("File tidak mengandung data.")
        return
    added = 0
    for code in codes:
        try:
            await add_item(sub_id, code)
            added += 1
        except Exception:
            continue
    await message.answer(f"✅ Berhasil mengimpor {added} dari {len(codes)} kode.")
    await state.clear()
    await show_item_menu(message, state)

# ========== TAMBAH MANUAL ==========
@router.callback_query(F.data == "item_manual")
async def manual_codes_prompt(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Kirimkan daftar kode, satu per baris.\nContoh:\nCODE123\nCODE456\nKetik /batal untuk membatalkan.")
    await state.set_state(ItemState.waiting_manual_codes)
    await callback.answer()

@router.message(ItemState.waiting_manual_codes, F.text)
async def manual_codes_received(message: Message, state: FSMContext):
    if message.text == "/batal":
        await message.answer("Operasi dibatalkan.")
        await state.clear()
        return
    codes = [line.strip() for line in message.text.split('\n') if line.strip()]
    data = await state.get_data()
    sub_id = data.get('selected_subcategory_id')
    if not sub_id:
        await message.answer("Sesi kadaluarsa, silakan pilih ulang subkategori.")
        return
    added = 0
    for code in codes:
        try:
            await add_item(sub_id, code)
            added += 1
        except Exception:
            continue
    await message.answer(f"✅ Berhasil menambahkan {added} dari {len(codes)} kode.")
    await state.clear()
    await show_item_menu(message, state)

# ========== EKSPOR CSV ==========
@router.callback_query(F.data == "item_export")
async def export_csv(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    sub_id = data.get('selected_subcategory_id')
    if not sub_id:
        await callback.message.answer("Sesi kadaluarsa, silakan pilih ulang subkategori.")
        return
    codes = await export_items_csv(sub_id)
    if not codes:
        await callback.message.answer("Tidak ada item tersedia (stok habis).")
        return
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['code'])
    for code in codes:
        writer.writerow([code])
    output.seek(0)
    bytes_io = io.BytesIO(output.getvalue().encode('utf-8'))
    await callback.message.answer_document(
        document=BufferedInputFile(bytes_io.getvalue(), filename=f"items_{sub_id}.csv"),
        caption="Berikut daftar item yang tersedia."
    )
    await callback.answer()

# ========== HAPUS ITEM TERPAKAI ==========
@router.callback_query(F.data == "item_delete_used")
async def delete_used(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    sub_id = data.get('selected_subcategory_id')
    if not sub_id:
        await callback.message.answer("Sesi kadaluarsa, silakan pilih ulang subkategori.")
        return
    deleted = await delete_used_items(sub_id)
    await callback.message.answer(f"✅ Berhasil menghapus {deleted} item terpakai.")
    await show_item_menu(callback, state)

# ========== LIHAT DAFTAR ITEM ==========
@router.callback_query(F.data == "item_list")
async def list_items(callback: CallbackQuery, state: FSMContext, page: int = 1):
    data = await state.get_data()
    sub_id = data.get('selected_subcategory_id')
    if not sub_id:
        await callback.answer("Sesi kadaluarsa.", show_alert=True)
        return
    limit = 10
    offset = (page - 1) * limit
    items, total = await get_items_by_subcategory(sub_id, limit, offset)
    total_pages = (total + limit - 1) // limit
    if not items:
        text = "📭 Belum ada item untuk subkategori ini."
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="« Kembali", callback_data="item_back")]])
        await callback.message.edit_text(text, reply_markup=keyboard)
        await callback.answer()
        return
    text = f"📋 *Daftar Item (Halaman {page}/{total_pages})*\n\n"
    for item_id, code, is_used in items:
        status = "✅ Terpakai" if is_used else "🟢 Tersedia"
        text += f"• `{code}` - {status}\n"
    nav = []
    if page > 1:
        nav.append(InlineKeyboardButton(text="◀ Sebelumnya", callback_data=f"item_list_page_{page-1}"))
    if page < total_pages:
        nav.append(InlineKeyboardButton(text="Berikutnya ▶", callback_data=f"item_list_page_{page+1}"))
    keyboard_buttons = []
    if nav:
        keyboard_buttons.append(nav)
    keyboard_buttons.append([InlineKeyboardButton(text="« Kembali", callback_data="item_back")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)
    await callback.answer()
    await state.update_data(item_list_page=page)

@router.callback_query(F.data.startswith("item_list_page_"))
async def item_list_page(callback: CallbackQuery, state: FSMContext):
    page = int(callback.data.split("_")[3])
    await list_items(callback, state, page)

# ========== ATUR AUTO DELETE ==========
@router.callback_query(F.data == "item_auto")
async def auto_delete_prompt(callback: CallbackQuery, state: FSMContext):
    current = await get_auto_delete_days()
    await callback.message.answer(f"Saat ini auto delete: {current} hari.\nKirimkan angka baru (0 untuk menonaktifkan):")
    await state.set_state(ItemState.waiting_auto_delete)
    await callback.answer()

@router.message(ItemState.waiting_auto_delete)
async def set_auto_delete(message: Message, state: FSMContext):
    try:
        days = int(message.text.strip())
        if days < 0:
            raise ValueError
    except Exception:
        await message.answer("❌ Masukkan angka positif (0 untuk matikan).")
        return
    await set_auto_delete_days(days)
    await message.answer(f"✅ Auto delete diatur menjadi {days} hari.")
    await state.clear()
    await show_item_menu(message, state)