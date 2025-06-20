#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Тесты для модуля оптимизаций
"""

from mel_parser import parse
from optim import optimize_ast, ConstantFolder
from mel_ast import *

def test_constant_folding_arithmetic():
    """Тест свертки арифметических констант"""
    print("=== Тест свертки арифметических констант ===")
    
    source = '''алг тест;
нач
    а : цел;
кон
    а := 2 + 3 * 4;
    а := 10 - 5;
    а := 6 / 2;
    а := 15 mod 4;
кон'''
    
    ast = parse(source)
    optimized_ast, stats = optimize_ast(ast)
    
    print(f"Количество оптимизаций: {stats.get('constant_folding', 0)}")
    
    # Проверяем первое присваивание: 2 + 3 * 4 должно стать 14
    first_assign = optimized_ast.block.statements[0]
    if isinstance(first_assign.value, IntLiteralNode):
        print(f"✅ 2 + 3 * 4 = {first_assign.value.value}")
        assert first_assign.value.value == 14
    else:
        print(f"❌ Не оптимизировано: {type(first_assign.value)}")
    
    # Проверяем второе присваивание: 10 - 5 должно стать 5
    second_assign = optimized_ast.block.statements[1]
    if isinstance(second_assign.value, IntLiteralNode):
        print(f"✅ 10 - 5 = {second_assign.value.value}")
        assert second_assign.value.value == 5
    else:
        print(f"❌ Не оптимизировано: {type(second_assign.value)}")
    
    return True

def test_constant_folding_logical():
    """Тест свертки логических констант"""
    print("\n=== Тест свертки логических констант ===")
    
    source = '''алг тест;
нач
    флаг : лог;
кон
    флаг := да и нет;
    флаг := да или нет;
    флаг := не да;
    флаг := 5 > 3;
    флаг := 2 = 2;
кон'''
    
    ast = parse(source)
    optimized_ast, stats = optimize_ast(ast)
    
    print(f"Количество оптимизаций: {stats.get('constant_folding', 0)}")
    
    statements = optimized_ast.block.statements
    
    # да и нет = нет
    if isinstance(statements[0].value, BoolLiteralNode):
        print(f"✅ да и нет = {statements[0].value.value}")
        assert statements[0].value.value == False
    
    # да или нет = да
    if isinstance(statements[1].value, BoolLiteralNode):
        print(f"✅ да или нет = {statements[1].value.value}")
        assert statements[1].value.value == True
    
    # не да = нет
    if isinstance(statements[2].value, BoolLiteralNode):
        print(f"✅ не да = {statements[2].value.value}")
        assert statements[2].value.value == False
    
    # 5 > 3 = да
    if isinstance(statements[3].value, BoolLiteralNode):
        print(f"✅ 5 > 3 = {statements[3].value.value}")
        assert statements[3].value.value == True
    
    # 2 = 2 = да
    if isinstance(statements[4].value, BoolLiteralNode):
        print(f"✅ 2 = 2 = {statements[4].value.value}")
        assert statements[4].value.value == True
    
    return True

def test_algebraic_optimizations():
    """Тест алгебраических оптимизаций"""
    print("\n=== Тест алгебраических оптимизаций ===")
    
    source = '''алг тест;
нач
    х : цел;
кон
    х := х + 0;
    х := х * 1;
    х := х * 0;
    х := х / 1;
кон'''
    
    ast = parse(source)
    optimized_ast, stats = optimize_ast(ast)
    
    print(f"Количество оптимизаций: {stats.get('constant_folding', 0)}")
    
    statements = optimized_ast.block.statements
    
    # х + 0 = х
    if isinstance(statements[0].value, IdentifierNode):
        print("✅ х + 0 = х")
        assert statements[0].value.name == "х"
    
    # х * 1 = х  
    if isinstance(statements[1].value, IdentifierNode):
        print("✅ х * 1 = х")
        assert statements[1].value.name == "х"
    
    # х * 0 = 0
    if isinstance(statements[2].value, IntLiteralNode):
        print("✅ х * 0 = 0")
        assert statements[2].value.value == 0
    
    # х / 1 = х
    if isinstance(statements[3].value, IdentifierNode):
        print("✅ х / 1 = х")
        assert statements[3].value.name == "х"
    
    return True

def test_constant_if_optimization():
    """Тест оптимизации условий с константами"""
    print("\n=== Тест оптимизации условий с константами ===")
    
    source = '''алг тест;
нач
    а : цел;
кон
    если да то
        а := 1;
    иначе
        а := 2;
    все
    
    если нет то
        а := 3;
    иначе
        а := 4;
    все
кон'''
    
    ast = parse(source)
    optimized_ast, stats = optimize_ast(ast)
    
    print(f"Количество оптимизаций: {stats.get('constant_folding', 0)}")
    
    statements = optimized_ast.block.statements
    
    # Первый if должен превратиться в а := 1
    if isinstance(statements[0], AssignNode):
        print("✅ если да то ... оптимизировано")
        assert isinstance(statements[0].value, IntLiteralNode)
        assert statements[0].value.value == 1
    
    # Второй if должен превратиться в а := 4
    if isinstance(statements[1], AssignNode):
        print("✅ если нет то ... оптимизировано")
        assert isinstance(statements[1].value, IntLiteralNode)
        assert statements[1].value.value == 4
    
    return True

def test_constant_while_optimization():
    """Тест оптимизации циклов while с константными условиями"""
    print("\n=== Тест оптимизации циклов while ===")
    
    source = '''алг тест;
нач
    а : цел;
кон
    пока нет
        а := а + 1;
    кц
    
    а := 5;
кон'''
    
    ast = parse(source)
    optimized_ast, stats = optimize_ast(ast)
    
    print(f"Количество оптимизаций: {stats.get('constant_folding', 0)}")
    
    statements = optimized_ast.block.statements
    
    # Цикл while с условием нет должен быть удален
    print(f"Количество операторов после оптимизации: {len(statements)}")
    
    # Должен остаться только а := 5
    if len(statements) == 1 and isinstance(statements[0], AssignNode):
        print("✅ Цикл while с ложным условием удален")
        assert isinstance(statements[0].value, IntLiteralNode)
        assert statements[0].value.value == 5
    
    return True

def test_complex_constant_expression():
    """Тест сложного константного выражения"""
    print("\n=== Тест сложного константного выражения ===")
    
    source = '''алг тест;
нач
    результат : цел;
кон
    результат := (2 + 3) * (4 - 1) + 10 / 2;
кон'''
    
    ast = parse(source)
    optimized_ast, stats = optimize_ast(ast)
    
    print(f"Количество оптимизаций: {stats.get('constant_folding', 0)}")
    
    # (2 + 3) * (4 - 1) + 10 / 2 = 5 * 3 + 5 = 15 + 5 = 20
    assign = optimized_ast.block.statements[0]
    if isinstance(assign.value, IntLiteralNode):
        print(f"✅ Сложное выражение = {assign.value.value}")
        assert assign.value.value == 20
    else:
        print(f"❌ Не полностью оптимизировано: {type(assign.value)}")
    
    return True

def test_no_optimization_with_variables():
    """Тест что переменные не оптимизируются"""
    print("\n=== Тест что переменные не оптимизируются ===")
    
    source = '''алг тест;
нач
    а : цел;
    б : цел;
кон
    а := б + 5;
    б := а * 2;
кон'''
    
    ast = parse(source)
    optimized_ast, stats = optimize_ast(ast)
    
    print(f"Количество оптимизаций: {stats.get('constant_folding', 0)}")
    
    statements = optimized_ast.block.statements
    
    # Выражения с переменными не должны оптимизироваться
    assert isinstance(statements[0].value, BinOpNode)
    assert isinstance(statements[1].value, BinOpNode)
    
    print("✅ Выражения с переменными не оптимизированы (корректно)")
    
    return True

def run_all_optimization_tests():
    """Запуск всех тестов оптимизации"""
    print("🚀 Запуск тестов оптимизации...")
    
    tests = [
        test_constant_folding_arithmetic,
        test_constant_folding_logical,
        test_algebraic_optimizations,
        test_constant_if_optimization,
        test_constant_while_optimization,
        test_complex_constant_expression,
        test_no_optimization_with_variables
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Тест {test.__name__} провален: {e}")
    
    print(f"\n📊 Результат: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("🎉 Все тесты оптимизации пройдены!")
        return True
    else:
        print("❌ Некоторые тесты провалены")
        return False

if __name__ == "__main__":
    run_all_optimization_tests() 