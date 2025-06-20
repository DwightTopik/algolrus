import sys
import os

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import mel_parser
import importlib

print("Тест простых функций...")

# Очищаем кеш парсера
mel_parser._parser = None

# Перезагружаем модуль
importlib.reload(mel_parser)

try:
    test_file = 'examples/simple_function.alg'
    if not os.path.exists(test_file):
        print(f"Файл {test_file} не найден, создаем тестовую программу...")
        test_code = '''алг простая_функция;
нач
    а : цел;
кон
функции
    функция тест();
    кон
кон
    а := 10;
кон'''
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_code)
        print(f"Создан тестовый файл {test_file}")
    
    with open(test_file, 'r', encoding='utf-8') as f:
        source = f.read()
    
    print("Тестируем простую функцию:")
    print(source)
    print("\n" + "="*50 + "\n")
    
    ast = mel_parser.parse(source)
    print("УСПЕХ! Простая функция работает!")
    print(f"Количество функций: {len(ast.block.func_decls)}")
    print(f"Имя программы: {ast.name}")
    print("Тест простых функций завершен успешно")
    
except Exception as e:
    print(f"Ошибка: {e}")
    import traceback
    traceback.print_exc() 