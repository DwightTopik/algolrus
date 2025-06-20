import subprocess
import sys
import os

# Настройка кодировки для Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def run_test(test_name, test_file):
    print(f"\n{'='*60}")
    print(f"Запуск теста: {test_name}")
    print(f"{'='*60}")

    try:
        result = subprocess.run(
            [sys.executable, test_file],
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=60
        )

        if result.returncode == 0:
            print(f" {test_name} - ПРОЙДЕН")
            if result.stdout:
                print("Вывод:")
                print(result.stdout)
            return True
        else:
            print(f" {test_name} - ПРОВАЛЕН")
            if result.stderr:
                print("Ошибки:")
                print(result.stderr)
            return False

    except subprocess.TimeoutExpired:
        print(f"{test_name} - ПРЕВЫШЕН TIMEOUT")
        return False
    except Exception as e:
        print(f"{test_name} - ОШИБКА: {e}")
        return False

def main():
    print(" Запуск всех тестов компилятора AlgolRus")


    tests = [
        ("Тест оптимизаций", "test_optimization.py"),
        ("Тест виртуальной машины", "test_vm.py"),
        ("Тест интерпретатора", "test_interpreter.py"),
        ("Тест семантики", "test_semantics.py"),
        ("Тест peephole оптимизаций", "test_peephole.py"),
        ("Интеграционный тест", "test_integration.py"),
        ("Финальный интеграционный тест", "test_final_integration.py"),
    ]

    results = {}

    for test_name, test_file in tests:
        results[test_name] = run_test(test_name, test_file)


    print(f"\n{'='*60}")
    print("ИТОГОВЫЕ РЕЗУЛЬТАТЫ")
    print(f"{'='*60}")

    passed = 0
    total = len(tests)

    for test_name, test_file in tests:
        status = " ПРОЙДЕН" if results[test_name] else " ПРОВАЛЕН"
        print(f"{test_name:.<40} {status}")
        if results[test_name]:
            passed += 1

    print(f"\nСтатистика: {passed}/{total} тестов пройдено ({passed/total*100:.1f}%)")

    if passed == total:
        print(" ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
        return 0
    else:
        print(f"  {total - passed} тестов провалено")
        return 1

if __name__ == "__main__":
    sys.exit(main())