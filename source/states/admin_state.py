from aiogram.fsm.state import State, StatesGroup

class CategoryState(StatesGroup):
    waiting_new_name = State()
    waiting_edit_id = State()
    waiting_edit_name = State()
    waiting_delete_id = State()

class SubcategoryState(StatesGroup):
    selecting_category = State()
    waiting_new_name = State()
    waiting_new_price = State()
    waiting_edit_id = State()
    waiting_edit_name = State()
    waiting_edit_price = State()
    waiting_delete_id = State()

class ItemState(StatesGroup):
    selecting_subcategory = State()
    waiting_import_csv = State()
    waiting_manual_codes = State()
    waiting_delete_used = State()
    waiting_auto_delete = State()
    viewing_codes = State()

class StockState(StatesGroup):
    selecting_subcategory = State()
    waiting_import_csv = State()
    waiting_manual_codes = State()
    waiting_delete_used = State()
    waiting_auto_delete = State()
    viewing_codes = State()

class OrderState(StatesGroup):
    viewing_pending = State()
    viewing_detail = State()