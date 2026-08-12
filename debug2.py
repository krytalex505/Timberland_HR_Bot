import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
from config import TOKEN

async def test():
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher()
    
    @dp.message(Command("start"))
    async def start_cmd(message: types.Message):
        await message.answer("Тест: бот работает!")
        print(f"Получен /start от {message.from_user.id}")
    
    @dp.message(F.text)
    async def echo(message: types.Message):
        await message.answer(f"Вы написали: {message.text}")
        print(f"Текст: {message.text}")
    
    print("🤖 Тестовый бот запущен")
    await dp.start_polling(bot)

asyncio.run(test())