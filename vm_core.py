"""
Виртуальная машина для русскоязычного Pascal
Стековая архитектура с поддержкой локальных переменных и вызовов функций
"""

import json
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum
from mel_types import *


class VMError(Exception):
    """Исключение времени выполнения VM"""
    def __init__(self, message: str, ip: int = -1):
        self.message = message
        self.ip = ip
        super().__init__(self.format_message())
    
    def format_message(self) -> str:
        if self.ip >= 0:
            return f"Ошибка VM на инструкции {self.ip}: {self.message}"
        return f"Ошибка VM: {self.message}"


class OpCode(Enum):
    """Набор опкодов виртуальной машины"""
    
    # Константы и литералы
    PUSH_CONST = "PUSH_CONST"    # Загрузить константу на стек
    PUSH_INT = "PUSH_INT"        # Загрузить целое число на стек
    PUSH_BOOL = "PUSH_BOOL"      # Загрузить булево значение на стек
    PUSH_CHAR = "PUSH_CHAR"      # Загрузить символ на стек
    PUSH_STRING = "PUSH_STRING"  # Загрузить строку на стек
    
    # Переменные
    LOAD_GLOBAL = "LOAD_GLOBAL"  # Загрузить глобальную переменную
    STORE_GLOBAL = "STORE_GLOBAL" # Сохранить в глобальную переменную
    LOAD_LOCAL = "LOAD_LOCAL"    # Загрузить локальную переменную
    STORE_LOCAL = "STORE_LOCAL"  # Сохранить в локальную переменную
    
    # Массивы
    LOAD_ARRAY = "LOAD_ARRAY"    # Загрузить элемент массива
    STORE_ARRAY = "STORE_ARRAY"  # Сохранить элемент массива
    
    # Арифметические операции
    ADD = "ADD"          # Сложение
    SUB = "SUB"          # Вычитание
    MUL = "MUL"          # Умножение
    DIV = "DIV"          # Деление
    IDIV = "IDIV"        # Целочисленное деление (div)
    MOD = "MOD"          # Остаток от деления
    NEG = "NEG"          # Унарный минус
    
    # Операции сравнения
    EQ = "EQ"            # Равенство
    NE = "NE"            # Неравенство
    LT = "LT"            # Меньше
    LE = "LE"            # Меньше или равно
    GT = "GT"            # Больше
    GE = "GE"            # Больше или равно
    
    # Логические операции
    AND = "AND"          # Логическое И
    OR = "OR"            # Логическое ИЛИ
    NOT = "NOT"          # Логическое НЕ
    
    # Управление потоком
    JMP = "JMP"          # Безусловный переход
    JMP_IF_FALSE = "JMP_IF_FALSE"  # Переход если ложь
    JMP_IF_TRUE = "JMP_IF_TRUE"    # Переход если истина
    
    # Функции и процедуры
    CALL = "CALL"        # Вызов функции
    RETURN = "RETURN"    # Возврат из функции
    
    # Встроенные функции
    PRINT = "PRINT"      # Вывод значения
    INC = "INC"          # Увеличить на 1
    DEC = "DEC"          # Уменьшить на 1
    ABS = "ABS"          # Абсолютное значение
    
    # Управление стеком
    POP = "POP"          # Удалить верхний элемент стека
    DUP = "DUP"          # Дублировать верхний элемент стека
    
    # Специальные
    NOP = "NOP"          # Нет операции
    HALT = "HALT"        # Остановить выполнение


@dataclass
class VMInstruction:
    """Инструкция виртуальной машины"""
    opcode: OpCode
    arg: Optional[Any] = None
    
    def __str__(self) -> str:
        if self.arg is not None:
            return f"{self.opcode.value} {self.arg}"
        return self.opcode.value


