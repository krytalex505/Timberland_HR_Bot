# handlers/admin.py (полностью обновленный файл)
from aiogram import Router, types, F, Bot
from aiogram.filters import Command
from config import HR_CHAT_ID
from scheduler import check_and_send_forms
import logging
import sqlite3
from datetime import datetime, timedelta

router = Router()
logger = logging.getLogger(__name__)

@router.message(Command("admin"))
@router.message(F.text == "👨‍💼 Админ-панель")
async def admin_panel(message: types.Message):
    """Админ-панель"""
    user_id = message.from_user.id
    
    if str(user_id) != str(HR_CHAT_ID):
        await message.answer("⛔ Эта функция только для отдела персонала")
        return
    
    await message.answer(
        "👨‍💼 <b>Админ-панель отдела персонала</b>\n\n"
        "Доступные команды:\n"
        "• /stats - статистика\n"
        "• /users - список пользователей\n"
        "• /check_forms - проверить и отправить формы адаптации\n"
        "• /set_date [ID] [дней] - установить дату приема\n"
        "• /myid - показать ваш ID\n"
        "• /broadcast [текст] - рассылка всем пользователям",
        parse_mode="HTML"
    )

@router.message(Command("stats"))
async def show_stats(message: types.Message):
    """Показать статистику"""
    user_id = message.from_user.id
    
    if str(user_id) != str(HR_CHAT_ID):
        await message.answer("⛔ Эта команда только для отдела персонала")
        return
    
    try:
        conn = sqlite3.connect("bot_database.db")
        cursor = conn.cursor()
        
        # Статистика пользователей
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM users WHERE is_hr = 1")
        hr_users = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM users WHERE is_hr = 0")
        employee_users = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM users WHERE hire_date IS NOT NULL")
        users_with_date = cursor.fetchone()[0]
        
        # Статистика обращений
        cursor.execute("SELECT COUNT(*) FROM appeals")
        total_appeals = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM appeals WHERE status = 'pending'")
        pending_appeals = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM appeals WHERE status = 'in_progress'")
        in_progress_appeals = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM appeals WHERE status = 'completed'")
        completed_appeals = cursor.fetchone()[0]
        
        conn.close()
        
        await message.answer(
            f"📊 <b>Статистика бота</b>\n\n"
            f"👥 <b>Пользователи:</b>\n"
            f"• Всего: {total_users}\n"
            f"• HR: {hr_users}\n"
            f"• Сотрудники: {employee_users}\n"
            f"• С датой приема: {users_with_date}\n\n"
            f"📨 <b>Обращения:</b>\n"
            f"• Всего: {total_appeals}\n"
            f"• Ожидают: {pending_appeals}\n"
            f"• В работе: {in_progress_appeals}\n"
            f"• Завершены: {completed_appeals}",
            parse_mode="HTML"
        )
        
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")

