from aiogram import Router, types, F, Bot
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from config import HR_CHAT_ID
from database import (
    get_user, create_appeal, get_appeal_by_user,
    complete_appeal, set_active_chat,
    get_active_chat, get_hr_for_employee, clear_active_chat,
    clear_active_chat_by_employee, get_hr_active_appeals, save_chat_message,
    get_chat_history, get_appeal, get_unread_appeals_count,
    get_all_active_appeals_with_names, update_appeal_status
)
from datetime import datetime
import logging
from keyboards.reply import main_menu, chat_menu  # Импортируем из нового файла

router = Router()
logger = logging.getLogger(__name__)

# ==================== КОНСТАНТЫ С ТЕКСТОМ ====================
GENERAL_TEXT = (
    "• <b>Общая информация о компании</b> "
    "<a href='https://drive.google.com/file/d/1iqQpSVc69tj_iIZmTd-TLnj5H1C8wKTO/view?pli=1'>открыть</a>\n"
    "• <b>Корпоративная культура</b> — "
    "<a href='https://drive.google.com/file/d/1DI-_qGjcmo7MySqwF9CAl51nf9SizXXj/view'>открыть</a>\n"
    "• <b>Оргструктура</b> — "
    "<a href='https://drive.google.com/file/d/1X5eEMUgcI24QYkUsZYVu44tg9u-VSIC6/view'>открыть</a>"
)

CONTACTS_TEXT = (
    "💬 <b>Полезные контакты для стажёров</b>\n\n"
    "📞 <b>Приёмная</b>\n"
    "50-76-26\n\n"
    "👩‍💼 <b>Отдел персонала</b>\n"
    "<b>Карелина Ольга Владимировна</b> — заместитель директора по персоналу\n"
    "📧 o.karelina@timbel.info\n"
    "📱 +375 29 315 01 68\n\n"
    "<b>Филипченко Наталья Александровна</b> — ведущий специалист по кадрам\n"
    "📧 n.filipchenko@timbel.info\n"
    "📱 +375 29 736 57 46\n\n"
    "💰 <b>Бухгалтерия</b>\n"
    "<b>Рубисова Светлана Владимировна</b> — заместитель главного бухгалтера\n"
    "📧 s.rubisova@timbel.info\n"
    "📱 +375 44 778 77 32\n\n"
    "💻 <b>IT-отдел</b>\n"
    "<b>Пыргарь Алексей Валерьевич</b> — системный администратор\n"
    "📧 a.pyrgar@timbel.info\n"
    "📱 +375 29 538 33 30\n\n"
    "🤝 <b>Профсоюзный комитет</b>\n"
    "<b>Кобзева Елена Николаевна</b> — председатель профкома\n"
    "📧 e.kobzeva@timbel.info\n"
    "📱 +375 44 508 81 03"
)

REGULATIONS_TEXT = (
    "📂 <b>Регламенты компании:</b>\n\n"
    "• <b>Кодекс корпоративной этики</b> — "
    "<a href='https://drive.google.com/file/d/1fr_SvXdF3KypvRNlD8b7BHVCGmU9eMrF/view?usp=sharing'>открыть</a>\n"
    "• <b>Правила внутреннего трудового распорядка</b> — "
    "<a href='https://drive.google.com/file/d/1jtUsvWQCgDDg8Pmq80mtwjmljpL7UJom/view'>открыть</a>"
)

# ==================== ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ СОСТОЯНИЙ ====================
hr_states = {}
active_hr_chats = {}

