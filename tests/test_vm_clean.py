#!/usr/bin/env python3
import json
from vm_core import VMProgram, run_vm_program

def main():
    print("=== Тест VM ===")
    
    try:
        # Загружаем JSON
        print("1. Загружаем JSON...")
        with open("hello.avm", 'r', encoding='utf-8') as f:
            data = json.load(f)
        print("   ✅ JSON загружен")
        
        # Создаем программу
        print("2. Создаем VMProgram...")
        program = VMProgram.from_dict(data)
        print("   ✅ VMProgram создан")
        
        # Показываем инструкции
        print("3. Инструкции:")
        for i, instr in enumerate(program.code):
            print(f"   {i}: {instr}")
        
        # Запускаем VM
        print("4. Запускаем VM...")
        output = run_vm_program(program, trace=False)
        print("   ✅ VM завершен")
        
        # Показываем результат
        print(f"5. Результат: {output}")
        if output:
            print("   Вывод программы:")
            for line in output:
                print(f"     {line}")
        else:
            print("   Нет вывода")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 