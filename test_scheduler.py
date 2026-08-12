# test_scheduler.py
import asyncio
import sqlite3
from datetime import datetime, timedelta
from aiogram import Bot
from config import TOKEN
from scheduler import send_adaptation_form

async def test_form_sending():
    """Тест отправки формы конкретному пользователю"""
    bot = Bot(token=TOKEN)
    
    # Укажите ID тестового пользователя
    test_user_id = 8478706262  # Замените на реальный ID
    
    print(f"🧪 Тестирую отправку формы пользователю {test_user_id}...")
    
    try:
        success = await send_adaptation_form(bot, test_user_id)
        if success:
            print("✅ Тест пройден: форма отправлена успешно")
        else:
            print("❌ Тест не пройден: не удалось отправить форму")
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
    
    await bot.session.close()

async def test_database_check():
    """Тест проверки дат в базе данных"""
    print("\n🧪 Тестирую проверку дат в базе данных...")
    
    # Подключаемся к базе данных
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    
    # Получаем всех пользователей
    cursor.execute("SELECT user_id, fio, hire_date, is_hr FROM users")
    users = cursor.fetchall()
    
    today = datetime.now().date()
    
    print(f"\n📊 Всего пользователей: {len(users)}")
    print("=" * 60)
    
    for user in users:
        user_id, fio, hire_date_str, is_hr = user
        
        if is_hr == 1:
            print(f"👨‍💼 HR: {fio} (ID: {user_id}) - пропускаем")
            continue
        
        if not hire_date_str:
            print(f"👤 {fio} (ID: {user_id}) - нет даты приема")
            continue
        
        try:
            hire_date = datetime.strptime(hire_date_str, "%Y-%m-%d").date()
            days_diff = (today - hire_date).days
            
            if days_diff == 10:
                print(f"🎯 {fio} (ID: {user_id}) - СЕГОДНЯ 10-й день! Дата приема: {hire_date_str}")
            else:
                print(f"👤 {fio} (ID: {user_id}) - {days_diff} дней с даты приема: {hire_date_str}")
                
        except Exception as e:
            print(f"❌ {fio} (ID: {user_id}) - ошибка даты: {hire_date_str} - {e}")
    
    conn.close()
    print("=" * 60)

if __name__ == "__main__":
    # Запускаем тесты
    asyncio.run(test_database_check())
    
    # Если нужно протестировать отправку, раскомментируйте:
    # asyncio.run(test_form_sending())