import os

print("📁 Проверка структуры проекта:")
print("=" * 50)

# Проверка файлов
files_to_check = [
    "bot.py",
    "config.py", 
    "database.py",
    "keyboards/reply.py",
]

for file in files_to_check:
    if os.path.exists(file):
        print(f"✅ {file}")
    else:
        print(f"❌ {file} - не найден")

print("\n📁 Проверка папки handlers:")
print("-" * 30)

if os.path.exists("handlers"):
    handler_files = os.listdir("handlers")
    for file in handler_files:
        if file.endswith(".py"):
            print(f"📄 handlers/{file}")
            
            # Проверяем содержимое файла
            try:
                with open(f"handlers/{file}", "r", encoding="utf-8") as f:
                    content = f.read()
                    if "router = Router()" in content:
                        print(f"  ✅ содержит 'router = Router()'")
                    else:
                        print(f"  ❌ НЕТ 'router = Router()'")
                    if "@router" in content:
                        print(f"  ✅ содержит декораторы '@router'")
                    else:
                        print(f"  ❌ НЕТ декораторов '@router'")
            except Exception as e:
                print(f"  ⚠️  ошибка чтения: {e}")
else:
    print("❌ Папка handlers не найдена!")

print("\n🔧 Рекомендации:")
print("1. В каждом файле в папке handlers должна быть строка: router = Router()")
print("2. Все хендлеры должны использовать декоратор @router.message")
print("3. В bot.py импорт должен быть: from handlers.файл import router")   