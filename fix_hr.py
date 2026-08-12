# fix_hr.py
import asyncio
import sys
import os

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import db

async def fix_hr_user():
    """Добавить пользователя HR в базу данных"""
    
    # ID HR из вашего config.py
    hr_user_id = 749151832
    hr_name = "HR Специалист"
    
    print(f"🔄 Добавляем HR пользователя...")
    print(f"   👤 ID: {hr_user_id}")
    print(f"   📛 Имя: {hr_name}")
    
    try:
        # Проверяем, существует ли уже пользователь
        cursor = db.conn.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (hr_user_id,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            # Обновляем существующего пользователя
            cursor.execute("""
                UPDATE users 
                SET fio = ?, department = ?, position = ?, is_hr = 1
                WHERE user_id = ?
            """, (hr_name, "HR Отдел", "HR Специалист", hr_user_id))
            print(f"✅ Существующий пользователь обновлен как HR")
        else:
            # Добавляем нового пользователя
            cursor.execute("""
                INSERT INTO users (user_id, fio, department, position, is_hr)
                VALUES (?, ?, ?, ?, 1)
            """, (hr_user_id, hr_name, "HR Отдел", "HR Специалист"))
            print(f"✅ Новый HR пользователь добавлен")
        
        db.conn.commit()
        
        # Проверяем результат
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (hr_user_id,))
        result = cursor.fetchone()
        
        if result:
            print(f"\n✅ Проверка успешна:")
            print(f"   👤 ID: {result['user_id']}")
            print(f"   📛 Имя: {result['fio']}")
            print(f"   🏢 Отдел: {result['department']}")
            print(f"   💼 Должность: {result['position']}")
            print(f"   👑 HR: {'Да' if result['is_hr'] else 'Нет'}")
        else:
            print(f"❌ Ошибка: пользователь не найден после добавления")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        db.conn.close()

if __name__ == "__main__":
    # Используем asyncio.run() правильно
    asyncio.run(fix_hr_user())