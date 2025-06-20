import sys
import os

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import json
from vm_core import VMProgram, run_vm_program

print("Тест прямого запуска VM...")

try:
    print("Загружаем hello.avm...")
    
    avm_file = "hello.avm"
    if not os.path.exists(avm_file):
        print(f"Файл {avm_file} не найден, создаем тестовую программу...")
        
        # Создаем простую тестовую программу
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
    
    print("Читаем файл...")
    with open(avm_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print("JSON загружен успешно")
    print(f"Ключи: {data.keys()}")
    print(f"Количество инструкций: {len(data['code'])}")
    
    print("Создаем VMProgram...")
    program = VMProgram.from_dict(data)
    
    print("Содержимое программы:")
    for i, instr in enumerate(program.code):
        print(f"  {i}: {instr}")
    
    print("\nЗапускаем VM...")
    output = run_vm_program(program, trace=True)
    
    print(f"Результат VM: {output}")
    print(f"Тип результата: {type(output)}")
    
    if output:
        print("Вывод программы:")
        for line in output:
            print(f"  {line}")
    else:
        print("Нет вывода")
    
    print("Тест VM direct завершен успешно")
        
except Exception as e:
    print(f"Ошибка: {e}")
    import traceback
    traceback.print_exc() 