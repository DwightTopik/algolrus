from typing import List, Optional, Any, Union
from abc import ABC, abstractmethod


class SourcePosition:
    """Позиция в исходном коде"""
    def __init__(self, line: int, column: int):
        self.line = line
        self.column = column
    
    def __str__(self):
        return f"{self.line}:{self.column}"


class Node(ABC):
    """Базовый класс для всех узлов AST"""
    
    def __init__(self, meta: Optional[SourcePosition] = None):
        self.meta = meta
        self.type = None  # Заполняется в фазе семантического анализа
        self.const_value = None  # Для константных выражений
    
    def pretty(self, indent: int = 0) -> str:
        """Красивый вывод дерева"""
        spaces = "  " * indent
        name = self.__class__.__name__
        result = f"{spaces}{name}"
        
        # Добавляем позицию если есть
        if self.meta:
            result += f" @{self.meta}"
            
        # Добавляем тип если есть
        if self.type:
            result += f" : {self.type}"
            
        # Добавляем константное значение если есть
        if self.const_value is not None:
            result += f" = {self.const_value}"
            
        return result


# ============ Программа и блоки ============

class ProgramNode(Node):
    """Узел программы: алг <имя>; <блок>"""
    
    def __init__(self, name: str, block: 'BlockNode', meta: Optional[SourcePosition] = None):
        super().__init__(meta)
        self.name = name
        self.block = block
    
    def pretty(self, indent: int = 0) -> str:
        result = super().pretty(indent) + f"({self.name})\n"
        result += self.block.pretty(indent + 1)
        return result


class BlockNode(Node):
    """Блок: раздел переменных + раздел функций + раздел операторов"""
    
    def __init__(self, var_decls: List['VarDeclNode'] = None, 
                 func_decls: List['FuncDeclNode'] = None,
                 statements: List['StatementNode'] = None,
                 meta: Optional[SourcePosition] = None):
        super().__init__(meta)
        self.var_decls = var_decls or []
        self.func_decls = func_decls or []
        self.statements = statements or []
    
    def pretty(self, indent: int = 0) -> str:
        result = super().pretty(indent) + "\n"
        
        # Выводим объявления переменных
        if self.var_decls:
            for var_decl in self.var_decls:
                result += var_decl.pretty(indent + 1) + "\n"
        
        # Выводим объявления функций
        if self.func_decls:
            for func_decl in self.func_decls:
                result += func_decl.pretty(indent + 1) + "\n"
                
        # Выводим операторы
        for stmt in self.statements:
            result += stmt.pretty(indent + 1) + "\n"
            
        return result.rstrip()


# ============ Объявления ============

class VarDeclNode(Node):
    """Объявление переменной: <имя> : <тип>"""
    
    def __init__(self, name: str, var_type: 'TypeNode', meta: Optional[SourcePosition] = None):
        super().__init__(meta)
        self.name = name
        self.var_type = var_type
    
    def pretty(self, indent: int = 0) -> str:
        result = super().pretty(indent) + f"({self.name})\n"
        result += self.var_type.pretty(indent + 1)
        return result


class FuncDeclNode(Node):
    """Объявление функции: алг <имя>(<параметры>) : <тип>; <блок>"""
    
    def __init__(self, name: str, params: List['ParamNode'], 
                 return_type: Optional['TypeNode'], block: BlockNode,
                 meta: Optional[SourcePosition] = None):
        super().__init__(meta)
        self.name = name
        self.params = params
        self.return_type = return_type  # None для процедур
        self.block = block
    
    def pretty(self, indent: int = 0) -> str:
        result = super().pretty(indent) + f"({self.name})\n"
        
        for param in self.params:
            result += param.pretty(indent + 1) + "\n"
            
        if self.return_type:
            result += self.return_type.pretty(indent + 1) + "\n"
            
        result += self.block.pretty(indent + 1)
        return result


class ParamNode(Node):
    """Параметр функции: <имя> : <тип>"""
    
    def __init__(self, name: str, param_type: 'TypeNode', meta: Optional[SourcePosition] = None):
        super().__init__(meta)
        self.name = name
        self.param_type = param_type
    
    def pretty(self, indent: int = 0) -> str:
        result = super().pretty(indent) + f"({self.name})\n"
        result += self.param_type.pretty(indent + 1)
        return result


# ============ Типы ============

class TypeNode(Node):
    """Базовый класс для узлов типов"""
    pass


class SimpleTypeNode(TypeNode):
    """Простой тип: цел, лог, сим"""
    
    def __init__(self, name: str, meta: Optional[SourcePosition] = None):
        super().__init__(meta)
        self.name = name
    
    def pretty(self, indent: int = 0) -> str:
        return super().pretty(indent) + f"({self.name})"


