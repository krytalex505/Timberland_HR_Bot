# scheduler.py
import asyncio
from datetime import datetime, timedelta
from aiogram import Bot
from database import get_all_users
import logging

logger = logging.getLogger(__name__)

# Текст сообщения с формой
ADAPTATION_FORM_TEXT = (
    "🗓 <b>Добрый день!</b> Вы уже несколько дней работаете в нашей компании. "
    "Нам важно, как проходит ваша адаптация.\n\n"
    "Пожалуйста, ответьте на 6 коротких вопросов. Это займет не больше 1–2 минут.\n\n"
    "👉 <a href='https://forms.gle/4cJ2Dmjqm4zntNjT8'>Пройти опрос об адаптации</a>"
)

async def send_adaptation_form(bot: Bot, user_id: int):
    """Отправить форму адаптации сотруднику"""
    try:
        await bot.send_message(
            user_id,
            ADAPTATION_FORM_TEXT,
            parse_mode="HTML",
            disable_web_page_preview=False
        )
        logger.info(f"✅ Форма адаптации отправлена пользователю {user_id}")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка отправки формы пользователю {user_id}: {e}")
        return False

async def check_and_send_forms(bot: Bot):
    """Проверить всех пользователей и отправить формы через 10 дней после приема"""
    try:
        users = await get_all_users()
        today = datetime.now().date()
        
        sent_count = 0
        error_count = 0
        
        logger.info(f"🔍 Проверяю {len(users)} пользователей для отправки форм адаптации...")
        
        for user in users:
            user_id = user['user_id']
            hire_date_str = user.get('hire_date')
            
            # Пропускаем HR (is_hr = 1) и пользователей без даты приема
            if user.get('is_hr') == 1 or not hire_date_str:
                continue
            
            try:
                # Парсим дату приема (ожидаем формат YYYY-MM-DD)
                hire_date = datetime.strptime(hire_date_str, "%Y-%m-%d").date()
                
                # Вычисляем разницу в днях
                days_diff = (today - hire_date).days
                
                logger.debug(f"👤 Пользователь {user['fio']} ({user_id}): hire_date={hire_date_str}, дней прошло={days_diff}")
                
                # Отправляем через 10 дней (ровно 10 дней с даты приема)
                if days_diff == 10:
                    logger.info(f"📨 Отправляю форму адаптации пользователю {user['fio']} ({user_id}) - 10-й день работы")
                    success = await send_adaptation_form(bot, user_id)
                    if success:
                        sent_count += 1
                    else:
                        error_count += 1
                        
            except ValueError as e:
                logger.error(f"❌ Ошибка парсинга даты для пользователя {user['fio']} ({user_id}): {hire_date_str} - {e}")
                continue
            except Exception as e:
                logger.error(f"❌ Ошибка обработки пользователя {user['fio']} ({user_id}): {e}")
                error_count += 1
                continue
        
        if sent_count > 0 or error_count > 0:
            logger.info(f"📊 Итог: отправлено форм: {sent_count}, ошибок: {error_count}")
        else:
            logger.info("📊 Сегодня нет пользователей для отправки формы (10-й день работы)")
            
    except Exception as e:
        logger.error(f"❌ Критическая ошибка в check_and_send_forms: {e}")

async def scheduler_task(bot: Bot):
    """Задача планировщика, которая запускается раз в день"""
    logger.info("⏰ Планировщик форм адаптации запущен")
    
    while True:
        try:
            # Ждем до 10 утра следующего дня (можно настроить любое время)
            now = datetime.now()
            
            # Определяем, когда запускать следующую проверку
            # Запускаем в 10:00 каждый день
            if now.hour >= 10:
                # Если уже после 10:00, ждем до 10:00 завтра
                next_run = (now + timedelta(days=1)).replace(hour=10, minute=0, second=0, microsecond=0)
            else:
                # Если до 10:00, ждем до 10:00 сегодня
                next_run = now.replace(hour=10, minute=0, second=0, microsecond=0)
            
            wait_seconds = (next_run - now).total_seconds()
            
            logger.info(f"⏳ Следующая проверка в {next_run.strftime('%d.%m.%Y %H:%M')} (через {wait_seconds:.0f} секунд)")
            await asyncio.sleep(wait_seconds)
            
            # Проверяем и отправляем формы
            logger.info("🔍 Запускаю ежедневную проверку пользователей...")
            await check_and_send_forms(bot)
            logger.info("✅ Ежедневная проверка завершена")
            
        except asyncio.CancelledError:
            logger.info("🛑 Планировщик остановлен")
            break
        except Exception as e:
            logger.error(f"❌ Ошибка в scheduler_task: {e}")
            # В случае ошибки ждем 1 час и пробуем снова
            await asyncio.sleep(3600)

async def start_scheduler(bot: Bot):
    """Запустить планировщик в отдельной задаче"""
    # Запускаем проверку сразу при старте (на всякий случай)
    logger.info("🚀 Запуск планировщика форм адаптации...")
    asyncio.create_task(scheduler_task(bot))