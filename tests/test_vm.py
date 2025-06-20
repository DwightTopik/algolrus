import sys
import os

# Настройка кодировки для Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from mel_parser import parse
from vm_core import *
from vm_codegen import *
from interpreter import interpret


def test_simple_vm_instructions():
    print("=== Тест базовых инструкций VM ===")

    try:

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
        print("Базовые инструкции работают")
        return True

    except Exception as e:
        print(f" Ошибка: {e}")
        return False


def test_vm_variables():
    print("\n=== Тест переменных VM ===")

    try:

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
        print("Переменные работают")
        return True

    except Exception as e:
        print(f" Ошибка: {e}")
        return False


def test_vm_conditionals():
    print("\n=== Тест условных переходов VM ===")

    try:

        instructions = [
            VMInstruction(OpCode.PUSH_INT, 5),
            VMInstruction(OpCode.PUSH_INT, 3),
            VMInstruction(OpCode.GT),
            VMInstruction(OpCode.JMP_IF_FALSE, 7),
            VMInstruction(OpCode.PUSH_STRING, "да"),
            VMInstruction(OpCode.PRINT),
            VMInstruction(OpCode.JMP, 9),
            VMInstruction(OpCode.PUSH_STRING, "нет"),
            VMInstruction(OpCode.PRINT),
            VMInstruction(OpCode.HALT)
        ]

        program = VMProgram(constants=[], code=instructions)

        vm = VirtualMachine()
        output = vm.run(program)

        expected = ["да\n"]
        assert output == expected, f"Ожидается {expected}, получено {output}"
        print("Условные переходы работают")
        return True

    except Exception as e:
        print(f" Ошибка: {e}")
        return False


def test_codegen_simple():
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


        program = compile_to_vm(ast)


        vm_output = run_vm_program(program)


        interpreter_output = interpret(ast)

        assert vm_output == interpreter_output, f"VM: {vm_output}, Interpreter: {interpreter_output}"
        print("Простая кодогенерация работает")
        return True

    except Exception as e:
        print(f" Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_codegen_arithmetic():
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


        program = compile_to_vm(ast)


        vm_output = run_vm_program(program)


        interpreter_output = interpret(ast)

        assert vm_output == interpreter_output, f"VM: {vm_output}, Interpreter: {interpreter_output}"
        print("Арифметика работает")
        return True

    except Exception as e:
        print(f" Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_codegen_conditionals():
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


        program = compile_to_vm(ast)


        vm_output = run_vm_program(program)


        interpreter_output = interpret(ast)

        assert vm_output == interpreter_output, f"VM: {vm_output}, Interpreter: {interpreter_output}"
        print("Условия работают")
        return True

    except Exception as e:
        print(f" Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_codegen_loops():
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


        program = compile_to_vm(ast)


        vm_output = run_vm_program(program)


        interpreter_output = interpret(ast)

        assert vm_output == interpreter_output, f"VM: {vm_output}, Interpreter: {interpreter_output}"
        print("Циклы работают")
        return True

    except Exception as e:
        print(f" Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_codegen_builtins():
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


        program = compile_to_vm(ast)


        vm_output = run_vm_program(program)


        interpreter_output = interpret(ast)

        assert vm_output == interpreter_output, f"VM: {vm_output}, Interpreter: {interpreter_output}"
        print("Встроенные функции работают")
        return True

    except Exception as e:
        print(f" Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_vm_program_serialization():
    print("\n=== Тест сериализации программ ===")

    try:

        instructions = [
            VMInstruction(OpCode.PUSH_INT, 42),
            VMInstruction(OpCode.PRINT),
            VMInstruction(OpCode.HALT)
        ]

        original_program = VMProgram(constants=["hello"], code=instructions, globals_count=1)


        data = original_program.to_dict()


        restored_program = VMProgram.from_dict(data)


        assert len(original_program.code) == len(restored_program.code)
        assert original_program.constants == restored_program.constants
        assert original_program.globals_count == restored_program.globals_count


        vm1 = VirtualMachine()
        output1 = vm1.run(original_program)

        vm2 = VirtualMachine()
        output2 = vm2.run(restored_program)

        assert output1 == output2

        print("Сериализация работает")
        return True

    except Exception as e:
        print(f" Ошибка: {e}")
        return False


def test_vm_tracing():
    print("\n=== Тест трассировки VM ===")

    try:

        instructions = [
            VMInstruction(OpCode.PUSH_INT, 5),
            VMInstruction(OpCode.PUSH_INT, 3),
            VMInstruction(OpCode.ADD),
            VMInstruction(OpCode.PRINT),
            VMInstruction(OpCode.HALT)
        ]

        program = VMProgram(constants=[], code=instructions)


        print("Трассировка выполнения:")
        vm = VirtualMachine(trace=True)
        output = vm.run(program)

        expected = ["8\n"]
        assert output == expected

        print("Трассировка работает")
        return True

    except Exception as e:
        print(f" Ошибка: {e}")
        return False


def run_all_tests():
    print(" Запуск тестов виртуальной машины...\n")

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

    print(f"\nРезультаты: {passed}/{total} тестов пройдено")

    if passed == total:
        print(" Все тесты VM прошли успешно!")
        return True
    else:
        print(" Некоторые тесты не прошли")
        return False


if __name__ == "__main__":
    run_all_tests()