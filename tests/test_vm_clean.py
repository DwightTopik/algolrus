import sys
import os

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import json
from vm_core import VMProgram, run_vm_program

def main():
    print("=== Тест VM ===")
    
    try:
        avm_file = "hello.avm"
        
        # Создаем тестовый файл если его нет
        if not os.path.exists(avm_file):
            print("Файл hello.avm не найден, создаем тестовую программу...")
            from vm_core import VMInstruction, OpCode
            
            test_program = VMProgram(
                constants=["Привет от VM!"],
                code=[
                    VMInstruction(OpCode.PUSH_CONST, 0),
                    VMInstruction(OpCode.PRINT),
                    VMInstruction(OpCode.HALT)
                ],
                globals_count=0
            )
            
            test_program.save_to_file(avm_file)
            print(f"Создан тестовый файл {avm_file}")
        
        print("1. Загружаем JSON...")
        with open(avm_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print("    JSON загружен")
        
        print("2. Создаем VMProgram...")
        program = VMProgram.from_dict(data)
        print("    VMProgram создан")
        
        print("3. Инструкции:")
        for i, instr in enumerate(program.code):
            print(f"   {i}: {instr}")
        
        print("4. Запускаем VM...")
        output = run_vm_program(program, trace=False)
        print("    VM завершен")
        
        print(f"5. Результат: {output}")
        if output:
            print("   Вывод программы:")
            for line in output:
                print(f"     {line}")
        else:
            print("   Нет вывода")
        
        print("Тест VM clean завершен успешно")
            
    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 