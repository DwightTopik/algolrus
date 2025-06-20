import json
from vm_core import VMProgram, run_vm_program

# Загружаем hello.avm и запускаем
try:
    print("Загружаем hello.avm...")
    
    # Сначала загружаем JSON вручную
    print("Читаем файл...")
    with open("hello.avm", 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print("JSON загружен успешно")
    print(f"Ключи: {data.keys()}")
    print(f"Количество инструкций: {len(data['code'])}")
    
    # Теперь создаем программу
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
        
except Exception as e:
    print(f"Ошибка: {e}")
    import traceback
    traceback.print_exc() 