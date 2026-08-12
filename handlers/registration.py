from aiogram import Router, types, F
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command

from database import save_user, get_user
from keyboards.reply import main_menu

router = Router()

class Registration(StatesGroup):
    waiting_for_fio = State()
    waiting_for_department = State()
    waiting_for_position = State()

# Список отделов
DEPARTMENTS = [
    "1. Бухгалтерия",
    "2. Сектор ИТ",
    "3. Отдел закупок",
    "4. Оптовые продажи (Гомель)",
    "5. Отдел продаж (Минск)",
    "6. Розничные продажи (Гомель)",
    "7. Шоу-рум (Гомель)",
    "8. КТО",
    "9. Производство (Гомель/Минск)",
    "10. Цех фасадов (Гомель)",
    "11. Оптовый склад (Гомель/Минск)",
    "12. Склад ГП (Гомель)",
    "13. Ремонтно-техническая служба",
    "14. Служба качества",
    "15. Энергослужба"
]

# Старт регистрации
async def start_registration(message: types.Message):
    """Начало регистрации"""
    await message.answer(
        "👋 Добро пожаловать!\n\n"
        "Пожалуйста, введите ваше ФИО:"
    )

@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    """Обработчик команды /start"""
    user = await get_user(message.from_user.id)
    
    if user:
        is_hr = user.get('is_hr', False)
        await message.answer(
            f"👋 С возвращением, {user.get('fio', 'Сотрудник')}!",
            reply_markup=main_menu(is_hr=is_hr)
        )
    else:
        await message.answer(
            "👋 Добро пожаловать!\n\n"
            "Пожалуйста, введите ваше ФИО:"
        )
        await state.set_state(Registration.waiting_for_fio)

@router.message(Registration.waiting_for_fio)
async def process_fio(message: types.Message, state: FSMContext):
    """Обработка ФИО"""
    await state.update_data(fio=message.text)
    
    # Создаем клавиатуру с отделами
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for i in range(0, len(DEPARTMENTS), 2):
        row = DEPARTMENTS[i:i+2]
        keyboard.add(*[types.KeyboardButton(text=dept) for dept in row])
    
    await message.answer(
        "Выберите ваш отдел:",
        reply_markup=keyboard
    )
    await state.set_state(Registration.waiting_for_department)

@router.message(Registration.waiting_for_department)
async def process_department(message: types.Message, state: FSMContext):
    """Обработка отдела"""
    if message.text not in DEPARTMENTS:
        await message.answer("Пожалуйста, выберите отдел из списка:")
        return
    
    await state.update_data(department=message.text)
    await message.answer(
        "Введите вашу должность:",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(Registration.waiting_for_position)

@router.message(Registration.waiting_for_position)
async def process_position(message: types.Message, state: FSMContext):
    """Обработка должности"""
    data = await state.get_data()
    
    # Сохраняем пользователя (по умолчанию не HR)
    await save_user(
        user_id=message.from_user.id,
        fio=data['fio'],
        department=data['department'],
        position=message.text,
        is_hr=False
    )
    
    await state.clear()
    
    await message.answer(
        f"✅ Регистрация завершена!\n\n"
        f"👤 <b>{data['fio']}</b>\n"
        f"🏢 {data['department']}\n"
        f"💼 {message.text}\n\n"
        f"Теперь вы можете пользоваться всеми функциями бота.",
        parse_mode="HTML",
        reply_markup=main_menu(is_hr=False)
    )