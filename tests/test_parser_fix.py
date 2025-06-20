#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Принудительно сбрасываем кэш
import sys
if 'mel_parser' in sys.modules:
    del sys.modules['mel_parser']

import mel_parser
mel_parser._parser = None

from mel_parser import parse

def test_simple_assignment():
    """Тест простого присваивания"""
    print("=== Тест простого присваивания ===")
    
    source = '''алг тест;
нач
    а : цел;
кон
    а := 42;
кон'''
    
    try:
        ast = parse(source)
        print(f"AST: {type(ast)}")
        
        stmt = ast.block.statements[0]
        print(f"Оператор: {type(stmt)}")
        print(f"Цель: {type(stmt.target)}")
        print(f"Значение: {type(stmt.value)}")
        
        if hasattr(stmt.value, 'value'):
            print(f"Значение литерала: {stmt.value.value}")
        
        return True
        
    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_expression():
    """Тест выражения"""
    print("\n=== Тест выражения ===")
    
    source = '''алг тест;
нач
    а : цел;
    б : цел;
кон
    а := б + 5;
кон'''
    
    try:
        ast = parse(source)
        stmt = ast.block.statements[0]
        
        print(f"Значение: {type(stmt.value)}")
        
        if hasattr(stmt.value, 'left'):
            print(f"Левая часть: {type(stmt.value.left)}")
            print(f"Правая часть: {type(stmt.value.right)}")
            print(f"Оператор: {stmt.value.op}")
        
        return True
        
    except Exception as e:
        print(f"Ошибка: {e}")
        return False

if __name__ == "__main__":
    print("Тестирование исправленного парсера...")
    
    test1 = test_simple_assignment()
    test2 = test_expression()
    
    if test1 and test2:
        print("\n✅ Парсер работает корректно")
    else:
        print("\n❌ Проблемы с парсером") 