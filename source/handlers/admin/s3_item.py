# source/handlers/admin/s3_item.py

import csv
import io
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from source.database.queries import (
    get_all_categories,
    get_subcategories_by_category,
    get_category_name,
    get_subcategory_name,
    add_item,
    get_available_items_by_subcategory,
    get_item_by_id,
    edit_item_code,
    delete_single_item,
    get_used_items_count_by_subcategory,
)
from source.utils.helpers import pad_center, format_rupiah
from source.config import BOT_TOKEN

router = Router()
bot = Bot(token=BOT_TOKEN)

ITEMS_PER_PAGE = 10
BUTTON_COLS = 5
BUTTON_WIDTH = 12


class ItemState(StatesGroup):
    waiting_csv = State()
    waiting_manual = State()
    waiting_edit_code = State()


# ── Fungsi bantu ──────────────────────────────────────────────
async def get_available_count(subcategory_id: int) -> int:
    _, total = await get_available_items_by_subcategory(subcategory_id, limit=1, offset=0)
    return total


def action_menu_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📤 Ekspor CSV", callback_data="item_export"),
            InlineKeyboardButton(text="📥 Impor CSV", callback_data="item_import"),
        ],
        [
            InlineKeyboardButton(text="📋 Daftar Item", callback_data="item_list"),
            InlineKeyboardButton(text="✏️ Tambah Item", callback_data="item_manual"),
        ],
        [
            InlineKeyboardButton(text="✏️ Edit Item", callback_data="item_edit"),
            InlineKeyboardButton(text="🗑️ Hapus Item", callback_data="item_delete"),
        ],
        [InlineKeyboardButton(text="« Kembali", callback_data="admin_item")],
    ])


