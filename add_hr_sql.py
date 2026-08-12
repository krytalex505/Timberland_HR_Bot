# add_hr_sql.py
import sqlite3

def add_hr_directly():
    """Добавить HR напрямую через SQL"""
    
    db_path = "bot_database.db"
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        hr_user_id = 749151832
        hr_name = "HR Специалист"
        
        print(f"📊 Текущая база данных: {db_path}")
        
        # Смотрим всех пользователей
        cursor.execute("SELECT * FROM users")
        all_users = cursor.fetchall()
        
        print(f"\n👥 Все пользователи в БД ({len(all_users)}):")
        for user in all_users:
            hr_status = "✅ HR" if user['is_hr'] else "👤 Обычный"
            print(f"   {hr_status} - {user['fio']} (ID: {user['user_id']})")
        
        # Проверяем, есть ли уже HR
        cursor.execute("SELECT * FROM users WHERE is_hr = 1")
        hr_users = cursor.fetchall()
        
        print(f"\n👑 Текущие HR пользователи ({len(hr_users)}):")
        for hr in hr_users:
            print(f"   👑 {hr['fio']} (ID: {hr['user_id']})")
        
        # Добавляем/обновляем HR
        cursor.execute("""
            INSERT OR REPLACE INTO users (user_id, fio, department, position, is_hr)
            VALUES (?, ?, ?, ?, 1)
        """, (hr_user_id, hr_name, "HR Отдел", "HR Специалист"))
        
        conn.commit()
        
        print(f"\n✅ HR пользователь добавлен/обновлен:")
        print(f"   👤 ID: {hr_user_id}")
        print(f"   📛 Имя: {hr_name}")
        
        # Проверяем результат
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (hr_user_id,))
        result = cursor.fetchone()
        
        if result:
            print(f"\n📋 Проверка записи:")
            print(f"   ID: {result['user_id']}")
            print(f"   Имя: {result['fio']}")
            print(f"   Отдел: {result['department']}")
            print(f"   Должность: {result['position']}")
            print(f"   HR статус: {'✅ Да' if result['is_hr'] else '❌ Нет'}")
        
        conn.close()
        print("\n✅ Готово! Перезапустите бота.")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    add_hr_directly()