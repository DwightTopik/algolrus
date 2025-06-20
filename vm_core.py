import json
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum
from mel_types import *


class VMError(Exception):
    def __init__(self, message: str, ip: int = -1):
        self.message = message
        self.ip = ip
        super().__init__(self.format_message())

    def format_message(self) -> str:
        if self.ip >= 0:
            return f"Ошибка VM на инструкции {self.ip}: {self.message}"
        return f"Ошибка VM: {self.message}"


class OpCode(Enum):

    PUSH_CONST = "PUSH_CONST"
    PUSH_INT = "PUSH_INT"
    PUSH_BOOL = "PUSH_BOOL"
    PUSH_CHAR = "PUSH_CHAR"
    PUSH_STRING = "PUSH_STRING"


    LOAD_GLOBAL = "LOAD_GLOBAL"
    STORE_GLOBAL = "STORE_GLOBAL"
    LOAD_LOCAL = "LOAD_LOCAL"
    STORE_LOCAL = "STORE_LOCAL"


    LOAD_ARRAY = "LOAD_ARRAY"
    STORE_ARRAY = "STORE_ARRAY"


    ADD = "ADD"
    SUB = "SUB"
    MUL = "MUL"
    DIV = "DIV"
    IDIV = "IDIV"
    MOD = "MOD"
    NEG = "NEG"


    EQ = "EQ"
    NE = "NE"
    LT = "LT"
    LE = "LE"
    GT = "GT"
    GE = "GE"


    AND = "AND"
    OR = "OR"
    NOT = "NOT"


    JMP = "JMP"
    JMP_IF_FALSE = "JMP_IF_FALSE"
    JMP_IF_TRUE = "JMP_IF_TRUE"


    CALL = "CALL"
    RETURN = "RETURN"


    PRINT = "PRINT"
    INC = "INC"
    DEC = "DEC"
    ABS = "ABS"


    POP = "POP"
    DUP = "DUP"


    NOP = "NOP"
    HALT = "HALT"


@dataclass
class VMInstruction:
    opcode: OpCode
    arg: Optional[Any] = None

    def __str__(self) -> str:
        if self.arg is not None:
            return f"{self.opcode.value} {self.arg}"
        return self.opcode.value


@dataclass
class VMProgram:
    constants: List[Any]
    code: List[VMInstruction]
    globals_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "constants": self.constants,
            "code": [(instr.opcode.value, instr.arg) for instr in self.code],
            "globals_count": self.globals_count
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VMProgram':
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
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

    @classmethod
    def load_from_file(cls, filename: str) -> 'VMProgram':
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_dict(data)


@dataclass
class CallFrame:
    locals: List[Any]
    return_address: int
    function_name: str = ""


class VirtualMachine:

    def __init__(self, trace: bool = False):
        self.trace = trace
        self.reset()

    def reset(self):
        self.ip = 0
        self.stack: List[Any] = []
        self.globals: List[Any] = []
        self.call_stack: List[CallFrame] = []
        self.output: List[str] = []
        self.halted = False


        self.program: Optional[VMProgram] = None

    def run(self, program: VMProgram) -> List[str]:
        self.reset()
        self.program = program


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
        if not self.program or self.ip >= len(self.program.code):
            raise VMError("Попытка выполнения за пределами программы", self.ip)

        instruction = self.program.code[self.ip]

        if self.trace:
            self.trace_instruction(instruction)


        self.execute_instruction(instruction)


        if not self.halted:
            self.ip += 1

    def execute_instruction(self, instruction: VMInstruction):
        opcode = instruction.opcode
        arg = instruction.arg


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
            self.push(a // b)
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


        elif opcode == OpCode.AND:
            b, a = self.pop(), self.pop()
            self.push(bool(a) and bool(b))
        elif opcode == OpCode.OR:
            b, a = self.pop(), self.pop()
            self.push(bool(a) or bool(b))
        elif opcode == OpCode.NOT:
            a = self.pop()
            self.push(not bool(a))


        elif opcode == OpCode.JMP:
            self.ip = arg - 1
        elif opcode == OpCode.JMP_IF_FALSE:
            condition = self.pop()
            if not bool(condition):
                self.ip = arg - 1
        elif opcode == OpCode.JMP_IF_TRUE:
            condition = self.pop()
            if bool(condition):
                self.ip = arg - 1


        elif opcode == OpCode.CALL:

            if len(arg) == 3:
                func_addr, num_params, total_locals = arg
            else:
                # Обратная совместимость
                func_addr, num_params = arg
                total_locals = num_params
            
            # Извлекаем аргументы из стека
            args = []
            for _ in range(num_params):
                args.append(self.pop())
            
            # Дополняем локальные переменные до нужного количества
            locals_list = args + [self.get_default_value()] * (total_locals - num_params)
            
            # Создаем новый фрейм с аргументами как локальными переменными
            frame = CallFrame(
                locals=locals_list,
                return_address=self.ip + 1
            )
            self.call_stack.append(frame)
            self.ip = func_addr - 1
        elif opcode == OpCode.RETURN:
            if not self.call_stack:

                self.halted = True
                return
            frame = self.call_stack.pop()
            self.ip = frame.return_address - 1


        elif opcode == OpCode.PRINT:
            value = self.pop()
            output_str = self.format_value(value)
            self.output.append(output_str + "\n")
            if self.trace:
                print(output_str)
        elif opcode == OpCode.INC:

            if arg < len(self.globals):
                self.globals[arg] += 1
            else:
                raise VMError(f"Неверный индекс переменной для INC: {arg}")
        elif opcode == OpCode.DEC:

            if arg < len(self.globals):
                self.globals[arg] -= 1
            else:
                raise VMError(f"Неверный индекс переменной для DEC: {arg}")
        elif opcode == OpCode.ABS:
            a = self.pop()
            self.push(abs(a))


        elif opcode == OpCode.POP:
            self.pop()
        elif opcode == OpCode.DUP:
            value = self.pop()
            self.push(value)
            self.push(value)


        elif opcode == OpCode.NOP:
            pass
        elif opcode == OpCode.HALT:
            self.halted = True

        else:
            raise VMError(f"Неизвестная инструкция: {opcode}")

    def push(self, value: Any):
        self.stack.append(value)

    def pop(self) -> Any:
        if not self.stack:
            raise VMError("Попытка извлечения из пустого стека")
        return self.stack.pop()

    def peek(self) -> Any:
        if not self.stack:
            raise VMError("Попытка просмотра пустого стека")
        return self.stack[-1]

    def get_default_value(self) -> Any:
        return 0

    def format_value(self, value: Any) -> str:
        if isinstance(value, bool):
            return "да" if value else "нет"
        elif isinstance(value, str):
            return value
        else:
            return str(value)

    def trace_instruction(self, instruction: VMInstruction):
        stack_str = str(self.stack[-5:]) if len(self.stack) > 5 else str(self.stack)
        print(f"IP:{self.ip:3d} | {instruction} | Stack: {stack_str}")

    def get_state(self) -> Dict[str, Any]:
        return {
            "ip": self.ip,
            "stack": self.stack.copy(),
            "globals": self.globals.copy(),
            "call_stack_size": len(self.call_stack),
            "halted": self.halted
        }


def run_vm_program(program: VMProgram, trace: bool = False) -> List[str]:
    vm = VirtualMachine(trace=trace)
    return vm.run(program)



__all__ = [
    'VMError', 'OpCode', 'VMInstruction', 'VMProgram', 'CallFrame',
    'VirtualMachine', 'run_vm_program'
]
