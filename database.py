import sqlite3
from datetime import datetime
from typing import List, Dict, Optional
import logging

DATABASE_PATH = "bot_database.db"

class Database:
    def __init__(self):
        self.conn = None
        self.init_db()
    
    def init_db(self):
        """Инициализация базы данных"""
        self.conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.create_tables()
    
    def create_tables(self):
        """Создание таблиц"""
        cursor = self.conn.cursor()
        
        # Таблица пользователей
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                fio TEXT NOT NULL,
                department TEXT DEFAULT 'Не указан',
                position TEXT DEFAULT 'Не указана',
                hire_date TEXT,
                is_hr BOOLEAN DEFAULT FALSE,
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Таблица обращений
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS appeals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                fio TEXT NOT NULL,
                department TEXT,
                position TEXT,
                hire_date TEXT,
                message TEXT DEFAULT '',
                status TEXT DEFAULT 'pending',
                hr_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        # Таблица активных чатов
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS active_chats (
                hr_id INTEGER,
                employee_id INTEGER PRIMARY KEY,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (hr_id) REFERENCES users(user_id),
                FOREIGN KEY (employee_id) REFERENCES users(user_id)
            )
        """)
        
        # Таблица сообщений
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                appeal_id INTEGER,
                sender_id INTEGER NOT NULL,
                message TEXT NOT NULL,
                is_hr BOOLEAN NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (appeal_id) REFERENCES appeals(id)
            )
        """)
        
        self.conn.commit()
    
    # --- Пользователи ---
    async def save_user(self, user_id: int, fio: str, department: str = "Не указан", 
                       position: str = "Не указана", hire_date: str = None, is_hr: bool = False):
        """Сохранение пользователя"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO users (user_id, fio, department, position, hire_date, is_hr)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, fio, department, position, hire_date, 1 if is_hr else 0))
        self.conn.commit()
    
    async def get_user(self, user_id: int) -> Optional[Dict]:
        """Получение пользователя"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None
    
    async def delete_user(self, user_id: int) -> bool:
        """Удаление пользователя"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
        self.conn.commit()
        return cursor.rowcount > 0
    
    async def get_all_users(self) -> List[Dict]:
        """Получить всех пользователей"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users ORDER BY fio")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    
    # --- Обращения ---
    async def create_appeal(self, user_id: int, fio: str, department: str = "Не указан", 
                           position: str = "Не указана", hire_date: str = None, message: str = "") -> int:
        """Создание нового обращения"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO appeals (user_id, fio, department, position, hire_date, message, status)
            VALUES (?, ?, ?, ?, ?, ?, 'pending')
        """, (user_id, fio, department, position, hire_date, message))
        self.conn.commit()
        return cursor.lastrowid
    
    async def get_appeal_by_user(self, user_id: int) -> Optional[Dict]:
        """Получение активного обращения пользователя"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM appeals 
            WHERE user_id = ? AND status IN ('pending', 'in_progress')
            ORDER BY created_at DESC
            LIMIT 1
        """, (user_id,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None
    
    async def get_appeal(self, appeal_id: int) -> Optional[Dict]:
        """Получение обращения по ID"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM appeals WHERE id = ?", (appeal_id,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None
    
    async def get_appeal_by_participants(self, hr_id: int, employee_id: int) -> Optional[Dict]:
        """Получить обращение по участникам (HR и сотрудник)"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM appeals 
            WHERE hr_id = ? AND user_id = ? AND status = 'in_progress'
            ORDER BY created_at DESC 
            LIMIT 1
        """, (hr_id, employee_id))
        result = cursor.fetchone()
        return dict(result) if result else None
    
    async def reset_appeal_hr(self, appeal_id: int):
        """Сбросить HR у обращения"""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE appeals 
            SET hr_id = NULL
            WHERE id = ?
        """, (appeal_id,))
        self.conn.commit()
    
    async def get_all_pending_appeals_with_names(self) -> List[Dict]:
        """Получить все ожидающие обращения с именами пользователей"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT a.*, u.fio as user_name 
            FROM appeals a 
            LEFT JOIN users u ON a.user_id = u.user_id 
            WHERE a.status = 'pending' 
            ORDER BY a.created_at
        """)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    
    async def get_all_active_appeals_with_names(self) -> List[Dict]:
        """Получить ВСЕ активные обращения (включая in_progress) с именами пользователей"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT a.*, u.fio as user_name 
            FROM appeals a 
            LEFT JOIN users u ON a.user_id = u.user_id 
            WHERE a.status IN ('pending', 'in_progress') 
            ORDER BY 
                CASE 
                    WHEN a.status = 'in_progress' THEN 1
                    WHEN a.status = 'pending' THEN 2
                END,
                a.created_at
        """)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    
    async def update_appeal_status(self, appeal_id: int, status: str, hr_id: int = None):
        """Обновить статус обращения"""
        cursor = self.conn.cursor()
        
        if hr_id is not None:
            if hr_id == 0:  # Специальное значение для сброса hr_id
                cursor.execute("""
                    UPDATE appeals 
                    SET status = ?, hr_id = NULL
                    WHERE id = ?
                """, (status, appeal_id))
            else:
                cursor.execute("""
                    UPDATE appeals 
                    SET status = ?, hr_id = ?
                    WHERE id = ?
                """, (status, hr_id, appeal_id))
        else:
            cursor.execute("""
                UPDATE appeals 
                SET status = ?
                WHERE id = ?
            """, (status, appeal_id))
        
        self.conn.commit()
    
    async def complete_appeal(self, appeal_id: int):
        """Завершение обращения"""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE appeals 
            SET status = 'completed', completed_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (appeal_id,))
        self.conn.commit()
    
    async def get_hr_active_appeals(self, hr_id: int) -> List[Dict]:
        """Получить все обращения, которые обрабатывает конкретный HR"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT a.*, u.fio as user_name 
            FROM appeals a 
            LEFT JOIN users u ON a.user_id = u.user_id 
            WHERE a.status = 'in_progress' AND a.hr_id = ?
            ORDER BY a.created_at
        """, (hr_id,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    
    async def get_appeal_stats(self) -> Dict:
        """Получить статистику обращений"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
                SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as in_progress,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed
            FROM appeals
        """)
        
        stats = cursor.fetchone()
        return dict(stats) if stats else {
            'total': 0, 'pending': 0, 'in_progress': 0, 'completed': 0
        }
    
    # --- Активные чаты ---
    async def set_active_chat(self, hr_id: int, employee_id: int):
        """Установка активного чата"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO active_chats (hr_id, employee_id)
            VALUES (?, ?)
        """, (hr_id, employee_id))
        self.conn.commit()
    
    async def get_active_chat(self, hr_id: int) -> Optional[int]:
        """Получение активного чата для HR"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT employee_id FROM active_chats WHERE hr_id = ?", (hr_id,))
        row = cursor.fetchone()
        return row[0] if row else None
    
    async def get_hr_for_employee(self, employee_id: int) -> Optional[int]:
        """Получение HR для активного чата сотрудника"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT hr_id FROM active_chats WHERE employee_id = ?", (employee_id,))
        row = cursor.fetchone()
        return row[0] if row else None
    
    async def get_hr_id_for_employee_from_appeal(self, employee_id: int) -> Optional[int]:
        """Получить ID HR из активного обращения сотрудника"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT hr_id FROM appeals 
            WHERE user_id = ? AND status = 'in_progress'
            ORDER BY created_at DESC 
            LIMIT 1
        """, (employee_id,))
        result = cursor.fetchone()
        return result['hr_id'] if result else None
    
    async def clear_active_chat(self, hr_id: int):
        """Очистка активного чата"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM active_chats WHERE hr_id = ?", (hr_id,))
        self.conn.commit()
    
    async def clear_active_chat_by_employee(self, employee_id: int):
        """Очистка активного чата по сотруднику"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM active_chats WHERE employee_id = ?", (employee_id,))
        self.conn.commit()
    
    # --- Сообщения чата ---
    async def save_chat_message(self, appeal_id: int, sender_id: int, message: str, is_hr: bool):
        """Сохранение сообщения чата"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO chat_messages (appeal_id, sender_id, message, is_hr)
            VALUES (?, ?, ?, ?)
        """, (appeal_id, sender_id, message, 1 if is_hr else 0))
        self.conn.commit()
    
    async def get_chat_history(self, appeal_id: int, limit: int = 50) -> List[Dict]:
        """Получение истории чата"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM chat_messages 
            WHERE appeal_id = ?
            ORDER BY timestamp
            LIMIT ?
        """, (appeal_id, limit))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    
    async def get_appeal_messages(self, appeal_id: int, limit: int = 50) -> List[Dict]:
        """Алиас для get_chat_history (для обратной совместимости)"""
        return await self.get_chat_history(appeal_id, limit)
    
    # --- Статистика ---
    async def get_unread_appeals_count(self) -> int:
        """Количество непрочитанных обращений"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM appeals WHERE status = 'pending'")
        row = cursor.fetchone()
        return row[0] if row else 0
    
    async def get_user_count(self) -> int:
        """Количество пользователей"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        row = cursor.fetchone()
        return row[0] if row else 0
    
    async def get_appeals_today(self) -> int:
        """Количество обращений за сегодня"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM appeals 
            WHERE DATE(created_at) = DATE('now')
        """)
        row = cursor.fetchone()
        return row[0] if row else 0
    
    async def close(self):
        """Закрытие соединения с базой данных"""
        if self.conn:
            self.conn.close()

