



import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.stdout.reconfigure(encoding='utf-8')

import mel_parser
mel_parser._parser = None

from mel_parser import parse
from interpreter import interpret, InterpreterError


def test_simple_assignment():
    print("=== Тест простого присваивания ===")

    source = '''алг тест;
нач
    а : цел;
кон
    а := 42;
    вывод(а);
кон'''

    try:
        ast = parse(source)
        output = interpret(ast)

        expected = ["42\n"]
        assert output == expected, f"Ожидается {expected}, получено {output}"
        print(" Простое присваивание работает")
        return True
    except Exception as e:
        print(f" Ошибка: {e}")
        return False


def test_arithmetic():
    print("\n=== Тест арифметических операций ===")

    source = '''алг арифметика;
нач
    а : цел;
    б : цел;
    в : цел;
кон
    а := 10;
    б := 3;
    в := а + б;
    вывод(в);
    в := а - б;
    вывод(в);
    в := а * б;
    вывод(в);
    в := а / б;
    вывод(в);
    в := а mod б;
    вывод(в);
кон'''

    try:
        ast = parse(source)
        output = interpret(ast)

        expected = ["13\n", "7\n", "30\n", "3\n", "1\n"]
        assert output == expected, f"Ожидается {expected}, получено {output}"
        print(" Арифметические операции работают")
        return True
    except Exception as e:
        print(f" Ошибка: {e}")
        return False


def test_logical_operations():
    print("\n=== Тест логических операций ===")

    source = '''алг логика;
нач
    флаг1 : лог;
    флаг2 : лог;
    результат : лог;
кон
    флаг1 := да;
    флаг2 := нет;

    результат := флаг1 и флаг2;
    вывод(результат);

    результат := флаг1 или флаг2;
    вывод(результат);

    результат := не флаг1;
    вывод(результат);
кон'''

    try:
        ast = parse(source)
        output = interpret(ast)

        expected = ["False\n", "True\n", "False\n"]
        assert output == expected, f"Ожидается {expected}, получено {output}"
        print(" Логические операции работают")
        return True
    except Exception as e:
        print(f" Ошибка: {e}")
        return False


def test_arrays():
    print("\n=== Тест массивов ===")

    source = '''алг массивы;
нач
    массив : таб[3] цел;
    i : цел;
кон
    массив[1] := 10;
    массив[2] := 20;
    массив[3] := 30;

    для i от 1 до 3
        вывод(массив[i]);
    кц
кон'''

    try:
        ast = parse(source)
        output = interpret(ast)

        expected = ["10\n", "20\n", "30\n"]
        assert output == expected, f"Ожидается {expected}, получено {output}"
        print(" Массивы работают")
        return True
    except Exception as e:
        print(f" Ошибка: {e}")
        return False


def test_if_statement():
    print("\n=== Тест условного оператора ===")

    source = '''алг условие;
нач
    х : цел;
кон
    х := 5;

    если х > 3 то
        вывод("больше");
    иначе
        вывод("меньше");
    все

    если х < 3 то
        вывод("меньше");
    иначе
        вывод("больше или равно");
    все
кон'''

    try:
        ast = parse(source)
        output = interpret(ast)

        expected = ["больше\n", "больше или равно\n"]
        assert output == expected, f"Ожидается {expected}, получено {output}"
        print(" Условный оператор работает")
        return True
    except Exception as e:
        print(f" Ошибка: {e}")
        return False


def test_for_loop():
    print("\n=== Тест цикла for ===")

    source = '''алг цикл_for;
нач
    i : цел;
кон
    для i от 1 до 3
        вывод(i);
    кц
кон'''

    try:
        ast = parse(source)
        output = interpret(ast)

        expected = ["1\n", "2\n", "3\n"]
        assert output == expected, f"Ожидается {expected}, получено {output}"
        print(" Цикл for работает")
        return True
    except Exception as e:
        print(f" Ошибка: {e}")
        return False


def test_while_loop():
    print("\n=== Тест цикла while ===")

    source = '''алг цикл_while;
нач
    i : цел;
кон
    i := 1;
    пока i <= 3
        вывод(i);
        i := i + 1;
    кц
кон'''

    try:
        ast = parse(source)
        output = interpret(ast)

        expected = ["1\n", "2\n", "3\n"]
        assert output == expected, f"Ожидается {expected}, получено {output}"
        print(" Цикл while работает")
        return True
    except Exception as e:
        print(f" Ошибка: {e}")
        return False


def test_builtin_functions():
    print("\n=== Тест встроенных функций ===")

    source = '''алг встроенные;
нач
    х : цел;
кон
    х := 5;
    вывод(х);

    увел(х);
    вывод(х);

    умен(х);
    вывод(х);

    х := модуль(-10);
    вывод(х);
кон'''

    try:
        ast = parse(source)
        output = interpret(ast)

        expected = ["5\n", "6\n", "5\n", "10\n"]
        assert output == expected, f"Ожидается {expected}, получено {output}"
        print(" Встроенные функции работают")
        return True
    except Exception as e:
        print(f" Ошибка: {e}")
        return False


def test_complex_program():
    print("\n=== Тест сложной программы ===")

    source = '''алг факториал;
нач
    n : цел;
    результат : цел;
    i : цел;
кон
    n := 5;
    результат := 1;

    для i от 1 до n
        результат := результат * i;
    кц

    вывод("Факториал");
    вывод(n);
    вывод("равен");
    вывод(результат);
кон'''

    try:
        ast = parse(source)
        output = interpret(ast)

        expected = ["Факториал\n", "5\n", "равен\n", "120\n"]
        assert output == expected, f"Ожидается {expected}, получено {output}"
        print(" Сложная программа работает")
        return True
    except Exception as e:
        print(f" Ошибка: {e}")
        return False


def run_all_tests():
    print("Запуск тестов интерпретатора...\n")

    tests = [
        test_simple_assignment,
        test_arithmetic,
        test_logical_operations,
        test_arrays,
        test_if_statement,
        test_for_loop,
        test_while_loop,
        test_builtin_functions,
        test_complex_program,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1

    print(f"\n{'='*50}")
    print(f"Результаты тестов: {passed}/{total} прошли")

    if passed == total:
        print(" Все тесты прошли успешно!")
        return True
    else:
        print(f" {total - passed} тестов не прошли")
        return False


if __name__ == "__main__":
    run_all_tests()