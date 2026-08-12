from aiogram import Router, types, F, Bot
from aiogram.types import FSInputFile
from database import get_user
import os

router = Router()

@router.message(F.text == "📋 Памятка сотрудника")
async def send_memo(message: types.Message, bot: Bot):
    print("🔥🔥🔥 ПАМЯТКА: ОБРАБОТЧИК ВЫЗВАН!")  # ⬅️ ЭТО ДОЛЖНО ПОЯВИТЬСЯ
    user_id = message.from_user.id
    
    user = await get_user(user_id)
    if not user:
        await message.answer("⚠️ Сначала зарегистрируйтесь! Отправьте /start")
        return
    
    if user.get('is_hr', False):
        await message.answer("⛔ Только для сотрудников")
        return
    
    file_path = "files/Памятка_сотрудника.pdf"
    
    if not os.path.exists(file_path):
        await message.answer("❌ Файл памятки не найден")
        return
    
    try:
        doc = FSInputFile(file_path)
        await bot.send_document(user_id, document=doc, caption="📄 Памятка сотрудника")
        print("✅ PDF отправлен!")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")