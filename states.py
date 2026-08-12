from aiogram.fsm.state import State, StatesGroup
from aiogram import Router
router = Router()

class Registration(StatesGroup):
    fio = State()
    department = State()
    position = State()
    start_date = State()


class RoleSelect(StatesGroup):
    department = State()
    job = State()


class Survey(StatesGroup):
    type = State()
    answer = State()


class HRDialog(StatesGroup):
    message = State()
