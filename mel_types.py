from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from dataclasses import dataclass


class Type(ABC):
    """Базовый класс для всех типов языка"""
    
    @abstractmethod
    def __str__(self) -> str:
        pass
    
    @abstractmethod
    def __eq__(self, other) -> bool:
        pass
    
    @abstractmethod
    def __hash__(self) -> int:
        pass
    
    def is_compatible_with(self, other: 'Type') -> bool:
        """Проверка совместимости типов для присваивания"""
        return self == other


class IntegerType(Type):
    """Тип 'цел' - целые числа"""
    
    def __str__(self) -> str:
        return "цел"
    
    def __eq__(self, other) -> bool:
        return isinstance(other, IntegerType)
    
    def __hash__(self) -> int:
        return hash("цел")


class BooleanType(Type):
    """Тип 'лог' - логические значения"""
    
    def __str__(self) -> str:
        return "лог"
    
    def __eq__(self, other) -> bool:
        return isinstance(other, BooleanType)
    
    def __hash__(self) -> int:
        return hash("лог")


class CharType(Type):
    """Тип 'сим' - символы"""
    
    def __str__(self) -> str:
        return "сим"
    
    def __eq__(self, other) -> bool:
        return isinstance(other, CharType)
    
    def __hash__(self) -> int:
        return hash("сим")


class StringType(Type):
    """Тип 'строка' - строки (для литералов)"""
    
    def __str__(self) -> str:
        return "строка"
    
    def __eq__(self, other) -> bool:
        return isinstance(other, StringType)
    
    def __hash__(self) -> int:
        return hash("строка")


@dataclass
class ArrayType(Type):
    """Тип массива: таб[размер] тип_элемента"""
    element_type: Type
    size: Optional[int] = None  # None для динамических массивов
    
    def __str__(self) -> str:
        size_str = str(self.size) if self.size is not None else "?"
        return f"таб[{size_str}] {self.element_type}"
    
    def __eq__(self, other) -> bool:
        return (isinstance(other, ArrayType) and 
                self.element_type == other.element_type and
                self.size == other.size)
    
    def __hash__(self) -> int:
        return hash(("таб", self.element_type, self.size))


@dataclass
class FunctionType(Type):
    """Тип функции/процедуры"""
    param_types: List[Type]
    return_type: Optional[Type]  # None для процедур
    
    def __str__(self) -> str:
        params_str = ", ".join(str(t) for t in self.param_types)
        if self.return_type:
            return f"алг({params_str}) : {self.return_type}"
        else:
            return f"алг({params_str})"
    
    def __eq__(self, other) -> bool:
        return (isinstance(other, FunctionType) and 
                self.param_types == other.param_types and
                self.return_type == other.return_type)
    
    def __hash__(self) -> int:
        return hash(("алг", tuple(self.param_types), self.return_type))


class VoidType(Type):
    """Тип 'пусто' - для процедур без возвращаемого значения"""
    
    def __str__(self) -> str:
        return "пусто"
    
    def __eq__(self, other) -> bool:
        return isinstance(other, VoidType)
    
    def __hash__(self) -> int:
        return hash("пусто")


# Синглтоны для базовых типов
INTEGER = IntegerType()
BOOLEAN = BooleanType()
CHAR = CharType()
STRING = StringType()
VOID = VoidType()


# Операторы и их типы
ARITHMETIC_OPS = {'+', '-', '*', '/', 'div', 'mod'}
COMPARISON_OPS = {'=', '<>', '>', '>=', '<', '<='}
LOGICAL_OPS = {'и', 'или', 'не'}
UNARY_OPS = {'+', '-', 'не'}


