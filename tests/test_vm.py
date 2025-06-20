#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Тесты для виртуальной машины и кодогенератора
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

from mel_parser import parse
from vm_core import *
from vm_codegen import *
from interpreter import interpret


def test_simple_vm_instructions():
    """Тест базовых инструкций VM"""
    print("=== Тест базовых инструкций VM ===")
    
    try:
        # Создаем простую программу: PUSH 5, PUSH 3, ADD, PRINT, HALT
        instructions = [
            VMInstruction(OpCode.PUSH_INT, 5),
            VMInstruction(OpCode.PUSH_INT, 3),
            VMInstruction(OpCode.ADD),
            VMInstruction(OpCode.PRINT),
            VMInstruction(OpCode.HALT)
        ]
        
        program = VMProgram(constants=[], code=instructions)
        
        vm = VirtualMachine()
        output = vm.run(program)
        
        expected = ["8\n"]
        assert output == expected, f"Ожидается {expected}, получено {output}"
        print("✅ Базовые инструкции работают")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False


def test_vm_variables():
    """Тест работы с переменными"""
    print("\n=== Тест переменных VM ===")
    
    try:
        # Программа: глобальная переменная = 10, вывести её
        instructions = [
            VMInstruction(OpCode.PUSH_INT, 10),
            VMInstruction(OpCode.STORE_GLOBAL, 0),
            VMInstruction(OpCode.LOAD_GLOBAL, 0),
            VMInstruction(OpCode.PRINT),
            VMInstruction(OpCode.HALT)
        ]
        
        program = VMProgram(constants=[], code=instructions, globals_count=1)
        
        vm = VirtualMachine()
        output = vm.run(program)
        
        expected = ["10\n"]
        assert output == expected, f"Ожидается {expected}, получено {output}"
        print("✅ Переменные работают")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False


def test_vm_conditionals():
    """Тест условных переходов"""
    print("\n=== Тест условных переходов VM ===")
    
    try:
        # if (5 > 3) print("да"); else print("нет");
        instructions = [
            VMInstruction(OpCode.PUSH_INT, 5),      # 0
            VMInstruction(OpCode.PUSH_INT, 3),      # 1
            VMInstruction(OpCode.GT),               # 2
            VMInstruction(OpCode.JMP_IF_FALSE, 7),  # 3 -> jump to else
            VMInstruction(OpCode.PUSH_STRING, "да"), # 4
            VMInstruction(OpCode.PRINT),            # 5
            VMInstruction(OpCode.JMP, 9),           # 6 -> jump to end
            VMInstruction(OpCode.PUSH_STRING, "нет"), # 7 (else)
            VMInstruction(OpCode.PRINT),            # 8
            VMInstruction(OpCode.HALT)              # 9 (end)
        ]
        
        program = VMProgram(constants=[], code=instructions)
        
        vm = VirtualMachine()
        output = vm.run(program)
        
        expected = ["да\n"]
        assert output == expected, f"Ожидается {expected}, получено {output}"
        print("✅ Условные переходы работают")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False


