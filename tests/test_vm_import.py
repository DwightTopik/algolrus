import sys
import os

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
print("Тест импорта vm_core...")

try:
    print("Импортируем vm_core...")
    import vm_core
    print("vm_core импортирован")
    
    print("Импортируем VMProgram...")
    from vm_core import VMProgram
    print("VMProgram импортирован")
    
    print("Импортируем run_vm_program...")
    from vm_core import run_vm_program
    print("run_vm_program импортирован")
    
    print("Тестируем создание простой VM программы...")
    from vm_core import VMInstruction, OpCode
    
    program = VMProgram(
        constants=[42],
        code=[
            VMInstruction(OpCode.PUSH_INT, 42),
            VMInstruction(OpCode.HALT)
        ],
        globals_count=0
    )
    print("VMProgram создан")
    
    print("Все импорты успешны!")
    
except Exception as e:
    print(f"Ошибка импорта: {e}")
    import traceback
    traceback.print_exc()

print("Тест завершен") 