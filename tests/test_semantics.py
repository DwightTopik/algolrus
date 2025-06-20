

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.stdout.reconfigure(encoding='utf-8')

from mel_parser import parse
from semantics import analyze, check_semantics
from mel_types import INTEGER, BOOLEAN


def test_valid_program():
    print("=== Тест 1: Валидная программа ===")

    source = '''алг тест_валидный;
нач
    а : цел;
    б : цел;
    флаг : лог;
кон
    а := 10;
    б := а + 5;
    флаг := а > б;
кон'''

    try:
        ast = parse(source)
        print("Парсинг успешен")

        errors = analyze(ast)
        if errors:
            print("Семантические ошибки:")
            for error in errors:
                print(f"  - {error}")
            return False
        else:
            print("Семантический анализ прошел успешно!")


            var_a = ast.block.var_decls[0]
            var_b = ast.block.var_decls[1]
            var_flag = ast.block.var_decls[2]

            print(f"  Переменная 'а': {var_a.type}")
            print(f"  Переменная 'б': {var_b.type}")
            print(f"  Переменная 'флаг': {var_flag.type}")

            return True

    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_type_error():
    print("\n=== Тест 2: Ошибка типов ===")

    source = '''алг тест_ошибка_типов;
нач
    а : цел;
    флаг : лог;
кон
    а := да + 1;  | Ошибка: нельзя складывать логическое и целое
кон'''

    try:
        ast = parse(source)
        print("Парсинг успешен")

        errors = analyze(ast)
        if errors:
            print("Найдены ожидаемые семантические ошибки:")
            for error in errors:
                print(f"  - {error}")
            return True
        else:
            print("Ошибка не найдена - это неправильно!")
            return False

    except Exception as e:
        print(f" Неожиданная ошибка: {e}")
        return False


def test_undefined_variable():
    print("\n=== Тест 3: Неопределенная переменная ===")

    source = '''алг тест_неопределенная;
нач
    а : цел;
кон
    а := б + 1;  | Ошибка: 'б' не объявлена
кон'''

    try:
        ast = parse(source)
        print("Парсинг успешен")

        errors = analyze(ast)
        if errors:
            print("Найдены ожидаемые ошибки:")
            for error in errors:
                print(f"  - {error}")
            return True
        else:
            print("Ошибка не найдена!")
            return False

    except Exception as e:
        print(f" Неожиданная ошибка: {e}")
        return False


def test_assignment_compatibility():
    print("\n=== Тест 4: Совместимость типов при присваивании ===")

    source = '''алг тест_присваивание;
нач
    а : цел;
    флаг : лог;
кон
    флаг := а;  | Ошибка: нельзя присвоить цел переменной лог
кон'''

    try:
        ast = parse(source)
        print("Парсинг успешен")

        errors = analyze(ast)
        if errors:
            print("Найдены ожидаемые ошибки несовместимости типов:")
            for error in errors:
                print(f"  - {error}")
            return True
        else:
            print("Ошибка несовместимости типов не найдена!")
            return False

    except Exception as e:
        print(f" Неожиданная ошибка: {e}")
        return False


def test_complex_expressions():
    print("\n=== Тест 5: Сложные выражения ===")

    source = '''алг тест_выражения;
нач
    а : цел;
    б : цел;
    в : цел;
    флаг1 : лог;
    флаг2 : лог;
кон
    а := 10;
    б := 20;
    в := (а + б) * 2 - 5 / 2;  | Арифметическое выражение
    флаг1 := а > б и б < в;     | Логическое выражение
    флаг2 := не (а = б);        | Унарная операция
кон'''

    try:
        ast = parse(source)
        print("Парсинг успешен")

        errors = analyze(ast)
        if errors:
            print("Неожиданные семантические ошибки:")
            for error in errors:
                print(f"  - {error}")
            return False
        else:
            print("Сложные выражения прошли семантический анализ!")
            return True

    except Exception as e:
        print(f" Неожиданная ошибка: {e}")
        return False


def test_functions():
    print("\n=== Тест 6: Функции ===")

    source = '''алг тест_функции;
нач
    а : цел;
    б : цел;
кон
функции
    функция сумма(х : цел, у : цел) : цел;
    нач
        результат : цел;
    кон
        результат := х + у;
        знач результат;
    кон
кон
    а := 10;
    б := 20;
    а := сумма(а, б);
кон'''

    try:
        ast = parse(source)
        print("Парсинг успешен")

        errors = analyze(ast)
        if errors:
            print("Семантические ошибки в функциях:")
            for error in errors:
                print(f"  - {error}")
            return False
        else:
            print("Функции прошли семантический анализ!")
            return True

    except Exception as e:
        print(f" Неожиданная ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    print("🧪 ТЕСТИРОВАНИЕ СЕМАНТИЧЕСКОГО АНАЛИЗАТОРА")
    print("=" * 60)

    tests = [
        test_valid_program,
        test_type_error,
        test_undefined_variable,
        test_assignment_compatibility,
        test_complex_expressions,
        test_functions
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1

    print("\n" + "=" * 60)
    print(f"РЕЗУЛЬТАТЫ: {passed}/{total} тестов пройдено")

    if passed == total:
        print(" ВСЕ ТЕСТЫ ПРОЙДЕНЫ! Семантический анализатор работает корректно!")
        return True
    else:
        print(f" {total - passed} тестов не пройдено")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)