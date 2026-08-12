import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties

from config import TOKEN, HR_CHAT_ID
from database import init_db
from scheduler import start_scheduler

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

async def main():
    print("🤖 Бот запускается...")
    print("=" * 50)
    
    # Инициализация БД
    try:
        await init_db()
        print("✅ База данных инициализирована")
    except Exception as e:
        print(f"❌ Ошибка БД: {e}")
        return
    
    # Создаем бота
    try:
        bot = Bot(
            token=TOKEN,
            default=DefaultBotProperties(parse_mode="HTML")
        )
        print(f"✅ Бот создан")
    except Exception as e:
        print(f"❌ Ошибка создания бота: {e}")
        return
    
    dp = Dispatcher(storage=MemoryStorage())
    
    print("\n📂 Загрузка хендлеров:")
    print("-" * 30)
    
    try:
        from handlers.start import router as start_router
        dp.include_router(start_router)
        print("✅ Старт и регистрация")
    except Exception as e:
        print(f"❌ start.py: {e}")

    try:
        from handlers.commands import router as commands_router
        dp.include_router(commands_router)
        print("✅ Команды админ-панели")
    except Exception as e:
        print(f"❌ commands.py: {e}")

    try:
        from handlers.general import router as general_router
        dp.include_router(general_router)
        print("✅ Общая информация")
    except Exception as e:
        print(f"❌ general.py: {e}")
    
    try:
        from handlers.materials import router as materials_router
        dp.include_router(materials_router)
        print("✅ Регламенты")
    except Exception as e:
        print(f"❌ materials.py: {e}")
    
    try:
        from handlers.hr_contact import router as hr_contact_router
        dp.include_router(hr_contact_router)
        print("✅ Чат HR-сотрудник")
    except Exception as e:
        print(f"❌ hr_contact.py: {e}")
        import traceback
        traceback.print_exc()
    
    # ⭐⭐⭐ ДОБАВЛЕН ИМПОРТ ПАМЯТКИ ⭐⭐⭐
    try:
        from handlers.memo import router as memo_router
        dp.include_router(memo_router)
        print("✅ Памятка сотрудника (PDF)")
    except Exception as e:
        print(f"❌ memo.py: {e}")
    
    try:
        from handlers.admin import router as admin_router
        dp.include_router(admin_router)
        print("✅ Админ-команды")
    except Exception as e:
        print(f"❌ admin.py: {e}")
    
    try:
        from handlers.fallback import router as fallback_router
        dp.include_router(fallback_router)
        print("✅ Обработчик ошибок")
    except Exception as e:
        print(f"❌ fallback.py: {e}")
    
    print("-" * 30)
    
    # ЗАПУСК ПЛАНИРОВЩИКА
    print("⏰ Запуск планировщика форм адаптации...")
    try:
        await start_scheduler(bot)
        print("✅ Планировщик форм адаптации запущен")
    except Exception as e:
        print(f"⚠️ Не удалось запустить планировщик: {e}")
    
    print(f"\n👤 HR ID: {HR_CHAT_ID}")
    print("=" * 50)
    
    # Уведомление HR
    try:
        await bot.send_message(
            HR_CHAT_ID,
            "🤖 <b>Бот запущен!</b>\n\n"
            "Статус: <code>работает</code>\n"
            f"ID: <code>{HR_CHAT_ID}</code>\n\n"
            "💡 <b>Новая функция:</b> автоматическая отправка формы адаптации "
            "через 10 дней после приема сотрудника.\n\n"
            "Теперь вы можете использовать функции отдела персонала.\n"
            "Используйте /start для начала работы.",
            parse_mode="HTML"
        )
        print("📨 Уведомление отправлено HR")
    except Exception as e:
        print(f"⚠️ Не удалось отправить уведомление HR: {e}")
    
    print("\n🚀 Бот запущен и готов к работе!")
    print("⏰ Планировщик форм адаптации активен")
    print("⏳ Ожидание сообщений...")
    print("Для остановки нажмите Ctrl+C")
    print("=" * 50)
    
    try:
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("🔄 Завершение работы...")
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())