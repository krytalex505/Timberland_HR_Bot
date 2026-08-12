# test_final.py
import sqlite3

def test_db():
    conn = sqlite3.connect("bot_database.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("📊 ФИНАЛЬНАЯ ПРОВЕРКА БАЗЫ ДАННЫХ:")
    print("=" * 50)
    
    # 1. Все пользователи
    cursor.execute("SELECT * FROM users ORDER BY is_hr DESC")
    users = cursor.fetchall()
    
    print(f"\n👥 Всего пользователей: {len(users)}")
    for user in users:
        status = "👑 HR" if user['is_hr'] else "👤 Сотрудник"
        print(f"   {status}: {user['fio']} (ID: {user['user_id']})")
    
    # 2. HR пользователи
    cursor.execute("SELECT * FROM users WHERE is_hr = 1")
    hr_users = cursor.fetchall()
    
    print(f"\n👑 HR пользователи: {len(hr_users)}")
    for hr in hr_users:
        print(f"   ✅ {hr['fio']} (ID: {hr['user_id']})")
    
    # 3. Обращения
    cursor.execute("SELECT * FROM appeals")
    appeals = cursor.fetchall()
    
    print(f"\n📨 Всего обращений: {len(appeals)}")
    for appeal in appeals:
        print(f"   📝 #{appeal['id']}: {appeal['fio']} (Статус: {appeal['status']})")
    
    conn.close()

if __name__ == "__main__":
    test_db()