@router.message(Command("users"))
async def show_users(message: types.Message):
    """Показать список пользователей"""
    user_id = message.from_user.id
    
    if str(user_id) != str(HR_CHAT_ID):
        await message.answer("⛔ Эта команда только для отдела персонала")
        return
    
    try:
        conn = sqlite3.connect("bot_database.db")
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT user_id, fio, hire_date, is_hr 
            FROM users 
            ORDER BY user_id
        """)
        
        users = cursor.fetchall()
        conn.close()
        
        if not users:
            await message.answer("❌ В базе данных нет пользователей")
            return
        
        text = "📋 <b>Список пользователей:</b>\n\n"
        
        for user in users[:50]:  # Ограничиваем первые 50
            user_id, fio, hire_date, is_hr = user
            hire_date_str = hire_date if hire_date else "нет даты"
            hr_status = "👨‍💼 HR" if is_hr == 1 else "👤"
            
            text += f"{hr_status} <b>ID:</b> <code>{user_id}</code>\n"
            text += f"<b>ФИО:</b> {fio}\n"
            text += f"<b>Дата приема:</b> {hire_date_str}\n\n"
        
        if len(users) > 50:
            text += f"\n... и еще {len(users) - 50} пользователей"
        
        await message.answer(text, parse_mode="HTML")
        
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")

@router.message(Command("check_forms"))
@router.message(F.text == "/check_forms")
async def check_forms_command(message: types.Message, bot: Bot):
    """Ручная проверка и отправка форм адаптации"""
    user_id = message.from_user.id
    
    # Проверяем, что это HR
    if str(user_id) != str(HR_CHAT_ID):
        await message.answer("⛔ Эта команда только для отдела персонала")
        return
    
    await message.answer("🔍 <b>Запускаю проверку пользователей для отправки форм адаптации...</b>", parse_mode="HTML")
    
    try:
        # Запускаем проверку
        await check_and_send_forms(bot)
        
        # После проверки показываем подробный отчет
        try:
            conn = sqlite3.connect("bot_database.db")
            cursor = conn.cursor()
            
            today = datetime.now().strftime("%Y-%m-%d")
            
            # Находим пользователей, у которых сегодня 10-й день
            cursor.execute("""
                SELECT user_id, fio, hire_date 
                FROM users 
                WHERE is_hr = 0 
                AND hire_date IS NOT NULL
                AND date(hire_date, '+10 days') = date(?)
            """, (today,))
            
            users_today = cursor.fetchall()
            conn.close()
            
            if users_today:
                text = f"✅ <b>Проверка завершена!</b>\n\n"
                text += f"📅 <b>Сегодня ({today}) 10-й день работы у:</b>\n\n"
                
                for user in users_today:
                    user_id, fio, hire_date = user
                    text += f"👤 <b>{fio}</b>\n"
                    text += f"   ID: <code>{user_id}</code>\n"
                    text += f"   Дата приема: {hire_date}\n\n"
                
                await message.answer(text, parse_mode="HTML")
            else:
                await message.answer(
                    f"✅ <b>Проверка завершена!</b>\n\n"
                    f"📅 Сегодня ({today}) нет пользователей, у которых 10-й день работы.\n\n"
                    f"Формы отправлены пользователям, у которых сегодня 10-й день.",
                    parse_mode="HTML"
                )
                
        except Exception as e:
            await message.answer(
                "✅ <b>Проверка завершена!</b>\n\n"
                "Формы отправлены пользователям, у которых сегодня 10-й день работы.",
                parse_mode="HTML"
            )
            
    except Exception as e:
        logger.error(f"Ошибка при ручной проверке форм: {e}")
        await message.answer(
            f"❌ <b>Ошибка при проверке:</b>\n{str(e)}",
            parse_mode="HTML"
        )

@router.message(Command("set_date"))
async def set_user_date(message: types.Message):
    """Установить дату приема пользователю (только для HR)"""
    user_id = message.from_user.id
    
    if str(user_id) != str(HR_CHAT_ID):
        await message.answer("⛔ Эта команда только для отдела персонала")
        return
    
    # Пример использования команды: /set_date 123456789 10
    args = message.text.split()
    
    if len(args) != 3:
        await message.answer(
            "📝 <b>Использование:</b>\n"
            "<code>/set_date [ID_пользователя] [дней_назад]</code>\n\n"
            "Пример: <code>/set_date 123456789 10</code>\n"
            "Установит дату приема 10 дней назад для пользователя 123456789",
            parse_mode="HTML"
        )
        return
    
    try:
        target_user_id = int(args[1])
        days_ago = int(args[2])
        
        # Обновляем дату в базе
        conn = sqlite3.connect("bot_database.db")
        cursor = conn.cursor()
        
        # Проверяем существование пользователя
        cursor.execute("SELECT fio FROM users WHERE user_id = ?", (target_user_id,))
        user = cursor.fetchone()
        
        if not user:
            await message.answer(f"❌ Пользователь с ID {target_user_id} не найден")
            conn.close()
            return
        
        # Устанавливаем новую дату
        new_date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
        
        cursor.execute(
            "UPDATE users SET hire_date = ? WHERE user_id = ?",
            (new_date, target_user_id)
        )
        
        conn.commit()
        conn.close()
        
        await message.answer(
            f"✅ <b>Дата приема обновлена!</b>\n\n"
            f"👤 Пользователь: {user[0]}\n"
            f"🆔 ID: <code>{target_user_id}</code>\n"
            f"📅 Новая дата приема: <code>{new_date}</code>\n"
            f"📆 Сегодня: {datetime.now().strftime('%Y-%m-%d')}\n"
            f"⏰ Форма будет отправлена через {days_ago} дней\n"
            f"🗓 Дата отправки: {(datetime.now() + timedelta(days=days_ago)).strftime('%Y-%m-%d')}",
            parse_mode="HTML"
        )
        
    except ValueError:
        await message.answer("❌ Неверный формат. ID и дни должны быть числами")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")

@router.message(Command("myid"))
async def get_my_id(message: types.Message):
    """Показать ID пользователя"""
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name or ""
    username = message.from_user.username or "нет username"
    
    await message.answer(
        f"👤 <b>Ваши данные:</b>\n\n"
        f"🆔 <b>ID:</b> <code>{user_id}</code>\n"
        f"👤 <b>Имя:</b> {first_name} {last_name}\n"
        f"📱 <b>Username:</b> @{username}\n\n"
        f"📋 <b>Копировать ID:</b> <code>{user_id}</code>",
        parse_mode="HTML"
    )