def item_list_keyboard(items, page, total_pages, offset, subcategory_id):
    buttons = []
    for i, (item_id, _) in enumerate(items, start=offset + 1):
        buttons.append(
            InlineKeyboardButton(
                text=pad_center(str(i), BUTTON_WIDTH),
                callback_data=f"itemselect_{item_id}",
            )
        )
    rows = [buttons[i:i + BUTTON_COLS] for i in range(0, len(buttons), BUTTON_COLS)]

    nav = []
    if page > 1:
        nav.append(InlineKeyboardButton(text="◀", callback_data=f"itempage_{subcategory_id}_{page - 1}"))
    if page < total_pages:
        nav.append(InlineKeyboardButton(text="▶", callback_data=f"itempage_{subcategory_id}_{page + 1}"))
    if nav:
        rows.append(nav)

    rows.append([InlineKeyboardButton(text="« Kembali", callback_data="item_back_to_menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def show_item_menu(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    sub_id = data.get("selected_subcategory_id")
    cat_name = data.get("selected_category_name", "Kategori")
    sub_name = await get_subcategory_name(sub_id)

    avail = await get_available_count(sub_id)
    used = await get_used_items_count_by_subcategory(sub_id)
    total = avail + used

    text = (
        f"📂 *{cat_name}*\n"
        f"📦 *{sub_name}*\n\n"
        f"🟢 Stok Tersedia: {avail}\n"
        f"🔴 Stok Terpakai: {used}\n"
        f"📊 Stok Total: {total}\n\n"
        f"*Pilih aksi:*"
    )
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=action_menu_keyboard())
    await callback.answer()


async def show_item_menu_from_message(message: Message, state: FSMContext, sub_id: int = None, cat_name: str = None):
    if sub_id is None or cat_name is None:
        data = await state.get_data()
        sub_id = data.get("selected_subcategory_id")
        cat_name = data.get("selected_category_name", "Kategori")

    sub_name = await get_subcategory_name(sub_id)
    avail = await get_available_count(sub_id)
    used = await get_used_items_count_by_subcategory(sub_id)
    total = avail + used

    text = (
        f"📂 *{cat_name}*\n"
        f"📦 *{sub_name}*\n\n"
        f"🟢 Stok Tersedia: {avail}\n"
        f"🔴 Stok Terpakai: {used}\n"
        f"📊 Stok Total: {total}\n\n"
        f"*Pilih aksi:*"
    )
    await message.answer(text, parse_mode="Markdown", reply_markup=action_menu_keyboard())


# ── Entry: Pilih Kategori ────────────────────────────────────
@router.callback_query(F.data == "admin_item")
async def item_start(callback: CallbackQuery):
    await callback.answer()
    await show_categories_for_item(callback, page=1)


async def show_categories_for_item(callback: CallbackQuery, page: int):
    offset = (page - 1) * ITEMS_PER_PAGE
    cats, total = await get_all_categories(ITEMS_PER_PAGE, offset)
    if not cats:
        await callback.message.edit_text("❌ Belum ada kategori.")
        return

    total_pages = (total + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
    text = "📂 *Pilih Kategori*\n\n"
    for i, (cat_id, name) in enumerate(cats, start=offset + 1):
        text += f"{i}. {name}\n"

    buttons = []
    for i, (cat_id, _) in enumerate(cats, start=offset + 1):
        buttons.append(InlineKeyboardButton(text=pad_center(str(i), BUTTON_WIDTH), callback_data=f"itemcat_{cat_id}"))
    rows = [buttons[i:i + BUTTON_COLS] for i in range(0, len(buttons), BUTTON_COLS)]

    nav = []
    if page > 1:
        nav.append(InlineKeyboardButton(text="◀", callback_data=f"itemcatpage_{page - 1}"))
    if page < total_pages:
        nav.append(InlineKeyboardButton(text="▶", callback_data=f"itemcatpage_{page + 1}"))
    if nav:
        rows.append(nav)

    rows.append([InlineKeyboardButton(text="« Kembali ke Panel", callback_data="admin_back")])
    kb = InlineKeyboardMarkup(inline_keyboard=rows)
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=kb)


@router.callback_query(F.data.startswith("itemcatpage_"))
async def item_cat_page(callback: CallbackQuery):
    await callback.answer()
    page = int(callback.data.split("_")[1])
    await show_categories_for_item(callback, page)


@router.callback_query(F.data.startswith("itemcat_"))
async def item_cat_selected(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    cat_id = int(callback.data.split("_")[1])
    await state.update_data(selected_category_id=cat_id)
    await show_subcategories_for_item(callback, state, cat_id, page=1)


# ── Pilih Subkategori ────────────────────────────────────────
async def show_subcategories_for_item(callback: CallbackQuery, state: FSMContext, cat_id: int, page: int):
    offset = (page - 1) * ITEMS_PER_PAGE
    subs, total = await get_subcategories_by_category(cat_id, ITEMS_PER_PAGE, offset)
    if not subs:
        await callback.message.edit_text(
            "❌ Belum ada subkategori di kategori ini.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="« Kembali", callback_data="admin_item")]
            ]),
        )
        return

    total_pages = (total + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
    cat_name = await get_category_name(cat_id)
    await state.update_data(selected_category_name=cat_name)

    text = f"📂 *{cat_name}* (Halaman {page}/{total_pages})\n\n"
    for i, (sub_id, name, price) in enumerate(subs, start=offset + 1):
        available_count = await get_available_count(sub_id)
        text += f"{i}. {name} - Rp{format_rupiah(price)} (Stok: {available_count})\n"

    buttons = []
    for i, (sub_id, _, _) in enumerate(subs, start=offset + 1):
        buttons.append(InlineKeyboardButton(text=pad_center(str(i), BUTTON_WIDTH), callback_data=f"itemsub_{sub_id}"))
    rows = [buttons[i:i + BUTTON_COLS] for i in range(0, len(buttons), BUTTON_COLS)]

    nav = []
    if page > 1:
        nav.append(InlineKeyboardButton(text="◀", callback_data=f"itemsubpage_{cat_id}_{page - 1}"))
    if page < total_pages:
        nav.append(InlineKeyboardButton(text="▶", callback_data=f"itemsubpage_{cat_id}_{page + 1}"))
    if nav:
        rows.append(nav)

    rows.append([InlineKeyboardButton(text="« Kembali", callback_data="admin_item")])
    kb = InlineKeyboardMarkup(inline_keyboard=rows)
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=kb)


@router.callback_query(F.data.startswith("itemsubpage_"))
async def item_sub_page(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    parts = callback.data.split("_")
    cat_id = int(parts[1])
    page = int(parts[2])
    await show_subcategories_for_item(callback, state, cat_id, page)


@router.callback_query(F.data.startswith("itemsub_"))
async def item_sub_selected(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    sub_id = int(callback.data.split("_")[1])
    await state.update_data(selected_subcategory_id=sub_id)
    await show_item_menu(callback, state)


# ── EKSPOR CSV ────────────────────────────────────────────────
@router.callback_query(F.data == "item_export")
async def export_items(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    sub_id = data.get("selected_subcategory_id")
    items, _ = await get_available_items_by_subcategory(sub_id, limit=10000, offset=0)
    if not items:
        await callback.answer("Tidak ada item tersedia untuk diekspor.", show_alert=True)
        return

    output = io.StringIO()
    for _, code in items:
        output.write(f"{code}\n")
    output.seek(0)
    await callback.message.answer_document(
        document=output.getvalue().encode(),
        visible_file_name=f"items_sub{sub_id}.csv",
        caption="✅ Ekspor item tersedia.",
    )
    await show_item_menu(callback, state)


# ── DAFTAR ITEM ──────────────────────────────────────────────
@router.callback_query(F.data == "item_list")
async def list_items(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await show_item_list(callback, state, page=1)


async def show_item_list(callback: CallbackQuery, state: FSMContext, page: int):
    data = await state.get_data()
    sub_id = data.get("selected_subcategory_id")
    sub_name = await get_subcategory_name(sub_id)
    offset = (page - 1) * ITEMS_PER_PAGE
    items, total = await get_available_items_by_subcategory(sub_id, ITEMS_PER_PAGE, offset)

    if not items:
        await callback.message.edit_text(
            f"📋 *{sub_name}* - Daftar Item\n\n❌ Tidak ada item tersedia.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="« Kembali", callback_data="item_back_to_menu")]
            ]),
        )
        return

    total_pages = (total + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
    text = f"📋 *{sub_name}* (Hal {page}/{total_pages})\n\n"
    for i, (_, code) in enumerate(items, start=offset + 1):
        text += f"{i}. {code}\n"

    kb = item_list_keyboard(items, page, total_pages, offset, sub_id)
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=kb)
    await state.update_data(item_list_page=page)


@router.callback_query(F.data.startswith("itempage_"))
async def item_list_page(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    parts = callback.data.split("_")
    sub_id = int(parts[1])
    page = int(parts[2])
    await state.update_data(selected_subcategory_id=sub_id)
    await show_item_list(callback, state, page)


@router.callback_query(F.data == "item_back_to_menu")
async def item_back_to_menu(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await show_item_menu(callback, state)


# ── EDIT ITEM (mode) ─────────────────────────────────────────
@router.callback_query(F.data == "item_edit")
async def edit_item_mode(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(item_action_mode="edit")
    await show_item_list(callback, state, page=1)


@router.callback_query(F.data == "item_delete")
async def delete_item_mode(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(item_action_mode="delete")
    await show_item_list(callback, state, page=1)


# ── Pilih item dari daftar (edit / hapus) ────────────────────
@router.callback_query(F.data.startswith("itemselect_"))
async def item_selected(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    item_id = int(callback.data.split("_")[1])
    item = await get_item_by_id(item_id)
    if not item or item[3] == 1:
        await callback.answer("Item tidak valid atau sudah terpakai.", show_alert=True)
        return

    data = await state.get_data()
    mode = data.get("item_action_mode")

    if mode == "edit":
        await state.update_data(edit_item_id=item_id, edit_old_code=item[2])
        await callback.message.edit_text(
            f"📝 *Edit Item*\nKode saat ini: `{item[2]}`\n\nKirim kode baru:",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="« Batal", callback_data="item_back_to_menu")]
            ]),
        )
        await state.set_state(ItemState.waiting_edit_code)

    elif mode == "delete":
        await state.update_data(delete_item_id=item_id)
        await callback.message.edit_text(
            f"🗑️ *Hapus Item*\nKode: `{item[2]}`\n\nYakin hapus?",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✅ Ya", callback_data="itemdelete_confirm")],
                [InlineKeyboardButton(text="❌ Tidak", callback_data="item_back_to_menu")],
            ]),
        )


# ── Konfirmasi Hapus ─────────────────────────────────────────
@router.callback_query(F.data == "itemdelete_confirm")
async def confirm_delete_item(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    item_id = data.get("delete_item_id")
    if not item_id:
        await callback.answer("Sesi hapus tidak valid.", show_alert=True)
        return

    success = await delete_single_item(item_id)
    if success:
        await callback.answer("Item dihapus.", show_alert=True)
    else:
        await callback.answer("Gagal menghapus item.", show_alert=True)

    await state.update_data(item_action_mode=None)
    await show_item_menu(callback, state)


# ── IMPOR CSV ─────────────────────────────────────────────────
@router.callback_query(F.data == "item_import")
async def import_csv_prompt(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer("📥 Kirim file CSV (satu kode per baris).")
    await state.set_state(ItemState.waiting_csv)


@router.message(ItemState.waiting_csv, F.document)
async def receive_csv(message: Message, state: FSMContext):
    data = await state.get_data()
    sub_id = data.get("selected_subcategory_id")
    cat_name = data.get("selected_category_name", "Kategori")

    file_id = message.document.file_id
    file = await bot.get_file(file_id)
    content = await bot.download_file(file.file_path)
    reader = csv.reader(io.StringIO(content.decode()))
    added = 0
    for row in reader:
        if row:
            code = row[0].strip()
            if code:
                await add_item(sub_id, code)
                added += 1

    await message.delete()
    await state.set_state(None)   # hanya nonaktifkan FSM

    sub_name = await get_subcategory_name(sub_id)
    avail = await get_available_count(sub_id)
    used = await get_used_items_count_by_subcategory(sub_id)
    total = avail + used

    text = (
        f"✅ {added} item berhasil diimpor.\n\n"
        f"📂 *{cat_name}*\n"
        f"📦 *{sub_name}*\n\n"
        f"🟢 Stok Tersisa: {avail}\n"
        f"🔴 Stok Terpakai: {used}\n"
        f"📊 Stok Total: {total}\n\n"
        f"*Pilih aksi:*"
    )
    await bot.send_message(
        message.chat.id,
        text,
        parse_mode="Markdown",
        reply_markup=action_menu_keyboard()
    )
    
# ── TAMBAH ITEM MANUAL ────────────────────────────────────────
@router.callback_query(F.data == "item_manual")
async def manual_prompt(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer("✏️ Kirim kode item (satu per baris).")
    await state.set_state(ItemState.waiting_manual)

@router.message(ItemState.waiting_manual, F.text)
async def manual_codes_received(message: Message, state: FSMContext):
    data = await state.get_data()
    sub_id = data.get("selected_subcategory_id")
    cat_name = data.get("selected_category_name", "Kategori")

    lines = message.text.strip().split('\n')
    added = 0
    for line in lines:
        code = line.strip()
        if code:
            await add_item(sub_id, code)
            added += 1

    await message.delete()
    await state.set_state(None)   # hanya nonaktifkan FSM

    sub_name = await get_subcategory_name(sub_id)
    avail = await get_available_count(sub_id)
    used = await get_used_items_count_by_subcategory(sub_id)
    total = avail + used

    text = (
        f"✅ {added} item berhasil ditambahkan.\n\n"
        f"📂 *{cat_name}*\n"
        f"📦 *{sub_name}*\n\n"
        f"🟢 Stok Tersisa: {avail}\n"
        f"🔴 Stok Terpakai: {used}\n"
        f"📊 Stok Total: {total}\n\n"
        f"*Pilih aksi:*"
    )
    await bot.send_message(
        message.chat.id,
        text,
        parse_mode="Markdown",
        reply_markup=action_menu_keyboard()
    )


# ── EDIT KODE (menerima input teks) ───────────────────────────
@router.message(ItemState.waiting_edit_code, F.text)
async def receive_new_code(message: Message, state: FSMContext):
    new_code = message.text.strip()
    data = await state.get_data()
    item_id = data.get("edit_item_id")
    sub_id = data.get("selected_subcategory_id")
    cat_name = data.get("selected_category_name", "Kategori")

    if not item_id:
        await message.answer("❌ Sesi edit tidak valid.")
        await state.clear()
        return
    if not new_code:
        await message.answer("❌ Kode tidak boleh kosong.")
        return

    success = await edit_item_code(item_id, new_code)
    if not success:
        await message.answer("❌ Kode sudah ada di subkategori ini. Coba lagi:")
        return

    # Hapus pesan input (kode baru) lalu kirim menu baru
    await message.delete()

    # Nonaktifkan state FSM, tapi biarkan data lain tetap tersimpan
    await state.set_state(None)

    sub_name = await get_subcategory_name(sub_id)
    avail = await get_available_count(sub_id)
    used = await get_used_items_count_by_subcategory(sub_id)
    total = avail + used

    text = (
        f"✅ Kode berhasil diubah.\n\n"
        f"📂 *{cat_name}*\n"
        f"📦 *{sub_name}*\n\n"
        f"🟢 Stok Tersisa: {avail}\n"
        f"🔴 Stok Terpakai: {used}\n"
        f"📊 Stok Total: {total}\n\n"
        f"*Pilih aksi:*"
    )
    await bot.send_message(
        message.chat.id,
        text,
        parse_mode="Markdown",
        reply_markup=action_menu_keyboard()
    )