# Создаем глобальный экземпляр
db = Database()

# Функции для импорта
async def init_db():
    return db

async def save_user(*args, **kwargs):
    return await db.save_user(*args, **kwargs)

async def get_user(*args, **kwargs):
    return await db.get_user(*args, **kwargs)

async def delete_user(*args, **kwargs):
    return await db.delete_user(*args, **kwargs)

async def get_all_users(*args, **kwargs):
    return await db.get_all_users(*args, **kwargs)

async def create_appeal(*args, **kwargs):
    return await db.create_appeal(*args, **kwargs)

async def get_appeal_by_user(*args, **kwargs):
    return await db.get_appeal_by_user(*args, **kwargs)

async def get_appeal(*args, **kwargs):
    return await db.get_appeal(*args, **kwargs)

async def get_appeal_by_participants(*args, **kwargs):
    return await db.get_appeal_by_participants(*args, **kwargs)

async def reset_appeal_hr(*args, **kwargs):
    return await db.reset_appeal_hr(*args, **kwargs)

async def get_all_pending_appeals_with_names(*args, **kwargs):
    return await db.get_all_pending_appeals_with_names(*args, **kwargs)

async def get_all_active_appeals_with_names(*args, **kwargs):
    return await db.get_all_active_appeals_with_names(*args, **kwargs)

