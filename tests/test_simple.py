import sys
import os

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

print("Тест 1: Простой print")

try:
    print("Тест 2: Импорт json")
    import json
    print("JSON импортирован успешно")
    
    print("Тест 3: Чтение файла")
    test_file = "hello.avm"
    if not os.path.exists(test_file):
        print(f"Файл {test_file} не найден, создаем тестовые данные...")
        test_data = {"constants": [], "code": [], "globals_count": 0}
        with open(test_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, ensure_ascii=False, indent=2)
        print(f"Создан тестовый файл {test_file}")
    
    with open(test_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print("Файл прочитан успешно")
    print(f"Размер данных: {len(str(data))}")
    
    print("Тест простых импортов...")
    from mel_parser import parse
    from mel_ast import ProgramNode
    print("Основные модули импортированы успешно")
    
except Exception as e:
    print(f"Ошибка: {e}")
    import traceback
    traceback.print_exc()

print("Тест завершен") 