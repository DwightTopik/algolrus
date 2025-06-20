print("Тест 1: Простой print")

try:
    print("Тест 2: Импорт json")
    import json
    print("JSON импортирован успешно")
    
    print("Тест 3: Чтение файла")
    with open("hello.avm", 'r', encoding='utf-8') as f:
        data = json.load(f)
    print("Файл прочитан успешно")
    print(f"Размер данных: {len(str(data))}")
    
except Exception as e:
    print(f"Ошибка: {e}")
    import traceback
    traceback.print_exc()

print("Тест завершен") 