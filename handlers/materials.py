from aiogram import Router, types, F
from database import get_user
from keyboards.reply import main_menu

router = Router()

MATERIALS_TEXT = (
    "📂 <b>Регламенты компании</b>\n\n"
    "• <b>Кодекс корпоративной этики</b> — "
    "<a href='https://docs.google.com/document/d/1o2_4X1kDx7aLMOhLCVI8meJeAHHmI3pv/edit?usp=sharing&ouid=110172262026327886716&rtpof=true&sd=true'>открыть</a>\n"
    "• <b>Правила внутреннего трудового распорядка</b> — "
    "<a href='https://drive.google.com/file/d/1cCJSnDP7MuITd5WCiKdLq5r4ZFmTnVOo/view?usp=sharing'>открыть</a>"
)

@router.message(F.text == "📂 Регламенты компании")
async def materials_info(message: types.Message):
    """Регламенты компании"""
    user = await get_user(message.from_user.id)
    is_hr = user.get('is_hr', False) if user else False
    
    # Создаем клавиатуру с кнопкой "Назад в меню"
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="⬅️ В меню")]
        ],
        resize_keyboard=True
    )
    
    await message.answer(
        MATERIALS_TEXT, 
        parse_mode="HTML", 
        reply_markup=keyboard,
        disable_web_page_preview=True
    )

@router.message(F.text == "⬅️ В меню")
async def back_to_menu(message: types.Message):
    """Возврат в главное меню"""
    user = await get_user(message.from_user.id)
    is_hr = user.get('is_hr', False) if user else False
    
    await message.answer(
        "Главное меню:",
        reply_markup=main_menu(is_hr=is_hr)
    )