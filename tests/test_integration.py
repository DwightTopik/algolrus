



import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import sys
sys.stdout.reconfigure(encoding='utf-8')

from pathlib import Path
from mel_parser import parse
from interpreter import interpret
from vm_codegen import compile_to_vm
from vm_core import run_vm_program


def test_file_comparison(file_path: str) -> bool:
    print(f"=== Тестирование {file_path} ===")

    try:

        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()


        ast = parse(source)


        interpreter_output = interpret(ast)


        program = compile_to_vm(ast)
        vm_output = run_vm_program(program)


        if interpreter_output == vm_output:
            print(f" {file_path}: результаты совпадают")
            return True
        else:
            print(f" {file_path}: результаты различаются")
            print(f"  Интерпретатор: {interpreter_output}")
            print(f"  VM: {vm_output}")
            return False

    except Exception as e:
        print(f" {file_path}: ошибка - {e}")
        return False


def test_all_examples():
    print(" Интеграционное тестирование всех примеров...\n")

    examples_dir = Path("examples")
    if not examples_dir.exists():
        print(" Папка examples не найдена")
        return False


    alg_files = list(examples_dir.glob("*.alg"))

    if not alg_files:
        print(" Файлы .alg не найдены в папке examples")
        return False

    passed = 0
    total = len(alg_files)

    for file_path in sorted(alg_files):
        if test_file_comparison(str(file_path)):
            passed += 1
        print()

    print(f"Результаты: {passed}/{total} файлов прошли тестирование")

    if passed == total:
        print(" Все интеграционные тесты прошли успешно!")
        return True
    else:
        print(" Некоторые тесты не прошли")
        return False


def test_specific_cases():
    print("🔍 Тестирование специфических случаев...\n")

    test_cases = [
        {
            "name": "Факториал",
            "code": '''алг факториал;
нач
    н : цел;
    рез : цел;
    i : цел;
кон
    н := 5;
    рез := 1;
    для i от 1 до н
        рез := рез * i;
    кц
    вывод(рез);
кон'''
        },
        {
            "name": "Условия и логика",
            "code": '''алг логика;
нач
    а : лог;
    б : лог;
кон
    а := да;
    б := нет;
    если а и не б то
        вывод("истина");
    иначе
        вывод("ложь");
    все
кон'''
        },
        {
            "name": "Вложенные циклы",
            "code": '''алг вложенные;
нач
    сумма : цел;
    i : цел;
    j : цел;
кон
    сумма := 0;
    для i от 1 до 3
        для j от 1 до 2
            сумма := сумма + i * j;
        кц
    кц
    вывод(сумма);
кон'''
        }
    ]

    passed = 0
    total = len(test_cases)

    for case in test_cases:
        print(f"=== Тест: {case['name']} ===")

        try:

            ast = parse(case['code'])


            interpreter_output = interpret(ast)


            program = compile_to_vm(ast)
            vm_output = run_vm_program(program)


            if interpreter_output == vm_output:
                print(f" {case['name']}: результаты совпадают")
                passed += 1
            else:
                print(f" {case['name']}: результаты различаются")
                print(f"  Интерпретатор: {interpreter_output}")
                print(f"  VM: {vm_output}")

        except Exception as e:
            print(f" {case['name']}: ошибка - {e}")

        print()

    print(f"Результаты специфических тестов: {passed}/{total}")
    return passed == total


def test_performance_comparison():
    print("⏱️ Сравнение производительности...\n")


    heavy_code = '''алг производительность;
нач
    сумма : цел;
    i : цел;
кон
    сумма := 0;
    для i от 1 до 1000
        сумма := сумма + i;
    кц
    вывод(сумма);
кон'''

    try:
        import time

        ast = parse(heavy_code)


        start_time = time.time()
        interpreter_output = interpret(ast)
        interpreter_time = time.time() - start_time


        program = compile_to_vm(ast)
        start_time = time.time()
        vm_output = run_vm_program(program)
        vm_time = time.time() - start_time

        print(f"Интерпретатор: {interpreter_time:.4f} сек")
        print(f"VM: {vm_time:.4f} сек")

        if vm_time < interpreter_time:
            speedup = interpreter_time / vm_time
            print(f" VM быстрее в {speedup:.2f} раз")
        else:
            slowdown = vm_time / interpreter_time
            print(f"🐌 VM медленнее в {slowdown:.2f} раз")


        if interpreter_output == vm_output:
            print(" Результаты совпадают")
            return True
        else:
            print(" Результаты различаются")
            return False

    except Exception as e:
        print(f" Ошибка в тесте производительности: {e}")
        return False


def run_all_integration_tests():
    print("🧪 Запуск полного набора интеграционных тестов...\n")

    tests = [
        ("Примеры из папки examples", test_all_examples),
        ("Специфические случаи", test_specific_cases),
        ("Сравнение производительности", test_performance_comparison)
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"🔄 {test_name}...")
        if test_func():
            passed += 1
        print("=" * 50)

    print(f"\nОбщие результаты: {passed}/{total} групп тестов прошли")

    if passed == total:
        print(" Все интеграционные тесты прошли успешно!")
        print("✨ Интерпретатор и VM работают корректно и дают одинаковые результаты!")
        return True
    else:
        print(" Некоторые интеграционные тесты не прошли")
        return False


if __name__ == "__main__":
    run_all_integration_tests()