async def update_appeal_status(*args, **kwargs):
    return await db.update_appeal_status(*args, **kwargs)

async def complete_appeal(*args, **kwargs):
    return await db.complete_appeal(*args, **kwargs)

async def get_hr_active_appeals(*args, **kwargs):
    return await db.get_hr_active_appeals(*args, **kwargs)

async def get_appeal_stats(*args, **kwargs):
    return await db.get_appeal_stats(*args, **kwargs)

async def set_active_chat(*args, **kwargs):
    return await db.set_active_chat(*args, **kwargs)

async def get_active_chat(*args, **kwargs):
    return await db.get_active_chat(*args, **kwargs)

async def get_hr_for_employee(*args, **kwargs):
    return await db.get_hr_for_employee(*args, **kwargs)

async def get_hr_id_for_employee_from_appeal(*args, **kwargs):
    return await db.get_hr_id_for_employee_from_appeal(*args, **kwargs)

async def clear_active_chat(*args, **kwargs):
    return await db.clear_active_chat(*args, **kwargs)

async def clear_active_chat_by_employee(*args, **kwargs):
    return await db.clear_active_chat_by_employee(*args, **kwargs)

async def save_chat_message(*args, **kwargs):
    return await db.save_chat_message(*args, **kwargs)

async def get_chat_history(*args, **kwargs):
    return await db.get_chat_history(*args, **kwargs)

async def get_appeal_messages(*args, **kwargs):
    return await db.get_appeal_messages(*args, **kwargs)

async def get_unread_appeals_count(*args, **kwargs):
    return await db.get_unread_appeals_count(*args, **kwargs)

async def get_user_count(*args, **kwargs):
    return await db.get_user_count(*args, **kwargs)

async def get_appeals_today(*args, **kwargs):
    return await db.get_appeals_today(*args, **kwargs)

async def close_db(*args, **kwargs):
    return await db.close(*args, **kwargs)

# Экспортируем все функции
__all__ = [
    'init_db',
    'save_user',
    'get_user',
    'delete_user',
    'get_all_users',
    'create_appeal',
    'get_appeal_by_user',
    'get_appeal',
    'get_appeal_by_participants',
    'reset_appeal_hr',
    'get_all_pending_appeals_with_names',
    'get_all_active_appeals_with_names',
    'update_appeal_status',
    'complete_appeal',
    'get_hr_active_appeals',
    'get_appeal_stats',
    'set_active_chat',
    'get_active_chat',
    'get_hr_for_employee',
    'get_hr_id_for_employee_from_appeal',
    'clear_active_chat',
    'clear_active_chat_by_employee',
    'save_chat_message',
    'get_chat_history',
    'get_appeal_messages',
    'get_unread_appeals_count',
    'get_user_count',
    'get_appeals_today',
    'close_db'
]   