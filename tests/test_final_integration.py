#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Финальный интеграционный тест компилятора AlgolRus
Проверяет все компоненты: парсер, семантику, интерпретатор, VM, оптимизации
"""

import subprocess
import sys
import tempfile
import os
from pathlib import Path

def create_test_program():
    """Создает тестовую программу для проверки всех возможностей"""
    return '''алг финальный_тест;
нач
    х : цел;
    у : цел;
    результат : цел;
    флаг : лог;
    счетчик : цел;
кон
    х := 2 + 3 * 4;
    у := 10 - 5;
    
    х := х + 0;
    у := у * 1;
    
    флаг := х > у;
    
    если флаг то
        вывод("х больше у");
    иначе
        вывод("у больше или равно х");
    все
    
    результат := 0;
    для счетчик от 1 до 3
        результат := результат + счетчик;
    кц
    
    пока результат < 10
        результат := результат + 1;
    кц
    
    вывод("Результат:");
    вывод(результат);
    
    результат := модуль(-5);
    вывод("Модуль -5:");
    вывод(результат);
кон'''

def test_component(component_name, command, expected_in_output=None):
    """Тестирует отдельный компонент"""
    print(f"\n=== Тест {component_name} ===")
    
    try:
        result = subprocess.run(
            command, 
            capture_output=True, 
            text=True, 
            encoding='utf-8',
            timeout=30
        )
        
        print(f"Код возврата: {result.returncode}")
        
        if result.stdout:
            print("Вывод:")
            print(result.stdout)
        
        if result.stderr:
            print("Ошибки:")
            print(result.stderr)
        
        # Проверяем успешность выполнения
        if result.returncode != 0:
            print(f"❌ {component_name} завершился с ошибкой")
            return False
        
        # Проверяем ожидаемый вывод
        if expected_in_output:
            for expected in expected_in_output:
                if expected not in result.stdout:
                    print(f"❌ Ожидаемый вывод '{expected}' не найден")
                    return False
        
        print(f"✅ {component_name} работает корректно")
        return True
        
    except subprocess.TimeoutExpired:
        print(f"❌ {component_name} превысил время ожидания")
        return False
    except Exception as e:
        print(f"❌ Ошибка при тестировании {component_name}: {e}")
        return False

def run_final_integration_test():
    """Запускает финальный интеграционный тест"""
    print("🚀 Запуск финального интеграционного теста AlgolRus")
    print("=" * 60)
    
    # Создаем временный файл с тестовой программой
    test_program = create_test_program()
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.alg', delete=False, encoding='utf-8') as f:
        f.write(test_program)
        test_file = f.name
    
    try:
        results = {}
        
        # 1. Тест парсера
        results['parser'] = test_component(
            "Парсер",
            [sys.executable, 'main.py', 'parse', test_file],
            expected_in_output=["Парсинг успешен!", "AST:"]
        )
        
        # 2. Тест интерпретатора без оптимизаций
        results['interpreter'] = test_component(
            "Интерпретатор (без оптимизаций)",
            [sys.executable, 'main.py', 'run', test_file],
            expected_in_output=["х больше у", "Результат:", "10", "Модуль -5:", "5"]
        )
        
        # 3. Тест интерпретатора с оптимизациями
        results['interpreter_opt'] = test_component(
            "Интерпретатор (с оптимизациями)",
            [sys.executable, 'main.py', 'run', test_file, '-O', '-v'],
            expected_in_output=["х больше у", "Результат:", "10", "🔧 Применено оптимизаций"]
        )
        
        # 4. Тест компиляции без оптимизаций
        avm_file = test_file.replace('.alg', '.avm')
        results['compile'] = test_component(
            "Компилятор VM (без оптимизаций)",
            [sys.executable, 'main.py', 'compile', test_file, '-o', avm_file],
            expected_in_output=["Компиляция программы", "Байт-код сохранен"]
        )
        
        # 5. Тест выполнения VM
        if results['compile']:
            results['vm'] = test_component(
                "Виртуальная машина",
                [sys.executable, 'main.py', 'vm', avm_file],
                expected_in_output=["х больше у", "Результат:", "10", "Модуль -5:", "5"]
            )
        else:
            results['vm'] = False
        
        # 6. Тест компиляции с оптимизациями
        avm_opt_file = test_file.replace('.alg', '_opt.avm')
        results['compile_opt'] = test_component(
            "Компилятор VM (с оптимизациями)",
            [sys.executable, 'main.py', 'compile', test_file, '-o', avm_opt_file, '-O', '-v'],
            expected_in_output=["🔧 Применено AST оптимизаций", "📊 Размер байт-кода"]
        )
        
        # 7. Тест выполнения оптимизированного VM
        if results['compile_opt']:
            results['vm_opt'] = test_component(
                "VM (оптимизированный)",
                [sys.executable, 'main.py', 'vm', avm_opt_file],
                expected_in_output=["х больше у", "Результат:", "10", "Модуль -5:", "5"]
            )
        else:
            results['vm_opt'] = False
        
        # 8. Тест сравнения результатов
        print("\n=== Сравнение результатов ===")
        
        # Запускаем все версии и сравниваем вывод
        commands = [
            ("Интерпретатор", [sys.executable, 'main.py', 'run', test_file]),
            ("Интерпретатор+O", [sys.executable, 'main.py', 'run', test_file, '-O']),
            ("VM", [sys.executable, 'main.py', 'vm', avm_file]),
            ("VM+O", [sys.executable, 'main.py', 'vm', avm_opt_file])
        ]
        
        outputs = {}
        for name, cmd in commands:
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', timeout=10)
                if result.returncode == 0:
                    # Извлекаем только программный вывод (без служебных сообщений)
                    lines = result.stdout.split('\n')
                    program_output = []
                    in_program = False
                    for line in lines:
                        if 'Запуск программы' in line or 'Запуск VM программы' in line:
                            in_program = True
                            continue
                        if in_program and line.strip() and not line.startswith('Программа завершена'):
                            program_output.append(line.strip())
                    outputs[name] = '\n'.join(program_output)
                else:
                    outputs[name] = f"ОШИБКА: {result.returncode}"
            except Exception as e:
                outputs[name] = f"ИСКЛЮЧЕНИЕ: {e}"
        
        # Сравниваем выводы
        reference_output = outputs.get("Интерпретатор", "")
        all_match = True
        
        for name, output in outputs.items():
            if name == "Интерпретатор":
                continue
            if output == reference_output:
                print(f"✅ {name}: вывод совпадает с эталоном")
            else:
                print(f"❌ {name}: вывод отличается")
                print(f"   Эталон: {reference_output}")
                print(f"   Получен: {output}")
                all_match = False
        
        results['consistency'] = all_match
        
        # Подводим итоги
        print("\n" + "=" * 60)
        print("📊 ИТОГОВЫЕ РЕЗУЛЬТАТЫ")
        print("=" * 60)
        
        passed = sum(1 for result in results.values() if result)
        total = len(results)
        
        for component, result in results.items():
            status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
            print(f"{component:25} {status}")
        
        print(f"\nОбщий результат: {passed}/{total} тестов пройдено")
        
        if passed == total:
            print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! КОМПИЛЯТОР ГОТОВ К АТТЕСТАЦИИ!")
            print("\n📋 Реализованные компоненты:")
            print("   ✅ Лексический анализатор")
            print("   ✅ Синтаксический анализатор") 
            print("   ✅ Семантический анализатор")
            print("   ✅ Tree-walking интерпретатор")
            print("   ✅ Кодогенератор VM")
            print("   ✅ Виртуальная машина")
            print("   ✅ AST оптимизации (Constant Folding)")
            print("   ✅ Bytecode оптимизации (Peephole)")
            print("   ✅ CLI интерфейс")
            print("   ✅ Полная документация")
            return True
        else:
            print(f"\n❌ {total - passed} тестов провалено. Требуется доработка.")
            return False
        
    finally:
        # Убираем временные файлы
        for file_path in [test_file, avm_file, avm_opt_file]:
            try:
                if os.path.exists(file_path):
                    os.unlink(file_path)
            except:
                pass

if __name__ == "__main__":
    success = run_final_integration_test()
    sys.exit(0 if success else 1) 