class ArrayTypeNode(TypeNode):
    """Тип массива: таб[<размер>] <тип>"""
    
    def __init__(self, size: 'ExpressionNode', element_type: TypeNode, 
                 meta: Optional[SourcePosition] = None):
        super().__init__(meta)
        self.size = size
        self.element_type = element_type
    
    def pretty(self, indent: int = 0) -> str:
        result = super().pretty(indent) + "\n"
        result += self.size.pretty(indent + 1) + "\n"
        result += self.element_type.pretty(indent + 1)
        return result


# ============ Операторы ============

class StatementNode(Node):
    """Базовый класс для операторов"""
    pass


class AssignNode(StatementNode):
    """Присваивание: <переменная> := <выражение>"""
    
    def __init__(self, target: 'ExpressionNode', value: 'ExpressionNode',
                 meta: Optional[SourcePosition] = None):
        super().__init__(meta)
        self.target = target
        self.value = value
    
    def pretty(self, indent: int = 0) -> str:
        result = super().pretty(indent) + "\n"
        result += self.target.pretty(indent + 1) + "\n"
        result += self.value.pretty(indent + 1)
        return result


class IfNode(StatementNode):
    """Условный оператор: если <условие> то <блок> [иначе <блок>] все"""
    
    def __init__(self, condition: 'ExpressionNode', then_block: List[StatementNode],
                 else_block: Optional[List[StatementNode]] = None,
                 meta: Optional[SourcePosition] = None):
        super().__init__(meta)
        self.condition = condition
        self.then_block = then_block
        self.else_block = else_block
    
    def pretty(self, indent: int = 0) -> str:
        result = super().pretty(indent) + "\n"
        result += self.condition.pretty(indent + 1) + "\n"
        
        for stmt in self.then_block:
            result += stmt.pretty(indent + 1) + "\n"
            
        if self.else_block:
            for stmt in self.else_block:
                result += stmt.pretty(indent + 1) + "\n"
                
        return result.rstrip()


class ForNode(StatementNode):
    """Цикл for: для <переменная> от <начало> до <конец> [шаг <шаг>] <блок> кц"""
    
    def __init__(self, var: str, start: 'ExpressionNode', end: 'ExpressionNode',
                 step: Optional['ExpressionNode'] = None, body: List[StatementNode] = None,
                 meta: Optional[SourcePosition] = None):
        super().__init__(meta)
        self.var = var
        self.start = start
        self.end = end
        self.step = step
        self.body = body or []
    
    def pretty(self, indent: int = 0) -> str:
        result = super().pretty(indent) + f"({self.var})\n"
        result += self.start.pretty(indent + 1) + "\n"
        result += self.end.pretty(indent + 1) + "\n"
        
        if self.step:
            result += self.step.pretty(indent + 1) + "\n"
            
        for stmt in self.body:
            result += stmt.pretty(indent + 1) + "\n"
            
        return result.rstrip()


class WhileNode(StatementNode):
    """Цикл while: пока <условие> <блок> кц"""
    
    def __init__(self, condition: 'ExpressionNode', body: List[StatementNode],
                 meta: Optional[SourcePosition] = None):
        super().__init__(meta)
        self.condition = condition
        self.body = body
    
    def pretty(self, indent: int = 0) -> str:
        result = super().pretty(indent) + "\n"
        result += self.condition.pretty(indent + 1) + "\n"
        
        for stmt in self.body:
            result += stmt.pretty(indent + 1) + "\n"
            
        return result.rstrip()


class DoWhileNode(StatementNode):
    """Цикл do-while: цикл <блок> пока <условие>"""
    
    def __init__(self, body: List[StatementNode], condition: 'ExpressionNode',
                 meta: Optional[SourcePosition] = None):
        super().__init__(meta)
        self.body = body
        self.condition = condition
    
    def pretty(self, indent: int = 0) -> str:
        result = super().pretty(indent) + "\n"
        
        for stmt in self.body:
            result += stmt.pretty(indent + 1) + "\n"
            
        result += self.condition.pretty(indent + 1)
        return result


class BreakNode(StatementNode):
    """Оператор прерывания цикла: стоп"""
    
    def pretty(self, indent: int = 0) -> str:
        return super().pretty(indent)


class ContinueNode(StatementNode):
    """Оператор продолжения цикла: далее"""
    
    def pretty(self, indent: int = 0) -> str:
        return super().pretty(indent)


class ReturnNode(StatementNode):
    """Оператор возврата: знач <выражение>"""
    
    def __init__(self, value: Optional['ExpressionNode'] = None,
                 meta: Optional[SourcePosition] = None):
        super().__init__(meta)
        self.value = value
    
    def pretty(self, indent: int = 0) -> str:
        result = super().pretty(indent)
        if self.value:
            result += "\n" + self.value.pretty(indent + 1)
        return result


