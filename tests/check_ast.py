import sys
import os

# Настройка кодировки для Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from mel_parser import parse

try:
    # Проверяем существование файла и создаем если нужно
    example_file = 'examples/complete_test.alg'
    if not os.path.exists(example_file):
        print(f"Файл {example_file} не найден, создаем тестовый файл...")
        os.makedirs('examples', exist_ok=True)
        with open(example_file, 'w', encoding='utf-8') as f:
            f.write('''алг тест_проверки;
нач
    а : цел;
    б : цел;
    флаг : лог;
кон
    а := 10;
    б := а + 5;
    флаг := а > б;
    вывод("Тест завершен");
кон''')
    
    with open(example_file, 'r', encoding='utf-8') as f:
        source = f.read()
    
    print("Парсинг complete_test.alg...")
    ast = parse(source)
    
    print(f"AST создан: {type(ast)}")
    print(f"Имя программы: {ast.name}")
    print(f"Количество переменных: {len(ast.block.var_decls)}")
    print(f"Количество операторов: {len(ast.block.statements)}")
    
    print("\nПеременные:")
    for var in ast.block.var_decls[:5]:            
        print(f"  {var.name}: {var.var_type}")
        
    print("\nПервые 5 операторов:")
    for i, stmt in enumerate(ast.block.statements[:5]):
        print(f"  {i+1}. {type(stmt).__name__}")
        
    if len(ast.block.statements) > 5:
        print(f"\n... и ещё {len(ast.block.statements) - 5} операторов")
    print("✅ AST корректно построен!")
    
except Exception as e:
    print(f"❌ Ошибка: {e}")
    import traceback
    traceback.print_exc() 