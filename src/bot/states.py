from aiogram.fsm.state import State, StatesGroup

class ContactAdminStates(StatesGroup):
    waiting_for_message = State()

class AddChannelStates(StatesGroup):
    waiting_for_username = State()

class TokenAuditStates(StatesGroup):
    waiting_for_address = State()