def get_hr_workspace_keyboard(appeal_id: int, employee_id: int):
    """Клавиатура рабочего пространства HR в чате (inline)"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="✅ Завершить диалог", callback_data="end_chat")
    builder.button(text="📋 История диалога", callback_data=f"history_{appeal_id}")
    builder.button(text="🔙 К списку обращений", callback_data="back_to_appeals")
    
    builder.button(text="⏳ Уточняю информацию", callback_data="quick_clarify")
    builder.button(text="✅ Вопрос решен", callback_data="quick_solved")
    
    builder.adjust(2, 1, 2)
    return builder.as_markup()

# ==================== ВАЖНО: ПЕРВЫЕ ОБРАБОТЧИКИ ДЛЯ ВСЕХ КНОПОК МЕНЮ ====================

# ==================== ОБРАБОТКА ВСЕХ КНОПОК СОТРУДНИКА ====================
@router.message(F.text == "❓ Задать вопрос в отдел персонала")
async def create_question(message: types.Message, bot: Bot):
    """Сотрудник создает новый вопрос"""
    user_id = message.from_user.id
    
    # Проверяем, не является ли это HR
    if str(user_id) == str(HR_CHAT_ID):
        await message.answer(
            "👨‍💼 <b>Вы в главном меню отдела персонала</b>",
            parse_mode="HTML",
            reply_markup=main_menu(is_hr=True)
        )
        return
    
    # Проверяем, есть ли уже активный вопрос у сотрудника
    existing_appeal = await get_appeal_by_user(user_id)
    if existing_appeal and existing_appeal['status'] == 'in_progress':
        await message.answer(
            f"⏳ <b>У вас уже есть активный вопрос #{existing_appeal['id']}</b>\n\n"
            f"Дождитесь ответа от отдела персонала.",
            parse_mode="HTML",
            reply_markup=chat_menu(is_hr=False)
        )
        return
    
    # Проверяем, есть ли вопрос в ожидании
    if existing_appeal and existing_appeal['status'] == 'pending':
        await message.answer(
            f"⏳ <b>Ваш вопрос #{existing_appeal['id']} уже в ожидании ответа</b>\n\n"
            f"Специалист скоро с вами свяжется.",
            parse_mode="HTML",
            reply_markup=main_menu(is_hr=False)
        )
        return
    
    # Создаем новое обращение
    appeal_id = await create_appeal(user_id, "Новый вопрос")
    
    if not appeal_id:
        await message.answer(
            "❌ <b>Ошибка создания вопроса</b>\n\n"
            "Попробуйте позже или обратитесь в отдел персонала по телефону.",
            parse_mode="HTML",
            reply_markup=main_menu(is_hr=False)
        )
        return
    
    # Получаем информацию о сотруднике
    user_info = await get_user(user_id)
    fio = user_info.get('fio', 'Сотрудник') if user_info else 'Сотрудник'
    
    # Уведомляем отдел персонала
    await bot.send_message(
        HR_CHAT_ID,
        f"🆕 <b>Новый вопрос от сотрудника!</b>\n\n"
        f"👤 <b>Сотрудник:</b> {fio}\n"
        f"📅 <b>Дата:</b> {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
        f"🔢 <b>Номер вопроса:</b> #{appeal_id}",
        parse_mode="HTML"
    )
    
    # Показываем сотруднику, что вопрос создан
    await message.answer(
        f"✅ <b>Ваш вопрос создан под номером #{appeal_id}</b>\n\n"
        f"Специалист отдела персонала скоро свяжется с вами.\n\n"
        f"<b>Теперь можете написать ваш вопрос текстом:</b>",
        parse_mode="HTML",
        reply_markup=chat_menu(is_hr=False)
    )

@router.message(F.text == "📜 История диалога")
async def show_employee_history(message: types.Message):
    """Показать историю диалога сотруднику"""
    user_id = message.from_user.id
    
    # Если это HR, показываем ему главное меню
    if str(user_id) == str(HR_CHAT_ID):
        await message.answer(
            "👨‍💼 <b>Вы в главном меню отдела персонала</b>",
            parse_mode="HTML",
            reply_markup=main_menu(is_hr=True)
        )
        return
    
    # Проверяем, есть ли активное обращение
    appeal = await get_appeal_by_user(user_id)
    
    if not appeal or appeal['status'] != 'in_progress':
        await message.answer(
            "❌ <b>У вас нет активного диалога</b>\n\n"
            "Сначала начните диалог с отделом персонала.",
            parse_mode="HTML",
            reply_markup=main_menu(is_hr=False)
        )
        return
    
    appeal_id = appeal['id']
    
    # Получаем историю диалога
    history = await get_chat_history(appeal_id, limit=20)
    
    if not history:
        await message.answer(
            "📭 <i>История диалога пуста.</i>",
            parse_mode="HTML",
            reply_markup=chat_menu(is_hr=False)
        )
        return
    
    text = "<b>📜 История диалога:</b>\n\n"
    for msg in history:
        sender = "👨‍💼 Специалист" if msg['is_hr'] else "👤 Вы"
        text += f"<b>{sender}:</b> {msg['message']}\n\n"
    
    await message.answer(
        text, 
        parse_mode="HTML",
        reply_markup=chat_menu(is_hr=False)
    )

@router.message(F.text == "✅ Завершить диалог")
async def end_chat_employee(message: types.Message, bot: Bot):
    """Сотрудник завершает диалог"""
    user_id = message.from_user.id
    
    # Если это HR, показываем ему главное меню
    if str(user_id) == str(HR_CHAT_ID):
        await message.answer(
            "👨‍💼 <b>Вы в главном меню отдела персонала</b>",
            parse_mode="HTML",
            reply_markup=main_menu(is_hr=True)
        )
        return
    
    # Проверяем, есть ли активное обращение
    appeal = await get_appeal_by_user(user_id)
    
    if not appeal or appeal['status'] != 'in_progress':
        await message.answer(
            "❌ <b>У вас нет активного диалога с отделом персонала</b>",
            parse_mode="HTML",
            reply_markup=main_menu(is_hr=False)
        )
        return
    
    appeal_id = appeal['id']
    hr_id = appeal.get('hr_id')
    
    # Завершаем обращение
    await complete_appeal(appeal_id)
    
    if hr_id:
        # Уведомляем HR
        user_info = await get_user(user_id)
        fio = user_info.get('fio', 'Сотрудник') if user_info else 'Сотрудник'
        
        try:
            await bot.send_message(
                hr_id,
                f"📌 <b>Сотрудник {fio} завершил диалог</b>\n\n"
                f"Вопрос: <b>#{appeal_id}</b>\n"
                f"Статус: <b>✅ ЗАВЕРШЕНО</b>",
                parse_mode="HTML"
            )
            
            # Очищаем активный чат HR
            if hr_id in active_hr_chats:
                del active_hr_chats[hr_id]
            if hr_id in hr_states:
                hr_states[hr_id] = "menu"
            await clear_active_chat(hr_id)
        except:
            pass
    
    # Очищаем активный чат сотрудника
    await clear_active_chat_by_employee(user_id)
    
    # Сообщаем сотруднику
    await message.answer(
        f"✅ <b>Диалог завершён</b>\n\n"
        f"Отдел персонала получил уведомление. Если у вас возникнут еще вопросы, задайте новый вопрос.",
        parse_mode="HTML",
        reply_markup=main_menu(is_hr=False)
    )

@router.message(F.text == "📋 В меню")
async def back_to_menu(message: types.Message):
    """Возврат в главное меню"""
    user_id = message.from_user.id
    
    is_hr = str(user_id) == str(HR_CHAT_ID)
    
    if is_hr and user_id in active_hr_chats:
        await message.answer(
            "⚠️ <b>У вас есть активный диалог!</b>\n\n"
            "Для возврата в меню сначала завершите текущий диалог.",
            parse_mode="HTML"
        )
        return
    
    if is_hr and user_id in active_hr_chats:
        del active_hr_chats[user_id]
    
    await message.answer(
        "Главное меню:",
        reply_markup=main_menu(is_hr=is_hr)
    )
# ==================== ПАМЯТКА С

@router.message(F.text == "ℹ️ О нас")
async def show_about_us(message: types.Message):
    """Показать информацию о компании"""
    user_id = message.from_user.id
    is_hr = str(user_id) == str(HR_CHAT_ID)
    
    await message.answer(
        GENERAL_TEXT,
        parse_mode="HTML",
        disable_web_page_preview=True,
        reply_markup=main_menu(is_hr=is_hr)
    )

@router.message(F.text == "📞 Полезные контакты")
async def show_useful_contacts(message: types.Message):
    """Показать полезные контакты"""
    user_id = message.from_user.id
    is_hr = str(user_id) == str(HR_CHAT_ID)
    
    await message.answer(
        CONTACTS_TEXT,
        parse_mode="HTML",
        disable_web_page_preview=True,
        reply_markup=main_menu(is_hr=is_hr)
    )
# ==================== ПАМЯТКА СОТРУДНИКА ====================
@router.message(F.text == "📋 Памятка сотрудника")
async def show_memo_pdf(message: types.Message, bot: Bot):
    """Отправить PDF-памятку сотруднику"""
    user_id = message.from_user.id
    is_hr = str(user_id) == str(HR_CHAT_ID)
    
    # Если это HR - не показываем
    if is_hr:
        await message.answer("⛔ Эта функция только для сотрудников")
        return
    
    # Путь к PDF-файлу
    file_path = "files/Памятка_сотрудника.pdf"
    
    # Проверяем, существует ли файл
    import os
    if not os.path.exists(file_path):
        await message.answer(
            "❌ <b>Файл памятки не найден</b>\n\n"
            "Обратитесь к администратору.",
            parse_mode="HTML"
        )
        return
    
    try:
        from aiogram.types import FSInputFile
        
        # Создаем объект файла
        document = FSInputFile(file_path)
        
        # Отправляем PDF
        await bot.send_document(
            chat_id=user_id,
            document=document,
            caption="📄 <b>Памятка сотрудника</b>\n\n"
                    "Сохраните файл для ознакомления.",
            parse_mode="HTML",
            reply_markup=main_menu(is_hr=is_hr)
        )
        
    except Exception as e:
        print(f"❌ Ошибка отправки PDF: {e}")
        await message.answer(
            "❌ <b>Ошибка отправки файла</b>\n\n"
            "Попробуйте позже.",
            parse_mode="HTML"
        )
@router.message(F.text == "📂 Регламенты компании")
async def show_regulations(message: types.Message):
    """Показать регламенты компании"""
    user_id = message.from_user.id
    is_hr = str(user_id) == str(HR_CHAT_ID)
    
    await message.answer(
        REGULATIONS_TEXT,
        parse_mode="HTML",
        disable_web_page_preview=True,
        reply_markup=main_menu(is_hr=is_hr)
    )

# ==================== ОБРАБОТКА КНОПОК HR ====================
@router.message(F.text == "📨 Обращения")
async def show_appeals_list(message: types.Message):
    """Показать список обращений"""
    hr_id = message.from_user.id
    
    if str(hr_id) != str(HR_CHAT_ID):
        await message.answer("⛔ Эта функция только для отдела персонала")
        return
    
    # Меняем состояние на "просмотр обращений"
    hr_states[hr_id] = "viewing_appeals"
    
    # Очищаем активный чат если был
    if hr_id in active_hr_chats:
        del active_hr_chats[hr_id]
    
    # Получаем все активные обращения
    appeals = await get_all_active_appeals_with_names()
    
    if not appeals:
        await message.answer(
            "📭 <b>Нет активных вопросов.</b>",
            parse_mode="HTML",
            reply_markup=main_menu(is_hr=True)
        )
        return
    
    builder = InlineKeyboardBuilder()
    text = "📨 <b>Активные вопросы:</b>\n\n"
    
    # Получаем обращения текущего HR
    hr_active_appeals = await get_hr_active_appeals(hr_id)
    if hr_active_appeals:
        text += f"🔔 <b>У вас в работе:</b> {len(hr_active_appeals)} вопрос(ов)\n\n"
    
    for appeal in appeals:
        user_name = appeal.get('user_name', appeal.get('fio', 'Без имени'))
        
        # Определяем статус
        if appeal['status'] == 'pending':
            status_icon = "🟢"
            status_text = "ожидает ответа"
            can_open = True
        else:  # in_progress
            if appeal.get('hr_id') == hr_id:
                status_icon = "💬"
                status_text = "ВАШ вопрос"
                can_open = True
            else:
                status_icon = "🔒"
                status_text = "занят другим специалистом"
                can_open = False
        
        text += f"{status_icon} <b>#{appeal['id']}</b> {user_name}\n"
        text += f"   └─ <i>{status_text}</i>\n\n"
        
        if can_open:
            if appeal['status'] == 'in_progress' and appeal.get('hr_id') == hr_id:
                emoji = "💬"
            elif appeal['status'] == 'pending':
                emoji = "🟢"
            else:
                emoji = "🟢"
            
            builder.button(
                text=f"{emoji} #{appeal['id']} {user_name[:15]}...",
                callback_data=f"appeal_{appeal['id']}"
            )
        else:
            builder.button(
                text=f"🔒 #{appeal['id']} {user_name[:15]}...",
                callback_data=f"locked_{appeal['id']}"
            )
    
    builder.button(text="🔄 Обновить", callback_data="refresh_appeals")
    builder.button(text="📋 В меню", callback_data="hr_menu")
    builder.adjust(1)
    
    await message.answer(
        text, 
        parse_mode="HTML", 
        reply_markup=builder.as_markup()
    )

@router.message(F.text == "🔙 К списку обращений")
async def back_to_appeals_from_chat_button(message: types.Message, bot: Bot):
    """Обработка кнопки возврата к списку обращений (только для HR)"""
    hr_id = message.from_user.id
    
    if str(hr_id) != str(HR_CHAT_ID):
        await message.answer("⛔ Эта функция только для отдела персонала")
        return
    
    if hr_id in active_hr_chats:
        employee_id, appeal_id = active_hr_chats[hr_id]
        
        # Возвращаем вопрос в ожидание
        await update_appeal_status(appeal_id, "pending", hr_id=None)
        
        # Уведомляем сотрудника
        try:
            await bot.send_message(
                employee_id,
                "⏸️ <b>Специалист отдела персонала приостановил диалог</b>\n\n"
                "Специалист вернется к вам позже.",
                parse_mode="HTML",
                reply_markup=main_menu(is_hr=False)
            )
        except:
            pass
        
        # Очищаем активный чат
        await clear_active_chat(hr_id)
        await clear_active_chat_by_employee(employee_id)
    
    # Меняем состояние
    hr_states[hr_id] = "viewing_appeals"
    if hr_id in active_hr_chats:
        del active_hr_chats[hr_id]
    
    # Показываем список обращений
    appeals = await get_all_active_appeals_with_names()
    
    if not appeals:
        await message.answer(
            "📭 <b>Нет активных вопросов.</b>",
            parse_mode="HTML",
            reply_markup=main_menu(is_hr=True)
        )
        return
    
    builder = InlineKeyboardBuilder()
    text = "📨 <b>Активные вопросы:</b>\n\n"
    
    hr_active_appeals = await get_hr_active_appeals(hr_id)
    if hr_active_appeals:
        text += f"🔔 <b>У вас в работе:</b> {len(hr_active_appeals)} вопрос(ов)\n\n"
    
    for appeal in appeals:
        user_name = appeal.get('user_name', 'Без имени')
        
        if appeal['status'] == 'pending':
            status_icon = "🟢"
            status_text = "ожидает ответа"
        else:
            if appeal.get('hr_id') == hr_id:
                status_icon = "💬"
                status_text = "ваш вопрос"
            else:
                status_icon = "🔒"
                status_text = "занят другим специалистом"
        
        text += f"{status_icon} <b>#{appeal['id']}</b> {user_name}\n"
        text += f"   └─ <i>{status_text}</i>\n\n"
        
        if appeal['status'] == 'pending' or (appeal['status'] == 'in_progress' and appeal.get('hr_id') == hr_id):
            builder.button(
                text=f"{status_icon} #{appeal['id']} {user_name[:15]}...",
                callback_data=f"appeal_{appeal['id']}"
            )
    
    builder.button(text="🔄 Обновить", callback_data="refresh_appeals")
    builder.button(text="📋 В меню", callback_data="hr_menu")
    builder.adjust(1)
    
    await message.answer(
        text, 
        parse_mode="HTML", 
        reply_markup=builder.as_markup()
    )

# ==================== ОБРАБОТКА СООБЩЕНИЙ СОТРУДНИКА ====================
@router.message(lambda message: str(message.from_user.id) != str(HR_CHAT_ID))
async def handle_employee_messages(message: types.Message, bot: Bot):
    """Обработчик сообщений от сотрудника (кроме кнопок меню)"""
    
    user_id = message.from_user.id
    # ... остальной код без изменений
    
    # Проверяем, есть ли у сотрудника активное обращение
    appeal = await get_appeal_by_user(user_id)
    
    if not appeal:
        # Если нет обращения, предлагаем создать вопрос
        await message.answer(
            "❌ <b>У вас нет активного вопроса</b>\n\n"
            "Чтобы задать вопрос отделу персонала, нажмите кнопку "
            "'❓ Задать вопрос в отдел персонала'.",
            parse_mode="HTML",
            reply_markup=main_menu(is_hr=False)
        )
        return
    
    appeal_id = appeal['id']
    
    if appeal['status'] == 'in_progress':
        # Если диалог активен, проверяем действительно ли HR в активном чате с этим сотрудником
        hr_id = appeal.get('hr_id')
        if hr_id:
            # КЛЮЧЕВАЯ ПРОВЕРКА: есть ли этот сотрудник в активных чатах HR?
            if hr_id in active_hr_chats:
                active_employee_id, active_appeal_id = active_hr_chats[hr_id]
                if active_appeal_id == appeal_id:
                    # ДА, это активный чат! Можно отправлять сообщение
                    try:
                        # Сохраняем сообщение в историю
                        await save_chat_message(appeal_id, user_id, message.text, is_hr=False)
                        
                        # Получаем информацию о сотруднике для форматирования
                        user_info = await get_user(user_id)
                        fio = user_info.get('fio', 'Сотрудник') if user_info else 'Сотрудник'
                        
                        # Отправляем сообщение HR
                        await bot.send_message(
                            hr_id,
                            f"👤 <b>{fio}:</b>\n{message.text}",
                            parse_mode="HTML"
                        )
                        
                    except Exception as e:
                        logger.error(f"Ошибка отправки сообщения HR: {e}")
                        await message.answer(
                            "❌ Не удалось отправить сообщение.",
                            reply_markup=chat_menu(is_hr=False)
                        )
                else:
                    # НЕТ, это не активный чат! Диалог приостановлен
                    await message.answer(
                        "⏸️ <b>Ваш диалог приостановлен</b>\n\n"
                        "Специалист в данный момент общается с другим сотрудником. "
                        "Ваше сообщение не будет отправлено.\n\n"
                        "Дождитесь, когда специалист вернется к вашему диалогу.",
                        parse_mode="HTML",
                        reply_markup=main_menu(is_hr=False)  # Возвращаем в главное меню!
                    )
            else:
                # HR нет в активных чатах - значит диалог не активен
                await message.answer(
                    "⏸️ <b>Диалог приостановлен</b>\n\n"
                    "Специалист в данный момент не ведет активный диалог. "
                    "Ваше сообщение не будет отправлено.",
                    parse_mode="HTML",
                    reply_markup=main_menu(is_hr=False)
                )
        else:
            # Нет HR_id - значит диалог не активен
            await message.answer(
                "⏳ Специалист еще не назначен. Ожидайте...",
                reply_markup=main_menu(is_hr=False)
            )
    
    elif appeal['status'] == 'pending':
        # Если вопрос в ожидании, сохраняем сообщение
        await save_chat_message(appeal_id, user_id, message.text, is_hr=False)
        
        await message.answer(
            f"💾 <b>Сообщение сохранено для вопроса #{appeal_id}</b>\n\n"
            f"Специалист отдела персонала получит его, как только возьмет ваш вопрос в работу.",
            parse_mode="HTML",
            reply_markup=main_menu(is_hr=False)
        )
    
    else:
        # Вопрос завершен
        await message.answer(
            f"❌ <b>Вопрос #{appeal_id} завершен</b>\n\n"
            f"Чтобы задать новый вопрос, нажмите '❓ Задать вопрос в отдел персонала'.",
            parse_mode="HTML",
            reply_markup=main_menu(is_hr=False)
        )


# ==================== ОБРАБОТКА СООБЩЕНИЙ HR (ВСЕ, ЧТО НЕ КНОПКИ) ====================
@router.message(lambda message: str(message.from_user.id) == str(HR_CHAT_ID))
async def handle_hr_messages(message: types.Message, bot: Bot):
    """Обработчик сообщений от отдела персонала (кроме кнопок меню)"""
    hr_id = message.from_user.id
    
    # ВСЕ КНОПКИ МЕНЮ УЖЕ ОБРАБОТАНЫ ВЫШЕ!
    # Этот обработчик срабатывает только для обычных текстовых сообщений
    
    # Проверяем состояние HR
    state = hr_states.get(hr_id, "menu")
    
    if state == "chat" and hr_id in active_hr_chats:
        # HR в активном чате - пересылаем сообщение сотруднику
        employee_id, appeal_id = active_hr_chats[hr_id]
        
        # ДОПОЛНИТЕЛЬНАЯ ПРОВЕРКА: убедимся, что это действительно текущий активный чат
        appeal = await get_appeal(appeal_id)
        if not appeal or appeal['status'] != 'in_progress' or appeal.get('hr_id') != hr_id:
            await message.answer("❌ <b>Диалог больше не активен</b>", parse_mode="HTML")
            hr_states[hr_id] = "menu"
            if hr_id in active_hr_chats:
                del active_hr_chats[hr_id]
            return
        
        try:
            # Получаем информацию о HR для форматирования
            hr_info = await get_user(hr_id)
            hr_name = hr_info.get('fio', 'Специалист') if hr_info else 'Специалист'
            
            # Сохраняем сообщение в историю
            await save_chat_message(appeal_id, hr_id, message.text, is_hr=True)
            
            # Отправляем сообщение сотруднику
            await bot.send_message(
                employee_id,
                f"👨‍💼 <b>{hr_name}:</b>\n{message.text}",
                parse_mode="HTML",
                reply_markup=chat_menu(is_hr=False)
            )
            
            # НЕ подтверждаем HR - тихо отправляем
            
        except Exception as e:
            logger.error(f"Ошибка отправки сообщения сотруднику: {e}")
            await message.answer(
                f"❌ Не удалось отправить сообщение: {str(e)}",
                parse_mode="HTML"
            )
    
    elif state == "viewing_appeals":
        # HR просматривает список
        await message.answer(
            "📋 <b>Вы просматриваете список вопросов</b>\n\n"
            "Выберите вопрос из списка выше или используйте кнопки для навигации.",
            parse_mode="HTML"
        )
    
    else:
        # HR в главном меню или неопределенном состоянии
        await message.answer(
            "👨‍💼 <b>Вы в главном меню отдела персонала</b>\n\n"
            "Используйте кнопки меню для навигации:\n"
            "• 📨 Обращения — список вопросов\n"
            "• 📞 Полезные контакты — контакты\n"
            "• ℹ️ О нас — информация о компании\n"
            "• 📋 Памятка сотрудника\n"
            "• 📂 Регламенты компании — документы",
            parse_mode="HTML",
            reply_markup=main_menu(is_hr=True)
        )
# ==================== ОБНОВЛЕНИЕ СПИСКА ====================
@router.callback_query(F.data == "refresh_appeals")
async def refresh_appeals_list(callback: types.CallbackQuery):
    """Обновить список обращений"""
    hr_id = callback.from_user.id
    
    if str(hr_id) != str(HR_CHAT_ID):
        await callback.answer("⛔ Эта функция только для отдела персонала")
        return
    
    # Проверяем, есть ли активный чат
    if hr_id in active_hr_chats:
        await callback.answer(
            "⚠️ У вас есть активный диалог! Завершите его сначала.",
            show_alert=True
        )
        return
    
    # Меняем состояние
    hr_states[hr_id] = "viewing_appeals"
    
    await callback.message.delete()
    
    # Показываем обновленный список
    appeals = await get_all_active_appeals_with_names()
    
    if not appeals:
        await callback.message.answer(
            "📭 <b>Нет активных вопросов.</b>",
            parse_mode="HTML",
            reply_markup=main_menu(is_hr=True)
        )
        return
    
    builder = InlineKeyboardBuilder()
    text = "📨 <b>Активные вопросы:</b>\n\n"
    
    hr_active_appeals = await get_hr_active_appeals(hr_id)
    if hr_active_appeals:
        text += f"🔔 <b>У вас в работе:</b> {len(hr_active_appeals)} вопрос(ов)\n\n"
    
    for appeal in appeals:
        user_name = appeal.get('user_name', appeal.get('fio', 'Без имени'))
        
        if appeal['status'] == 'pending':
            status_icon = "🟢"
            status_text = "ожидает ответа"
            can_open = True
        else:
            if appeal.get('hr_id') == hr_id:
                status_icon = "💬"
                status_text = "ВАШ вопрос"
                can_open = True
            else:
                status_icon = "🔒"
                status_text = "занят другим специалистом"
                can_open = False
        
        text += f"{status_icon} <b>#{appeal['id']}</b> {user_name}\n"
        text += f"   └─ <i>{status_text}</i>\n\n"
        
        if can_open:
            if appeal['status'] == 'in_progress' and appeal.get('hr_id') == hr_id:
                emoji = "💬"
            elif appeal['status'] == 'pending':
                emoji = "🟢"
            else:
                emoji = "🟢"
            
            builder.button(
                text=f"{emoji} #{appeal['id']} {user_name[:15]}...",
                callback_data=f"appeal_{appeal['id']}"
            )
        else:
            builder.button(
                text=f"🔒 #{appeal['id']} {user_name[:15]}...",
                callback_data=f"locked_{appeal['id']}"
            )
    
    builder.button(text="🔄 Обновить", callback_data="refresh_appeals")
    builder.button(text="📋 В меню", callback_data="hr_menu")
    builder.adjust(1)
    
    await callback.message.answer(
        text, 
        parse_mode="HTML", 
        reply_markup=builder.as_markup()
    )
    
    await callback.answer("✅ Список обновлен")

# ==================== ОТКРЫТИЕ ЧАТА С ОБРАЩЕНИЕМ ====================
@router.callback_query(F.data.startswith("appeal_"))
async def open_appeal_chat(callback: types.CallbackQuery, bot: Bot):
    """Открыть чат с обращением - ТОЛЬКО ЧЕРЕЗ ЭТУ ФУНКЦИЮ МОЖНО НАЧАТЬ ДИАЛОГ"""
    try:
        appeal_id = int(callback.data.split("_")[1])
        hr_id = callback.from_user.id
        
        if str(hr_id) != str(HR_CHAT_ID):
            await callback.answer("⛔ Эта функция только для отдела персонала")
            return
        
        # Получаем информацию об обращении
        appeal = await get_appeal(appeal_id)
        if not appeal:
            await callback.answer("❌ Вопрос не найден")
            return
        
        # Проверяем, не занят ли вопрос другим HR
        if appeal['status'] == 'in_progress' and appeal.get('hr_id') != hr_id:
            await callback.answer("⚠️ Этот вопрос уже обрабатывается другим специалистом")
            return
        
        employee = await get_user(appeal['user_id'])
        
        # ========== ВАЖНО: ПРОВЕРЯЕМ ЕСТЬ ЛИ У HR УЖЕ АКТИВНЫЙ ЧАТ ==========
        if hr_id in active_hr_chats:
            old_employee_id, old_appeal_id = active_hr_chats[hr_id]
            
            # Даже если это тот же самый сотрудник, всё равно нужно обработать
            if old_appeal_id != appeal_id:
                # Возвращаем старый вопрос в ожидание
                await update_appeal_status(old_appeal_id, "pending", hr_id=None)
                
                # Уведомляем старого сотрудника о приостановке
                try:
                    await bot.send_message(
                        old_employee_id,
                        "⏸️ <b>Специалист отдела персонала переключился на другой вопрос</b>\n\n"
                        "Ваш диалог приостановлен. Теперь вы не можете отправлять сообщения.",
                        parse_mode="HTML",
                        reply_markup=main_menu(is_hr=False)  # Возвращаем в главное меню!
                    )
                except:
                    pass
                
                # Очищаем активный чат старого сотрудника
                await clear_active_chat_by_employee(old_employee_id)
        
        # Обновляем статус и устанавливаем активный чат
        await update_appeal_status(appeal_id, "in_progress", hr_id=hr_id)
        await set_active_chat(hr_id, appeal['user_id'])
        
        # Сохраняем информацию о активном чате (ПЕРЕЗАПИСЫВАЕМ старый)
        active_hr_chats[hr_id] = (appeal['user_id'], appeal_id)
        hr_states[hr_id] = "chat"
        
        # Уведомляем сотрудника и МЕНЯЕМ ЕГО МЕНЮ НА ЧАТНОЕ
        hr_user = await get_user(hr_id)
        hr_name = hr_user.get('fio', 'Специалист') if hr_user else 'Специалист'
        
        await bot.send_message(
            appeal['user_id'],
            f"👨‍💼 <b>Специалист отдела персонала {hr_name} начал диалог с вами!</b>\n\n"
            f"Вопрос: <b>#{appeal_id}</b>\n"
            f"Теперь вы можете общаться в реальном времени.\n\n"
            f"Используйте меню ниже для управления диалогом.",
            parse_mode="HTML",
            reply_markup=chat_menu(is_hr=False)
        )
        
        # Получаем историю сообщений (включая те, что были в ожидании)
        messages = await get_chat_history(appeal_id)
        
        # Информация о сотруднике
        employee_info = ""
        if employee:
            employee_info = f"👤 <b>{employee['fio']}</b>\n"
            employee_info += f"🏢 <b>Подразделение:</b> {employee.get('department', 'Не указано')}\n"
            employee_info += f"💼 <b>Должность:</b> {employee.get('position', 'Не указана')}\n"
            if employee.get('hire_date'):
                try:
                    hire_date = datetime.strptime(employee['hire_date'], "%Y-%m-%d")
                    employee_info += f"📅 <b>Дата приёма:</b> {hire_date.strftime('%d.%m.%Y')}\n"
                except:
                    employee_info += f"📅 <b>Дата приёма:</b> {employee['hire_date']}\n"
        
        # Формируем рабочее пространство
        text = f"💬 <b>Чат вопроса #{appeal_id}</b>\n\n"
        text += employee_info
        text += "━━━━━━━━━━━━━━━━━━━━\n"
        
        if messages:
            text += "<b>📜 История диалога:</b>\n"
            for msg in messages[-5:]:
                sender = "👨‍💼 Вы" if msg.get('is_hr') else "👤 Сотрудник"
                text += f"<b>{sender}:</b> {msg.get('message', '')}\n\n"
        else:
            text += "📭 <i>Сообщений пока нет</i>\n\n"
        
        text += "━━━━━━━━━━━━━━━━━━━━\n"
        text += "<b>💬 Теперь все ваши сообщения будут отправляться сотруднику.</b>"
        
        # Удаляем старое сообщение
        await callback.message.delete()
        
        # Отправляем рабочее пространство
        await callback.message.answer(
            text,
            parse_mode="HTML",
            reply_markup=get_hr_workspace_keyboard(appeal_id, appeal['user_id'])
        )
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в open_appeal_chat: {e}")
        await callback.answer("❌ Ошибка открытия чата")

# ==================== ВОЗВРАТ К СПИСКУ ОБРАЩЕНИЙ ====================
@router.callback_query(F.data == "back_to_appeals")
async def back_to_appeals_from_chat(callback: types.CallbackQuery, bot: Bot):
    """Вернуться к списку обращений из чата"""
    hr_id = callback.from_user.id
    
    if hr_id in active_hr_chats:
        employee_id, appeal_id = active_hr_chats[hr_id]
        
        # Возвращаем вопрос в ожидание
        await update_appeal_status(appeal_id, "pending", hr_id=None)
        
        # Уведомляем сотрудника
        try:
            await bot.send_message(
                employee_id,
                "⏸️ <b>Специалист отдела персонала приостановил диалог</b>\n\n"
                "Специалист вернется к вам позже.\n\n"
                "Теперь вы не можете отправлять сообщения.",
                parse_mode="HTML",
                reply_markup=main_menu(is_hr=False)  # Возвращаем в главное меню!
            )
        except:
            pass
        
        # Очищаем активный чат
        await clear_active_chat(hr_id)
        await clear_active_chat_by_employee(employee_id)
    
    # Меняем состояние
    hr_states[hr_id] = "viewing_appeals"
    if hr_id in active_hr_chats:
        del active_hr_chats[hr_id]
    
    # Удаляем рабочее пространство
    await callback.message.delete()
    
    # Показываем список обращений
    appeals = await get_all_active_appeals_with_names()
    
    if not appeals:
        await callback.message.answer(
            "📭 <b>Нет активных вопросов.</b>",
            parse_mode="HTML",
            reply_markup=main_menu(is_hr=True)
        )
        return
    
    builder = InlineKeyboardBuilder()
    text = "📨 <b>Активные вопросы:</b>\n\n"
    
    hr_active_appeals = await get_hr_active_appeals(hr_id)
    if hr_active_appeals:
        text += f"🔔 <b>У вас в работе:</b> {len(hr_active_appeals)} вопрос(ов)\n\n"
    
    for appeal in appeals:
        user_name = appeal.get('user_name', 'Без имени')
        
        if appeal['status'] == 'pending':
            status_icon = "🟢"
            status_text = "ожидает ответа"
        else:
            if appeal.get('hr_id') == hr_id:
                status_icon = "💬"
                status_text = "ваш вопрос"
            else:
                status_icon = "🔒"
                status_text = "занят другим специалистом"
        
        text += f"{status_icon} <b>#{appeal['id']}</b> {user_name}\n"
        text += f"   └─ <i>{status_text}</i>\n\n"
        
        if appeal['status'] == 'pending' or (appeal['status'] == 'in_progress' and appeal.get('hr_id') == hr_id):
            builder.button(
                text=f"{status_icon} #{appeal['id']} {user_name[:15]}...",
                callback_data=f"appeal_{appeal['id']}"
            )
    
    builder.button(text="🔄 Обновить", callback_data="refresh_appeals")
    builder.button(text="📋 В меню", callback_data="hr_menu")
    builder.adjust(1)
    
    await callback.message.answer(
        text, 
        parse_mode="HTML", 
        reply_markup=builder.as_markup()
    )
    
    await callback.answer()

# ==================== ВОЗВРАТ В МЕНЮ ====================
@router.callback_query(F.data == "hr_menu")
async def hr_menu_callback(callback: types.CallbackQuery):
    """Вернуться в главное меню отдела персонала"""
    hr_id = callback.from_user.id
    
    if str(hr_id) != str(HR_CHAT_ID):
        await callback.answer("⛔ Эта функция только для отдела персонала")
        return
    
    # Проверяем, есть ли активный чат
    if hr_id in active_hr_chats:
        await callback.answer(
            "⚠️ У вас есть активный диалог! Завершите его сначала.",
            show_alert=True
        )
        return
    
    # Меняем состояние
    hr_states[hr_id] = "menu"
    
    await callback.message.delete()
    
    await callback.message.answer(
        "Главное меню:",
        reply_markup=main_menu(is_hr=True)
    )
    
    await callback.answer()

# ==================== ЗАВЕРШЕНИЕ ДИАЛОГА HR ====================
@router.callback_query(F.data == "end_chat")
async def end_chat_from_workspace(callback: types.CallbackQuery, bot: Bot):
    """Завершить диалог из рабочего пространства HR"""
    hr_id = callback.from_user.id
    
    if hr_id not in active_hr_chats:
        await callback.answer("❌ Нет активного диалога")
        return
    
    employee_id, appeal_id = active_hr_chats[hr_id]
    
    # Завершаем обращение
    await update_appeal_status(appeal_id, "completed", hr_id=None)  # Убираем hr_id!
    
    # Очищаем активные чаты
    await clear_active_chat(hr_id)
    await clear_active_chat_by_employee(employee_id)
    
    # Удаляем из состояний
    del active_hr_chats[hr_id]
    hr_states[hr_id] = "menu"
    
    # Уведомляем сотрудника и ВОЗВРАЩАЕМ ЕГО К ГЛАВНОМУ МЕНЮ
    hr_user = await get_user(hr_id)
    hr_name = hr_user.get('fio', 'Специалист') if hr_user else 'Специалист'
    
    try:
        await bot.send_message(
            employee_id,
            f"✅ <b>Диалог завершен специалистом отдела персонала ({hr_name})</b>\n\n"
            f"Вопрос: <b>#{appeal_id}</b>\n"
            f"Статус: <b>ЗАВЕРШЕНО</b>",
            parse_mode="HTML",
            reply_markup=main_menu(is_hr=False)
        )
    except Exception as e:
        logger.error(f"Ошибка уведомления сотрудника: {e}")
    
    # Удаляем рабочее пространство
    await callback.message.delete()
    
    # Показываем меню HR
    await callback.message.answer(
        "✅ <b>Диалог завершен!</b>\n\n"
        "Возвращаемся в главное меню.",
        parse_mode="HTML",
        reply_markup=main_menu(is_hr=True)
    )
    
    await callback.answer()

# ==================== ПОКАЗ ИСТОРИИ ДИАЛОГА ====================
@router.callback_query(F.data.startswith("history_"))
async def show_dialog_history(callback: types.CallbackQuery):
    """Показать историю диалога"""
    appeal_id = int(callback.data.split("_")[1])
    
    history = await get_chat_history(appeal_id, limit=20)
    
    if not history:
        await callback.answer("📭 История диалога пуста")
        return
    
    text = "<b>📜 Полная история диалога:</b>\n\n"
    for msg in history:
        sender = "👨‍💼 Вы" if msg['is_hr'] else "👤 Сотрудник"
        text += f"<b>{sender}:</b> {msg['message']}\n\n"
    
    await callback.message.answer(text, parse_mode="HTML")
    await callback.answer()

# ==================== ОБРАБОТКА БЫСТРЫХ ОТВЕТОВ ====================
@router.callback_query(F.data.startswith("quick_"))
async def handle_quick_reply(callback: types.CallbackQuery, bot: Bot):
    """Обработчик быстрых ответов"""
    hr_id = callback.from_user.id
    reply_type = callback.data.split("_")[1]
    
    if hr_id not in active_hr_chats:
        await callback.answer("❌ Нет активного диалога")
        return
    
    employee_id, appeal_id = active_hr_chats[hr_id]
    
    quick_responses = {
        "clarify": "⏳ Уточняю информацию по вашему вопросу. Вернусь с ответом в ближайшее время.",
        "solved": "✅ Ваш вопрос решен. Если будут дополнительные вопросы, обращайтесь!"
    }
    
    response = quick_responses.get(reply_type, "Спасибо за обращение!")
    
    try:
        hr_user = await get_user(hr_id)
        hr_name = hr_user.get('fio', 'Специалист') if hr_user else 'Специалист'
        
        await bot.send_message(
            employee_id,
            f"👨‍💼 <b>{hr_name}:</b>\n{response}",
            parse_mode="HTML"
        )
        
        await save_chat_message(appeal_id, hr_id, response, is_hr=True)
        
        await callback.answer()
        
    except Exception as e:
        await callback.answer(f"❌ Ошибка: {str(e)}")

# ==================== ЗАБЛОКИРОВАННЫЕ ОБРАЩЕНИЯ ====================
@router.callback_query(F.data.startswith("locked_"))
async def handle_locked_appeal(callback: types.CallbackQuery):
    """Обработка заблокированных обращений"""
    appeal_id = int(callback.data.split("_")[1])
    appeal = await get_appeal(appeal_id)
    
    if not appeal:
        await callback.answer("❌ Вопрос не найдено")
        return
    
    if appeal.get('hr_id'):
        hr_user = await get_user(appeal['hr_id'])
        hr_name = hr_user.get('fio', 'Специалист') if hr_user else 'Специалист'
        
        await callback.answer(f"⚠️ Этот вопрос уже обрабатывает {hr_name}")
    else:
        await callback.answer("⚠️ Этот вопрос временно недоступен")