class CallStmtNode(StatementNode):
    """Вызов процедуры как оператор"""
    
    def __init__(self, call: 'CallNode', meta: Optional[SourcePosition] = None):
        super().__init__(meta)
        self.call = call
    
    def pretty(self, indent: int = 0) -> str:
        result = super().pretty(indent) + "\n"
        result += self.call.pretty(indent + 1)
        return result


# ============ Выражения ============

class ExpressionNode(Node):
    """Базовый класс для выражений"""
    pass


class BinOpNode(ExpressionNode):
    """Бинарная операция: <левый> <оператор> <правый>"""
    
    def __init__(self, left: ExpressionNode, op: str, right: ExpressionNode,
                 meta: Optional[SourcePosition] = None):
        super().__init__(meta)
        self.left = left
        self.op = op
        self.right = right
    
    def pretty(self, indent: int = 0) -> str:
        result = super().pretty(indent) + f"({self.op})\n"
        result += self.left.pretty(indent + 1) + "\n"
        result += self.right.pretty(indent + 1)
        return result


class UnaryOpNode(ExpressionNode):
    """Унарная операция: <оператор> <операнд>"""
    
    def __init__(self, op: str, operand: ExpressionNode,
                 meta: Optional[SourcePosition] = None):
        super().__init__(meta)
        self.op = op
        self.operand = operand
    
    def pretty(self, indent: int = 0) -> str:
        result = super().pretty(indent) + f"({self.op})\n"
        result += self.operand.pretty(indent + 1)
        return result


class IdentifierNode(ExpressionNode):
    """Идентификатор (переменная)"""
    
    def __init__(self, name: str, meta: Optional[SourcePosition] = None):
        super().__init__(meta)
        self.name = name
    
    def pretty(self, indent: int = 0) -> str:
        return super().pretty(indent) + f"({self.name})"


class ArrayAccessNode(ExpressionNode):
    """Доступ к элементу массива: <массив>[<индекс>]"""
    
    def __init__(self, array: ExpressionNode, index: ExpressionNode,
                 meta: Optional[SourcePosition] = None):
        super().__init__(meta)
        self.array = array
        self.index = index
    
    def pretty(self, indent: int = 0) -> str:
        result = super().pretty(indent) + "\n"
        result += self.array.pretty(indent + 1) + "\n"
        result += self.index.pretty(indent + 1)
        return result


class CallNode(ExpressionNode):
    """Вызов функции: <имя>(<аргументы>)"""
    
    def __init__(self, name: str, args: List[ExpressionNode],
                 meta: Optional[SourcePosition] = None):
        super().__init__(meta)
        self.name = name
        self.args = args
    
    def pretty(self, indent: int = 0) -> str:
        result = super().pretty(indent) + f"({self.name})"
        
        if self.args:
            result += "\n"
            for arg in self.args:
                result += arg.pretty(indent + 1) + "\n"
            return result.rstrip()
        
        return result


# ============ Литералы ============

class IntLiteralNode(ExpressionNode):
    """Целочисленный литерал"""
    
    def __init__(self, value: int, meta: Optional[SourcePosition] = None):
        super().__init__(meta)
        self.value = value
    
    def pretty(self, indent: int = 0) -> str:
        return super().pretty(indent) + f"({self.value})"


class BoolLiteralNode(ExpressionNode):
    """Логический литерал: да/нет"""
    
    def __init__(self, value: bool, meta: Optional[SourcePosition] = None):
        super().__init__(meta)
        self.value = value
    
    def pretty(self, indent: int = 0) -> str:
        return super().pretty(indent) + f"({self.value})"


class CharLiteralNode(ExpressionNode):
    """Символьный литерал"""
    
    def __init__(self, value: str, meta: Optional[SourcePosition] = None):
        super().__init__(meta)
        self.value = value
    
    def pretty(self, indent: int = 0) -> str:
        return super().pretty(indent) + f"('{self.value}')"


class StringLiteralNode(ExpressionNode):
    """Строковый литерал (для вывода)"""
    
    def __init__(self, value: str, meta: Optional[SourcePosition] = None):
        super().__init__(meta)
        self.value = value
    
    def pretty(self, indent: int = 0) -> str:
        return super().pretty(indent) + f'("{self.value}")'


# Экспорт всех узлов
__all__ = [
    'Node', 'SourcePosition',
    'ProgramNode', 'BlockNode',
    'VarDeclNode', 'FuncDeclNode', 'ParamNode',
    'TypeNode', 'SimpleTypeNode', 'ArrayTypeNode',
    'StatementNode', 'AssignNode', 'IfNode', 'ForNode', 'WhileNode', 'DoWhileNode',
    'BreakNode', 'ContinueNode', 'ReturnNode', 'CallStmtNode',
    'ExpressionNode', 'BinOpNode', 'UnaryOpNode', 'IdentifierNode', 'ArrayAccessNode', 'CallNode',
    'IntLiteralNode', 'BoolLiteralNode', 'CharLiteralNode', 'StringLiteralNode'
]
