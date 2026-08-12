from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime
from database import save_user, get_user, delete_user
from config import HR_CHAT_ID
from database import get_active_chat
# ИСПРАВЛЕННЫЙ ИМПОРТ из папки keyboards:
from keyboards.reply import main_menu

router = Router()

# Состояния для регистрации
class RegistrationStates(StatesGroup):
    waiting_for_fio = State()
    waiting_for_department = State()
    waiting_for_position = State()
    waiting_for_hire_date = State()

# Приветственное сообщение
WELCOME_MESSAGE = """
👋 <b>Здравствуйте! Добро пожаловать в компанию Timberland! Мы рады видеть вас в нашей команде.</b>

Я — ваш виртуальный помощник. В период адаптации я буду предоставлять необходимую информацию и помогать с ответами на вопросы.

<b>Для начала работы необходимо пройти регистрацию.</b>
"""

@router.message(F.text == "/start")
async def cmd_start(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    
    if str(user_id) == str(HR_CHAT_ID):
        existing_user = await get_user(user_id)
        
        if not existing_user:
            await save_user(
                user_id=user_id,
                fio=message.from_user.full_name,
                department="HR Отдел",
                position="HR Менеджер",
                hire_date=datetime.now().strftime("%Y-%m-%d"),
                is_hr=True
            )
        
        has_active_chat = False
        employee_id = await get_active_chat(user_id)
        if employee_id:
            has_active_chat = True
        
        welcome_text = "👨‍💼 <b>Добро пожаловать в панель HR!</b>"
        if has_active_chat:
            welcome_text += "\n\n🔔 <b>У вас есть активный диалог!</b>"
        
        await message.answer(
            welcome_text,
            parse_mode="HTML",
            reply_markup=main_menu(is_hr=True)
        )
        await state.clear()
        return
    
    # Дальше обычная регистрация для сотрудников...
    existing_user = await get_user(user_id)
    
    if existing_user:
        await message.answer(
            f"👋 <b>С возвращением, {existing_user['fio']}!</b>",
            parse_mode="HTML",
            reply_markup=main_menu(is_hr=existing_user.get('is_hr', False))
        )
        await state.clear()
        return
    
    # Новый пользователь
    await message.answer(WELCOME_MESSAGE, parse_mode="HTML")
    await message.answer("📝 <b>Начнём регистрацию!</b>\n\n1️⃣ Напишите ваше ФИО (полностью):", parse_mode="HTML")
    await state.set_state(RegistrationStates.waiting_for_fio)

# /reset - удаление данных
@router.message(F.text == "/reset")
async def cmd_reset(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    
    deleted = await delete_user(user_id)
    
    if deleted:
        await state.clear()
        await message.answer(
            "🔄 <b>Ваши данные полностью удалены!</b>\n\n"
            "Для повторной регистрации отправьте /start",
            parse_mode="HTML",
            reply_markup=types.ReplyKeyboardRemove()
        )
    else:
        await message.answer(
            "⚠️ <b>Вы еще не были зарегистрированы.</b>\n\n"
            "Для регистрации отправьте /start",
            parse_mode="HTML"
        )

# ФИО
@router.message(RegistrationStates.waiting_for_fio)
async def process_fio(message: types.Message, state: FSMContext):
    if len(message.text.strip()) < 5:
        await message.answer("❌ ФИО слишком короткое. Введите полное ФИО:")
        return
    
    await state.update_data(fio=message.text.strip())
    await message.answer("✅ ФИО сохранено!\n\n2️⃣ Укажите ваше подразделение:")
    await state.set_state(RegistrationStates.waiting_for_department)

# Подразделение
@router.message(RegistrationStates.waiting_for_department)
async def process_department(message: types.Message, state: FSMContext):
    if len(message.text.strip()) < 2:
        await message.answer("❌ Название слишком короткое. Введите корректное название:")
        return
    
    await state.update_data(department=message.text.strip())
    await message.answer("✅ Подразделение сохранено!\n\n3️⃣ Укажите вашу должность:")
    await state.set_state(RegistrationStates.waiting_for_position)

# Должность
@router.message(RegistrationStates.waiting_for_position)
async def process_position(message: types.Message, state: FSMContext):
    if len(message.text.strip()) < 2:
        await message.answer("❌ Должность слишком короткая. Введите корректную должность:")
        return
    
    await state.update_data(position=message.text.strip())
    await message.answer("✅ Должность сохранена!\n\n4️⃣ Укажите дату приёма на работу (ДД.ММ.ГГГГ):")
    await state.set_state(RegistrationStates.waiting_for_hire_date)

# Дата приёма
@router.message(RegistrationStates.waiting_for_hire_date)
async def process_hire_date(message: types.Message, state: FSMContext):
    try:
        hire_date = datetime.strptime(message.text.strip(), "%d.%m.%Y")
        hire_date_str = hire_date.strftime("%Y-%m-%d")
    except ValueError:
        await message.answer("❌ Неверный формат. Используйте ДД.ММ.ГГГГ (например: 15.01.2023):")
        return
    
    user_data = await state.get_data()
    
    # Проверяем HR или сотрудник
    is_hr = str(message.from_user.id) == str(HR_CHAT_ID)
    
    await save_user(
        user_id=message.from_user.id,
        fio=user_data['fio'],
        department=user_data['department'],
        position=user_data['position'],
        hire_date=hire_date_str,
        is_hr=is_hr
    )
    
    await state.clear()
    
    await message.answer(
        f"🎉 <b>Регистрация завершена!</b>\n\n"
        f"<b>Ваши данные:</b>\n"
        f"• ФИО: {user_data['fio']}\n"
        f"• Подразделение: {user_data['department']}\n"
        f"• Должность: {user_data['position']}\n"
        f"• Дата приёма: {hire_date.strftime('%d.%m.%Y')}",
        parse_mode="HTML",
        reply_markup=main_menu(is_hr=is_hr)
    )