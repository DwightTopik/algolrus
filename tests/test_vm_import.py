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
    
    print("Все импорты успешны!")
    
except Exception as e:
    print(f"Ошибка импорта: {e}")
    import traceback
    traceback.print_exc()

print("Тест завершен") 