@dataclass
class VMProgram:
    """Программа для виртуальной машины"""
    constants: List[Any]     # Таблица констант
    code: List[VMInstruction] # Список инструкций
    globals_count: int = 0   # Количество глобальных переменных
    
    def to_dict(self) -> Dict[str, Any]:
        """Сериализация в словарь"""
        return {
            "constants": self.constants,
            "code": [(instr.opcode.value, instr.arg) for instr in self.code],
            "globals_count": self.globals_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VMProgram':
        """Десериализация из словаря"""
        instructions = []
        for opcode_str, arg in data["code"]:
            opcode = OpCode(opcode_str)
            instructions.append(VMInstruction(opcode, arg))
        
        return cls(
            constants=data["constants"],
            code=instructions,
            globals_count=data.get("globals_count", 0)
        )
    
    def save_to_file(self, filename: str):
        """Сохранить программу в файл"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
    
    @classmethod
    def load_from_file(cls, filename: str) -> 'VMProgram':
        """Загрузить программу из файла"""
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_dict(data)


@dataclass
class CallFrame:
    """Кадр вызова функции"""
    locals: List[Any]        # Локальные переменные
    return_address: int      # Адрес возврата
    function_name: str = ""  # Имя функции (для отладки)


class VirtualMachine:
    """Стековая виртуальная машина"""
    
    def __init__(self, trace: bool = False):
        self.trace = trace
        self.reset()
    
    def reset(self):
        """Сброс состояния VM"""
        self.ip = 0                          # Указатель инструкций
        self.stack: List[Any] = []           # Стек операндов
        self.globals: List[Any] = []         # Глобальные переменные
        self.call_stack: List[CallFrame] = [] # Стек вызовов
        self.output: List[str] = []          # Буфер вывода
        self.halted = False                  # Флаг остановки
        
        # Текущая программа
        self.program: Optional[VMProgram] = None
    
    def run(self, program: VMProgram) -> List[str]:
        """Запуск программы"""
        self.reset()
        self.program = program
        
        # Инициализируем глобальные переменные
        self.globals = [self.get_default_value()] * program.globals_count
        
        try:
            while not self.halted and self.ip < len(program.code):
                self.step()
            
            return self.output.copy()
            
        except Exception as e:
            if isinstance(e, VMError):
                raise
            else:
                raise VMError(f"Неожиданная ошибка: {e}", self.ip)
    
    def step(self):
        """Выполнить одну инструкцию"""
        if not self.program or self.ip >= len(self.program.code):
            raise VMError("Попытка выполнения за пределами программы", self.ip)
        
        instruction = self.program.code[self.ip]
        
        if self.trace:
            self.trace_instruction(instruction)
        
        # Выполняем инструкцию
        self.execute_instruction(instruction)
        
        # Переходим к следующей инструкции (если не было перехода)
        if not self.halted:
            self.ip += 1
    
    def execute_instruction(self, instruction: VMInstruction):
        """Выполнить инструкцию"""
        opcode = instruction.opcode
        arg = instruction.arg
        
        # Константы и литералы
        if opcode == OpCode.PUSH_CONST:
            self.push(self.program.constants[arg])
        elif opcode == OpCode.PUSH_INT:
            self.push(arg)
        elif opcode == OpCode.PUSH_BOOL:
            self.push(arg)
        elif opcode == OpCode.PUSH_CHAR:
            self.push(arg)
        elif opcode == OpCode.PUSH_STRING:
            self.push(arg)
        
        # Переменные
        elif opcode == OpCode.LOAD_GLOBAL:
            if arg >= len(self.globals):
                raise VMError(f"Неверный индекс глобальной переменной: {arg}")
            self.push(self.globals[arg])
        elif opcode == OpCode.STORE_GLOBAL:
            if arg >= len(self.globals):
                raise VMError(f"Неверный индекс глобальной переменной: {arg}")
            self.globals[arg] = self.pop()
        elif opcode == OpCode.LOAD_LOCAL:
            if not self.call_stack:
                raise VMError("Попытка доступа к локальной переменной вне функции")
            frame = self.call_stack[-1]
            if arg >= len(frame.locals):
                raise VMError(f"Неверный индекс локальной переменной: {arg}")
            self.push(frame.locals[arg])
        elif opcode == OpCode.STORE_LOCAL:
            if not self.call_stack:
                raise VMError("Попытка доступа к локальной переменной вне функции")
            frame = self.call_stack[-1]
            if arg >= len(frame.locals):
                raise VMError(f"Неверный индекс локальной переменной: {arg}")
            frame.locals[arg] = self.pop()
        
        # Массивы
        elif opcode == OpCode.LOAD_ARRAY:
            index = self.pop()
            array = self.pop()
            if not isinstance(array, list):
                raise VMError("Попытка индексации не-массива")
            if not isinstance(index, int) or index < 0 or index >= len(array):
                raise VMError(f"Неверный индекс массива: {index}")
            self.push(array[index])
        elif opcode == OpCode.STORE_ARRAY:
            value = self.pop()
            index = self.pop()
            array = self.pop()
            if not isinstance(array, list):
                raise VMError("Попытка индексации не-массива")
            if not isinstance(index, int) or index < 0 or index >= len(array):
                raise VMError(f"Неверный индекс массива: {index}")
            array[index] = value
        
        # Арифметические операции
        elif opcode == OpCode.ADD:
            b, a = self.pop(), self.pop()
            self.push(a + b)
        elif opcode == OpCode.SUB:
            b, a = self.pop(), self.pop()
            self.push(a - b)
        elif opcode == OpCode.MUL:
            b, a = self.pop(), self.pop()
            self.push(a * b)
        elif opcode == OpCode.DIV:
            b, a = self.pop(), self.pop()
            if b == 0:
                raise VMError("Деление на ноль")
            self.push(a // b)  # Целочисленное деление в Pascal
        elif opcode == OpCode.IDIV:
            b, a = self.pop(), self.pop()
            if b == 0:
                raise VMError("Деление на ноль")
            self.push(a // b)
        elif opcode == OpCode.MOD:
            b, a = self.pop(), self.pop()
            if b == 0:
                raise VMError("Деление на ноль")
            self.push(a % b)
        elif opcode == OpCode.NEG:
            a = self.pop()
            self.push(-a)
        
        # Операции сравнения
        elif opcode == OpCode.EQ:
            b, a = self.pop(), self.pop()
            self.push(a == b)
        elif opcode == OpCode.NE:
            b, a = self.pop(), self.pop()
            self.push(a != b)
        elif opcode == OpCode.LT:
            b, a = self.pop(), self.pop()
            self.push(a < b)
        elif opcode == OpCode.LE:
            b, a = self.pop(), self.pop()
            self.push(a <= b)
        elif opcode == OpCode.GT:
            b, a = self.pop(), self.pop()
            self.push(a > b)
        elif opcode == OpCode.GE:
            b, a = self.pop(), self.pop()
            self.push(a >= b)
        
        # Логические операции
        elif opcode == OpCode.AND:
            b, a = self.pop(), self.pop()
            self.push(bool(a) and bool(b))
        elif opcode == OpCode.OR:
            b, a = self.pop(), self.pop()
            self.push(bool(a) or bool(b))
        elif opcode == OpCode.NOT:
            a = self.pop()
            self.push(not bool(a))
        
        # Управление потоком
        elif opcode == OpCode.JMP:
            self.ip = arg - 1  # -1 потому что ip++ в конце step()
        elif opcode == OpCode.JMP_IF_FALSE:
            condition = self.pop()
            if not bool(condition):
                self.ip = arg - 1
        elif opcode == OpCode.JMP_IF_TRUE:
            condition = self.pop()
            if bool(condition):
                self.ip = arg - 1
        
        # Функции и процедуры
        elif opcode == OpCode.CALL:
            # arg = (function_address, num_locals)
            func_addr, num_locals = arg
            # Создаем новый кадр
            frame = CallFrame(
                locals=[self.get_default_value()] * num_locals,
                return_address=self.ip + 1
            )
            self.call_stack.append(frame)
            self.ip = func_addr - 1
        elif opcode == OpCode.RETURN:
            if not self.call_stack:
                # Возврат из главной программы - завершение
                self.halted = True
                return
            frame = self.call_stack.pop()
            self.ip = frame.return_address - 1
        
        # Встроенные функции
        elif opcode == OpCode.PRINT:
            value = self.pop()
            output_str = self.format_value(value)
            self.output.append(output_str + "\n")
            if self.trace:
                print(output_str)
        elif opcode == OpCode.INC:
            # Увеличить переменную на 1 (arg - индекс переменной)
            if arg < len(self.globals):
                self.globals[arg] += 1
            else:
                raise VMError(f"Неверный индекс переменной для INC: {arg}")
        elif opcode == OpCode.DEC:
            # Уменьшить переменную на 1
            if arg < len(self.globals):
                self.globals[arg] -= 1
            else:
                raise VMError(f"Неверный индекс переменной для DEC: {arg}")
        elif opcode == OpCode.ABS:
            a = self.pop()
            self.push(abs(a))
        
        # Управление стеком
        elif opcode == OpCode.POP:
            self.pop()
        elif opcode == OpCode.DUP:
            value = self.pop()
            self.push(value)
            self.push(value)
        
        # Специальные
        elif opcode == OpCode.NOP:
            pass  # Ничего не делаем
        elif opcode == OpCode.HALT:
            self.halted = True
        
        else:
            raise VMError(f"Неизвестная инструкция: {opcode}")
    
    def push(self, value: Any):
        """Поместить значение на стек"""
        self.stack.append(value)
    
    def pop(self) -> Any:
        """Извлечь значение со стека"""
        if not self.stack:
            raise VMError("Попытка извлечения из пустого стека")
        return self.stack.pop()
    
    def peek(self) -> Any:
        """Посмотреть верхний элемент стека без извлечения"""
        if not self.stack:
            raise VMError("Попытка просмотра пустого стека")
        return self.stack[-1]
    
    def get_default_value(self) -> Any:
        """Получить значение по умолчанию для переменной"""
        return 0  # Для простоты все переменные инициализируются нулем
    
    def format_value(self, value: Any) -> str:
        """Форматировать значение для вывода"""
        if isinstance(value, bool):
            return "да" if value else "нет"
        elif isinstance(value, str):
            return value
        else:
            return str(value)
    
    def trace_instruction(self, instruction: VMInstruction):
        """Вывести трассировку инструкции"""
        stack_str = str(self.stack[-5:]) if len(self.stack) > 5 else str(self.stack)
        print(f"IP:{self.ip:3d} | {instruction} | Stack: {stack_str}")
    
    def get_state(self) -> Dict[str, Any]:
        """Получить текущее состояние VM для отладки"""
        return {
            "ip": self.ip,
            "stack": self.stack.copy(),
            "globals": self.globals.copy(),
            "call_stack_size": len(self.call_stack),
            "halted": self.halted
        }


def run_vm_program(program: VMProgram, trace: bool = False) -> List[str]:
    """Удобная функция для запуска программы VM"""
    vm = VirtualMachine(trace=trace)
    return vm.run(program)


# Экспорт
__all__ = [
    'VMError', 'OpCode', 'VMInstruction', 'VMProgram', 'CallFrame', 
    'VirtualMachine', 'run_vm_program'
]