def get_binary_op_result_type(op: str, left_type: Type, right_type: Type) -> Optional[Type]:
    """Определяет тип результата бинарной операции"""
    
    if op in ARITHMETIC_OPS:
        # Арифметические операции работают только с целыми числами
        if left_type == INTEGER and right_type == INTEGER:
            return INTEGER
        return None
    
    elif op in COMPARISON_OPS:
        # Операции сравнения возвращают логический тип
        if left_type == right_type:
            # Можно сравнивать одинаковые типы
            if left_type in [INTEGER, BOOLEAN, CHAR]:
                return BOOLEAN
        return None
    
    elif op in LOGICAL_OPS:
        # Логические операции работают только с логическими значениями
        if op == 'не':
            # Унарная операция
            if left_type == BOOLEAN:
                return BOOLEAN
        else:
            # Бинарные операции
            if left_type == BOOLEAN and right_type == BOOLEAN:
                return BOOLEAN
        return None
    
    return None


def get_unary_op_result_type(op: str, operand_type: Type) -> Optional[Type]:
    """Определяет тип результата унарной операции"""
    
    if op in ['+', '-']:
        # Унарные арифметические операции
        if operand_type == INTEGER:
            return INTEGER
        return None
    
    elif op == 'не':
        # Логическое отрицание
        if operand_type == BOOLEAN:
            return BOOLEAN
        return None
    
    return None


def is_assignable(source: Type, target: Type) -> bool:
    """Проверяет, можно ли присвоить значение типа source переменной типа target"""
    return source.is_compatible_with(target)


def type_from_string(type_name: str) -> Optional[Type]:
    """Создает тип по его строковому представлению"""
    type_map = {
        'цел': INTEGER,
        'лог': BOOLEAN,
        'сим': CHAR,
        'строка': STRING,
        'пусто': VOID
    }
    return type_map.get(type_name)


def get_default_value(type_obj: Type) -> Any:
    """Возвращает значение по умолчанию для типа"""
    if type_obj == INTEGER:
        return 0
    elif type_obj == BOOLEAN:
        return False
    elif type_obj == CHAR:
        return '\0'
    elif type_obj == STRING:
        return ""
    elif isinstance(type_obj, ArrayType):
        # Для массивов возвращаем список значений по умолчанию
        if type_obj.size:
            default_element = get_default_value(type_obj.element_type)
            return [default_element] * type_obj.size
        return []
    else:
        return None


# Встроенные функции и их типы
BUILTIN_FUNCTIONS = {
    # Ввод-вывод
    'вывод': FunctionType([STRING], VOID),
    'выводстр': FunctionType([STRING], VOID),
    'ввод': FunctionType([INTEGER], VOID),  # Читает в переменную
    'вводстр': FunctionType([STRING], VOID),
    
    # Математические функции
    'увел': FunctionType([INTEGER], VOID),  # Inc
    'умен': FunctionType([INTEGER], VOID),  # Dec
    'модуль': FunctionType([INTEGER], INTEGER),  # Abs
    
    # Функции для работы с символами
    'код': FunctionType([CHAR], INTEGER),  # Ord
    'симв': FunctionType([INTEGER], CHAR),  # Chr
}


def get_builtin_function_type(name: str) -> Optional[FunctionType]:
    """Возвращает тип встроенной функции по имени"""
    return BUILTIN_FUNCTIONS.get(name)


def is_builtin_function(name: str) -> bool:
    """Проверяет, является ли имя встроенной функцией"""
    return name in BUILTIN_FUNCTIONS


# Экспорт
__all__ = [
    'Type', 'IntegerType', 'BooleanType', 'CharType', 'StringType', 
    'ArrayType', 'FunctionType', 'VoidType',
    'INTEGER', 'BOOLEAN', 'CHAR', 'STRING', 'VOID',
    'ARITHMETIC_OPS', 'COMPARISON_OPS', 'LOGICAL_OPS', 'UNARY_OPS',
    'get_binary_op_result_type', 'get_unary_op_result_type',
    'is_assignable', 'type_from_string', 'get_default_value',
    'get_builtin_function_type', 'is_builtin_function', 'BUILTIN_FUNCTIONS'
]
