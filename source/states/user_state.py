from aiogram.fsm.state import State, StatesGroup

class UserState(StatesGroup):
    selecting_category = State()
    selecting_subcategory = State()
    input_quantity = State()
    confirming = State()
    waiting_proof = State()