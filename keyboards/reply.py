from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def main_menu(is_hr: bool = False) -> ReplyKeyboardMarkup:
    """Главное меню - единое для всех"""
    if is_hr:
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="ℹ️ О нас")],
                [KeyboardButton(text="📂 Регламенты компании")],
                [KeyboardButton(text="📞 Полезные контакты")],
                [KeyboardButton(text="📨 Обращения")]
            ],
            resize_keyboard=True,
            input_field_placeholder="Выберите опцию..."
        )
    else:
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="ℹ️ О нас")],
                [KeyboardButton(text="📂 Регламенты компании")],
                [KeyboardButton(text="📋 Памятка сотрудника")],
                [KeyboardButton(text="📞 Полезные контакты")],
                [KeyboardButton(text="❓ Задать вопрос в отдел персонала")]
                
                
            ],
            resize_keyboard=True,
            input_field_placeholder="Выберите опцию..."
        )
    return keyboard

def chat_menu(is_hr: bool = False) -> ReplyKeyboardMarkup:
    """Меню во время чата"""
    if is_hr:
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text="📜 История диалога"),
                    KeyboardButton(text="✅ Завершить диалог")
                ],
                [
                    KeyboardButton(text="🔙 К списку обращений"),
                    KeyboardButton(text="📋 В меню")
                ]
            ],
            resize_keyboard=True
        )
    else:
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text="📜 История диалога"),
                    KeyboardButton(text="✅ Завершить диалог")
                ],
                [
                    KeyboardButton(text="📋 В меню")
                ]
            ],
            resize_keyboard=True
        )
    return keyboard