from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_hr_main_menu():
    """Главное меню HR с инлайн-кнопками"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="📨 Обращения", callback_data="hr_appeals_list")
    builder.button(text="👥 Список сотрудников", callback_data="hr_employees_list")
    builder.button(text="📊 Статистика", callback_data="hr_statistics")
    builder.button(text="⚙️ Настройки", callback_data="hr_settings")
    
    builder.adjust(2, 2)  # 2 кнопки в ряду
    return builder.as_markup()