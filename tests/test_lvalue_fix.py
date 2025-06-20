#!/usr/bin/env python3

print("=== ТЕСТ ИСПРАВЛЕНИЯ LVALUE ===")

# Принудительно очищаем кэш
import sys
if 'mel_parser' in sys.modules:
    del sys.modules['mel_parser']

import mel_parser
mel_parser._parser = None

print("Тестируем простое присваивание...")
try:
    simple_code = '''алг тест;
нач
    а : цел;
кон
    а := 10;
кон'''
    
    ast = mel_parser.parse(simple_code)
    print("✅ Простое присваивание работает!")
    
    print("Тестируем функцию с присваиванием...")
    func_code = '''алг тест;
нач
    а : цел;
кон
функции
    функция тест() : цел;
    нач
        temp : цел;
    кон
        temp := 42;
        знач temp;
    кон
кон
    а := 10;
кон'''
    
    ast = mel_parser.parse(func_code)
    print("🎉 ФУНКЦИЯ С ПРИСВАИВАНИЕМ РАБОТАЕТ!")
    print(f"Функций: {len(ast.block.func_decls)}")
    print(f"Операторов в функции: {len(ast.block.func_decls[0].block.statements)}")
    
except Exception as e:
    print(f"❌ Ошибка: {e}")
    import traceback
    traceback.print_exc() 