# source/handlers/admin/s4_data.py
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message, BufferedInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from source.config import BOT_TOKEN
from source.database.queries import (
    get_category_by_name, add_category,
    get_subcategory_by_name, add_subcategory, add_item,
    export_all_items_data
)
import csv, io

router = Router()
bot = Bot(token=BOT_TOKEN)

class DataState(StatesGroup):
    waiting_import_file = State()

@router.callback_query(F.data == "admin_data")
async def data_menu(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📤 Ekspor Data (CSV)", callback_data="export_data")],
        [InlineKeyboardButton(text="📥 Impor Data (CSV)", callback_data="import_data")],
        [InlineKeyboardButton(text="« Kembali", callback_data="admin_back")]
    ])
    await callback.message.edit_text("📁 *Manajemen Data*", parse_mode="Markdown", reply_markup=keyboard)
    await callback.answer()

# ========== EKSPOR ==========
@router.callback_query(F.data == "export_data")
async def export_data(callback: CallbackQuery):
    data = await export_all_items_data()
    if not data:
        await callback.message.answer("📭 Tidak ada data untuk diekspor.")
        await callback.answer()
        return
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['kategori', 'subkategori', 'item_code', 'harga'])
    for cat, sub, code, price in data:
        writer.writerow([cat, sub, code, price])
    output.seek(0)
    bytes_io = io.BytesIO(output.getvalue().encode('utf-8'))
    await callback.message.answer_document(
        document=BufferedInputFile(bytes_io.getvalue(), filename="data_export.csv"),
        caption="✅ Berikut data lengkap toko (kategori, subkategori, item, harga)."
    )
    await callback.answer()

# ========== IMPOR ==========
@router.callback_query(F.data == "import_data")
async def import_prompt(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("📂 Kirimkan file CSV dengan format:\n\n`kategori,subkategori,item_code,harga`\n\nContoh:\nCanva,Pro,user123:pass123,50000\nCanva,Pro,user456:pass456,50000\nNetflix,1 bulan,netflix1:pass1,30000\n\n*Perhatian:* File tidak boleh mengandung header (baris pertama harus data).")
    await state.set_state(DataState.waiting_import_file)
    await callback.answer()

@router.message(DataState.waiting_import_file, F.document)
async def process_import(message: Message, state: FSMContext):
    if not message.document.file_name.endswith('.csv'):
        await message.answer("❌ Harap kirim file CSV.")
        return
    file = await bot.get_file(message.document.file_id)
    file_bytes = await bot.download_file(file.file_path)
    content = file_bytes.read().decode('utf-8')
    reader = csv.reader(io.StringIO(content))
    rows = list(reader)
    if not rows:
        await message.answer("❌ File kosong.")
        return
    added_cat = 0
    added_sub = 0
    added_item = 0
    skip_item = 0
    for row in rows:
        if len(row) < 4:
            continue
        cat_name, sub_name, item_code, price_str = row[0].strip(), row[1].strip(), row[2].strip(), row[3].strip()
        if not cat_name or not sub_name or not item_code:
            continue
        try:
            price = int(price_str)
        except Exception:
            continue
        # Cari atau buat kategori
        cat = await get_category_by_name(cat_name)
        if not cat:
            cat_id = await add_category(cat_name)
            added_cat += 1
        else:
            cat_id = cat[0]
        # Cari atau buat subkategori
        sub = await get_subcategory_by_name(cat_id, sub_name)
        if not sub:
            sub_id = await add_subcategory(cat_id, sub_name, price)
            added_sub += 1
        else:
            sub_id = sub[0]
        # Tambah item (abaikan jika duplikat)
        try:
            await add_item(sub_id, item_code)
            added_item += 1
        except Exception:
            skip_item += 1
    await message.answer(f"✅ Impor selesai.\n"
                         f"Kategori baru: {added_cat}\n"
                         f"Subkategori baru: {added_sub}\n"
                         f"Item baru: {added_item}\n"
                         f"Item duplikat (dilewati): {skip_item}")
    await state.clear()