def test_codegen_simple():
    """Тест простой кодогенерации"""
    print("\n=== Тест простой кодогенерации ===")
    
    source = '''алг тест;
нач
    а : цел;
кон
    а := 42;
    вывод(а);
кон'''
    
    try:
        ast = parse(source)
        
        # Генерируем байт-код
        program = compile_to_vm(ast)
        
        # Запускаем на VM
        vm_output = run_vm_program(program)
        
        # Сравниваем с интерпретатором
        interpreter_output = interpret(ast)
        
        assert vm_output == interpreter_output, f"VM: {vm_output}, Interpreter: {interpreter_output}"
        print("✅ Простая кодогенерация работает")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_codegen_arithmetic():
    """Тест кодогенерации арифметики"""
    print("\n=== Тест кодогенерации арифметики ===")
    
    source = '''алг арифметика;
нач
    а : цел;
    б : цел;
    в : цел;
кон
    а := 10;
    б := 5;
    в := а + б * 2;
    вывод(в);
кон'''
    
    try:
        ast = parse(source)
        
        # Генерируем байт-код
        program = compile_to_vm(ast)
        
        # Запускаем на VM
        vm_output = run_vm_program(program)
        
        # Сравниваем с интерпретатором
        interpreter_output = interpret(ast)
        
        assert vm_output == interpreter_output, f"VM: {vm_output}, Interpreter: {interpreter_output}"
        print("✅ Арифметика работает")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_codegen_conditionals():
    """Тест кодогенерации условий"""
    print("\n=== Тест кодогенерации условий ===")
    
    source = '''алг условия;
нач
    а : цел;
кон
    а := 10;
    если а > 5 то
        вывод("больше");
    иначе
        вывод("меньше");
    все
кон'''
    
    try:
        ast = parse(source)
        
        # Генерируем байт-код
        program = compile_to_vm(ast)
        
        # Запускаем на VM
        vm_output = run_vm_program(program)
        
        # Сравниваем с интерпретатором
        interpreter_output = interpret(ast)
        
        assert vm_output == interpreter_output, f"VM: {vm_output}, Interpreter: {interpreter_output}"
        print("✅ Условия работают")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_codegen_loops():
    """Тест кодогенерации циклов"""
    print("\n=== Тест кодогенерации циклов ===")
    
    source = '''алг циклы;
нач
    i : цел;
кон
    для i от 1 до 3
        вывод(i);
    кц
кон'''
    
    try:
        ast = parse(source)
        
        # Генерируем байт-код
        program = compile_to_vm(ast)
        
        # Запускаем на VM
        vm_output = run_vm_program(program)
        
        # Сравниваем с интерпретатором
        interpreter_output = interpret(ast)
        
        assert vm_output == interpreter_output, f"VM: {vm_output}, Interpreter: {interpreter_output}"
        print("✅ Циклы работают")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_codegen_builtins():
    """Тест кодогенерации встроенных функций"""
    print("\n=== Тест встроенных функций ===")
    
    source = '''алг встроенные;
нач
    а : цел;
кон
    а := 10;
    увел(а);
    вывод(а);
    умен(а);
    вывод(а);
    вывод(модуль(-5));
кон'''
    
    try:
        ast = parse(source)
        
        # Генерируем байт-код
        program = compile_to_vm(ast)
        
        # Запускаем на VM
        vm_output = run_vm_program(program)
        
        # Сравниваем с интерпретатором
        interpreter_output = interpret(ast)
        
        assert vm_output == interpreter_output, f"VM: {vm_output}, Interpreter: {interpreter_output}"
        print("✅ Встроенные функции работают")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_vm_program_serialization():
    """Тест сериализации программ VM"""
    print("\n=== Тест сериализации программ ===")
    
    try:
        # Создаем простую программу
        instructions = [
            VMInstruction(OpCode.PUSH_INT, 42),
            VMInstruction(OpCode.PRINT),
            VMInstruction(OpCode.HALT)
        ]
        
        original_program = VMProgram(constants=["hello"], code=instructions, globals_count=1)
        
        # Сериализуем в словарь
        data = original_program.to_dict()
        
        # Десериализуем обратно
        restored_program = VMProgram.from_dict(data)
        
        # Проверяем, что программы одинаковые
        assert len(original_program.code) == len(restored_program.code)
        assert original_program.constants == restored_program.constants
        assert original_program.globals_count == restored_program.globals_count
        
        # Проверяем, что обе программы работают одинаково
        vm1 = VirtualMachine()
        output1 = vm1.run(original_program)
        
        vm2 = VirtualMachine()
        output2 = vm2.run(restored_program)
        
        assert output1 == output2
        
        print("✅ Сериализация работает")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False


def test_vm_tracing():
    """Тест трассировки VM"""
    print("\n=== Тест трассировки VM ===")
    
    try:
        # Простая программа для трассировки
        instructions = [
            VMInstruction(OpCode.PUSH_INT, 5),
            VMInstruction(OpCode.PUSH_INT, 3),
            VMInstruction(OpCode.ADD),
            VMInstruction(OpCode.PRINT),
            VMInstruction(OpCode.HALT)
        ]
        
        program = VMProgram(constants=[], code=instructions)
        
        # Запускаем с трассировкой
        print("Трассировка выполнения:")
        vm = VirtualMachine(trace=True)
        output = vm.run(program)
        
        expected = ["8\n"]
        assert output == expected
        
        print("✅ Трассировка работает")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False


def run_all_tests():
    """Запуск всех тестов VM"""
    print("🚀 Запуск тестов виртуальной машины...\n")
    
    tests = [
        test_simple_vm_instructions,
        test_vm_variables,
        test_vm_conditionals,
        test_codegen_simple,
        test_codegen_arithmetic,
        test_codegen_conditionals,
        test_codegen_loops,
        test_codegen_builtins,
        test_vm_program_serialization,
        test_vm_tracing
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n📊 Результаты: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("🎉 Все тесты VM прошли успешно!")
        return True
    else:
        print("❌ Некоторые тесты не прошли")
        return False


if __name__ == "__main__":
    run_all_tests() 