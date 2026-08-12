from aiogram import Router, types, F
from database import get_user
from keyboards.reply import main_menu

router = Router()

@router.message()
async def fallback_handler(message: types.Message):
    """Обработчик всех остальных сообщений"""
    user = await get_user(message.from_user.id)
    is_hr = user.get('is_hr', False) if user else False
    
    await message.answer(
        "🤔 Не понимаю команду. Пожалуйста, используйте кнопки меню.",
        reply_markup=main_menu(is_hr=is_hr)
    )