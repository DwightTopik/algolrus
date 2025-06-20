import sys
import os

# Настройка кодировки для Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from mel_parser import parse
from vm_codegen import compile_to_vm
from optim import optimize_bytecode, PeepholeOptimizer
from vm_core import VMInstruction, OpCode

def test_peephole_arithmetic():
    print("=== Тест Peephole арифметических оптимизаций ===")

    source = '''алг тест;
нач
    а : цел;
кон
    а := 5 + 3;
    а := 10 * 2;
кон'''

    ast = parse(source)
    program = compile_to_vm(ast)

    print(f"Исходный размер байт-кода: {len(program.code)}")

    optimized_program, stats = optimize_bytecode(program)

    print(f"Оптимизированный размер: {len(optimized_program.code)}")
    print(f"Количество peephole оптимизаций: {stats.get('peephole', 0)}")


    assert stats.get('peephole', 0) > 0, "Должны быть применены peephole оптимизации"

    print(" Peephole оптимизации работают")
    return True

def test_algebraic_peephole():
    print("\n=== Тест алгебраических Peephole оптимизаций ===")

    source = '''алг тест;
нач
    х : цел;
кон
    х := х + 0;
    х := х * 1;
кон'''

    ast = parse(source)
    program = compile_to_vm(ast)

    original_size = len(program.code)
    print(f"Исходный размер байт-кода: {original_size}")

    optimized_program, stats = optimize_bytecode(program)

    optimized_size = len(optimized_program.code)
    print(f"Оптимизированный размер: {optimized_size}")
    print(f"Уменьшение: {original_size - optimized_size} инструкций")
    print(f"Количество оптимизаций: {stats.get('peephole', 0)}")


    assert optimized_size < original_size, "Размер байт-кода должен уменьшиться"

    print("Алгебраические peephole оптимизации работают")
    return True

def test_constant_folding_in_bytecode():
    print("\n=== Тест свертки констант в байт-коде ===")


    optimizer = PeepholeOptimizer()


    from vm_core import VMProgram, VMInstruction, OpCode

    instructions = [
        VMInstruction(OpCode.PUSH_INT, 2),
        VMInstruction(OpCode.PUSH_INT, 3),
        VMInstruction(OpCode.ADD),
        VMInstruction(OpCode.PUSH_INT, 5),
        VMInstruction(OpCode.PUSH_INT, 2),
        VMInstruction(OpCode.MUL),
    ]

    program = VMProgram(constants=[], code=instructions, globals_count=1)

    print(f"Исходные инструкции: {len(program.code)}")
    for i, instr in enumerate(program.code):
        print(f"  {i}: {instr}")

    optimized_program, stats = optimizer.optimize(program)

    print(f"\nОптимизированные инструкции: {len(optimized_program.code)}")
    for i, instr in enumerate(optimized_program.code):
        print(f"  {i}: {instr}")

    print(f"\nКоличество оптимизаций: {stats.get('peephole', 0)}")


    assert len(optimized_program.code) < len(program.code)

    print("Свертка констант в байт-коде работает")
    return True

def test_integration_optimization():
    print("\n=== Интеграционный тест оптимизаций ===")

    source = '''алг тест;
нач
    результат : цел;
кон
    результат := 2 + 3 * 4;
    результат := результат + 0;
    результат := результат * 1;
кон'''

    ast = parse(source)


    program_no_opt = compile_to_vm(ast)


    from optim import optimize_ast
    optimized_ast, ast_stats = optimize_ast(ast)
    program_ast_opt = compile_to_vm(optimized_ast)


    program_full_opt, peephole_stats = optimize_bytecode(program_ast_opt)

    print(f"Без оптимизаций: {len(program_no_opt.code)} инструкций")
    print(f"AST оптимизации: {len(program_ast_opt.code)} инструкций")
    print(f"Полные оптимизации: {len(program_full_opt.code)} инструкций")

    print(f"AST оптимизаций: {ast_stats.get('total', 0)}")
    print(f"Peephole оптимизаций: {peephole_stats.get('total', 0)}")


    assert len(program_full_opt.code) <= len(program_ast_opt.code)
    assert len(program_ast_opt.code) <= len(program_no_opt.code)

    print("Интеграция оптимизаций работает")
    return True

def test_cli_optimization():
    print("\n=== Тест CLI с оптимизациями ===")


    test_source = '''алг тест_оптимизации;
нач
    х : цел;
кон
    х := 2 + 3;
    х := х + 0;
    х := х * 1;
    вывод(х);
кон'''

    with open('temp_opt_test.alg', 'w', encoding='utf-8') as f:
        f.write(test_source)

    try:

        import subprocess
        import sys


        result1 = subprocess.run([
            sys.executable, 'main.py', 'compile', 'temp_opt_test.alg',
            '-o', 'temp_no_opt.avm'
        ], capture_output=True, text=True, encoding='utf-8')


        result2 = subprocess.run([
            sys.executable, 'main.py', 'compile', 'temp_opt_test.alg',
            '-o', 'temp_opt.avm', '-O', '-v'
        ], capture_output=True, text=True, encoding='utf-8')

        print("Компиляция без оптимизаций:")
        print(result1.stdout)

        print("Компиляция с оптимизациями:")
        print(result2.stdout)


        assert "AST оптимизаций" in result2.stdout or "Peephole оптимизации" in result2.stdout

        print("CLI оптимизации работают")

    finally:

        import os
        for file in ['temp_opt_test.alg', 'temp_no_opt.avm', 'temp_opt.avm']:
            try:
                os.remove(file)
            except FileNotFoundError:
                pass

    return True

def run_all_peephole_tests():
    print("Запуск тестов Peephole оптимизаций...")

    tests = [
        test_peephole_arithmetic,
        test_algebraic_peephole,
        test_constant_folding_in_bytecode,
        test_integration_optimization,
        test_cli_optimization
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"Тест {test.__name__} провален: {e}")
            import traceback
            traceback.print_exc()

    print(f"\nРезультат: {passed}/{total} тестов пройдено")

    if passed == total:
        print("Все тесты Peephole оптимизаций пройдены!")
        return True
    else:
        print("Некоторые тесты провалены")
        return False

if __name__ == "__main__":
    run_all_peephole_tests()