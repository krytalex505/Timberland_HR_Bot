
import asyncio
from aiogram import Bot
from config import TOKEN
from scheduler import send_adaptation_form

async def test_send_form():
    """Тест отправки формы"""
    bot = Bot(token=TOKEN)
    
    # Замените на реальный ID пользователя Влады
    # Если не знаете ID, сначала запустите команду /users
    test_user_id = 123456789  # Замените на реальный ID
    
    print(f"🧪 Тестирую отправку формы пользователю ID: {test_user_id}")
    
    try:
        success = await send_adaptation_form(bot, test_user_id)
        if success:
            print("✅ Форма отправлена успешно!")
        else:
            print("❌ Не удалось отправить форму")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    await bot.session.close()

if __name__ == "__main__":
    asyncio.run(test_send_form())