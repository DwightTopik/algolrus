"""
Интерпретатор для русскоязычного Pascal
Выполняет программы напрямую по AST без генерации промежуточного кода
"""

import sys
from typing import Any, Dict, List, Optional, Union
from mel_ast import *
from mel_types import *
from semantics import analyze


class InterpreterError(Exception):
    """Исключение времени выполнения интерпретатора"""
    def __init__(self, message: str, position: Optional[SourcePosition] = None):
        self.message = message
        self.position = position
        super().__init__(self.format_message())
    
    def format_message(self) -> str:
        if self.position:
            return f"Ошибка выполнения на {self.position}: {self.message}"
        return f"Ошибка выполнения: {self.message}"


class BreakException(Exception):
    """Исключение для оператора break"""
    pass


class ContinueException(Exception):
    """Исключение для оператора continue"""
    pass


class ReturnException(Exception):
    """Исключение для оператора return"""
    def __init__(self, value: Any = None):
        self.value = value


class Environment:
    """Окружение выполнения - хранит переменные и их значения"""
    
    def __init__(self, parent: Optional['Environment'] = None):
        self.parent = parent
        self.variables: Dict[str, Any] = {}
    
    def define(self, name: str, value: Any):
        """Определяет переменную в текущем окружении"""
        self.variables[name] = value
    
    def get(self, name: str) -> Any:
        """Получает значение переменной"""
        if name in self.variables:
            return self.variables[name]
        if self.parent:
            return self.parent.get(name)
        raise InterpreterError(f"Неопределенная переменная '{name}'")
    
    def set(self, name: str, value: Any):
        """Устанавливает значение переменной"""
        if name in self.variables:
            self.variables[name] = value
            return
        if self.parent:
            try:
                self.parent.set(name, value)
                return
            except InterpreterError:
                pass
        raise InterpreterError(f"Неопределенная переменная '{name}'")
    
    def has(self, name: str) -> bool:
        """Проверяет, существует ли переменная"""
        if name in self.variables:
            return True
        if self.parent:
            return self.parent.has(name)
        return False


class Interpreter:
    """Интерпретатор - выполняет программы по AST"""
    
    def __init__(self):
        self.global_env = Environment()
        self.current_env = self.global_env
        self.functions: Dict[str, FuncDeclNode] = {}
        self.output_buffer: List[str] = []  # Для тестирования
    
    def interpret(self, ast: ProgramNode) -> List[str]:
        """Главный метод интерпретации"""
        # Сначала проводим семантический анализ
        errors = analyze(ast)
        if errors:
            error_messages = [str(error) for error in errors]
            raise InterpreterError(f"Семантические ошибки:\n" + "\n".join(error_messages))
        
        # Выполняем программу
        self.output_buffer = []
        try:
            self.visit_program(ast)
        except ReturnException:
            # Возврат из главной программы игнорируется
            pass
        
        return self.output_buffer
    
    def print_output(self, text: str):
        """Выводит текст (для тестирования сохраняет в буфер)"""
        self.output_buffer.append(text)
        print(text, end='')
    
    # ============ Посетители узлов AST ============
    
    def visit_program(self, node: ProgramNode):
        """Выполнение программы"""
        self.visit_block(node.block)
    
    def visit_block(self, node: BlockNode):
        """Выполнение блока"""
        # Создаем новое окружение для блока
        old_env = self.current_env
        self.current_env = Environment(parent=old_env)
        
        try:
            # 1. Объявляем переменные
            for var_decl in node.var_decls:
                self.visit_var_decl(var_decl)
            
            # 2. Регистрируем функции
            for func_decl in node.func_decls:
                self.functions[func_decl.name] = func_decl
            
            # 3. Выполняем операторы
            for stmt in node.statements:
                self.visit_statement(stmt)
        
        finally:
            # Восстанавливаем окружение
            self.current_env = old_env
    
    def visit_var_decl(self, node: VarDeclNode):
        """Объявление переменной"""
        # Получаем значение по умолчанию для типа
        var_type = self.get_type_from_node(node.var_type)
        default_value = get_default_value(var_type)
        self.current_env.define(node.name, default_value)
    
    def get_type_from_node(self, type_node: TypeNode) -> Type:
        """Преобразует узел типа в объект Type"""
        if isinstance(type_node, SimpleTypeNode):
            return type_from_string(type_node.name)
        elif isinstance(type_node, ArrayTypeNode):
            element_type = self.get_type_from_node(type_node.element_type)
            size = self.visit_expression(type_node.size)
            return ArrayType(element_type, size)
        else:
            raise InterpreterError(f"Неизвестный тип: {type(type_node)}")
    
    # ============ Операторы ============
    
    def visit_statement(self, node: StatementNode):
        """Выполнение оператора"""
        if isinstance(node, AssignNode):
            self.visit_assign(node)
        elif isinstance(node, IfNode):
            self.visit_if(node)
        elif isinstance(node, ForNode):
            self.visit_for(node)
        elif isinstance(node, WhileNode):
            self.visit_while(node)
        elif isinstance(node, DoWhileNode):
            self.visit_do_while(node)
        elif isinstance(node, BreakNode):
            raise BreakException()
        elif isinstance(node, ContinueNode):
            raise ContinueException()
        elif isinstance(node, ReturnNode):
            self.visit_return(node)
        elif isinstance(node, CallStmtNode):
            self.visit_call_stmt(node)
        else:
            raise InterpreterError(f"Неизвестный тип оператора: {type(node)}")
    
    def visit_assign(self, node: AssignNode):
        """Выполнение присваивания"""
        value = self.visit_expression(node.value)
        
        if isinstance(node.target, IdentifierNode):
            # Простое присваивание переменной
            self.current_env.set(node.target.name, value)
        elif isinstance(node.target, ArrayAccessNode):
            # Присваивание элементу массива
            array_name = node.target.array.name
            index = self.visit_expression(node.target.index)
            array = self.current_env.get(array_name)
            
            if not isinstance(array, list):
                raise InterpreterError(f"'{array_name}' не является массивом")
            
            # Проверяем границы массива (индексы с 1)
            if index < 1 or index > len(array):
                raise InterpreterError(f"Индекс {index} выходит за границы массива")
            
            array[index - 1] = value  # Преобразуем в 0-based индекс
        else:
            raise InterpreterError(f"Недопустимая левая часть присваивания: {type(node.target)}")
    
    def visit_if(self, node: IfNode):
        """Выполнение условного оператора"""
        condition = self.visit_expression(node.condition)
        
        if self.is_truthy(condition):
            for stmt in node.then_block:
                self.visit_statement(stmt)
        elif node.else_block:
            for stmt in node.else_block:
                self.visit_statement(stmt)
    
    def visit_for(self, node: ForNode):
        """Выполнение цикла for"""
        start_value = self.visit_expression(node.start)
        end_value = self.visit_expression(node.end)
        step_value = 1
        
        if node.step:
            step_value = self.visit_expression(node.step)
        
        # Устанавливаем начальное значение переменной цикла
        self.current_env.set(node.var, start_value)
        
        try:
            if step_value > 0:
                # Прямой цикл
                while self.current_env.get(node.var) <= end_value:
                    try:
                        for stmt in node.body:
                            self.visit_statement(stmt)
                    except ContinueException:
                        pass  # Продолжаем цикл
                    
                    # Увеличиваем переменную цикла
                    current_val = self.current_env.get(node.var)
                    self.current_env.set(node.var, current_val + step_value)
            else:
                # Обратный цикл
                while self.current_env.get(node.var) >= end_value:
                    try:
                        for stmt in node.body:
                            self.visit_statement(stmt)
                    except ContinueException:
                        pass  # Продолжаем цикл
                    
                    # Изменяем переменную цикла
                    current_val = self.current_env.get(node.var)
                    self.current_env.set(node.var, current_val + step_value)
        
        except BreakException:
            pass  # Выходим из цикла
    
    def visit_while(self, node: WhileNode):
        """Выполнение цикла while"""
        try:
            while self.is_truthy(self.visit_expression(node.condition)):
                try:
                    for stmt in node.body:
                        self.visit_statement(stmt)
                except ContinueException:
                    continue  # Продолжаем цикл
        except BreakException:
            pass  # Выходим из цикла
    
    def visit_do_while(self, node: DoWhileNode):
        """Выполнение цикла do-while"""
        try:
            while True:
                try:
                    for stmt in node.body:
                        self.visit_statement(stmt)
                except ContinueException:
                    pass  # Продолжаем к проверке условия
                
                # Проверяем условие выхода
                if not self.is_truthy(self.visit_expression(node.condition)):
                    break
        except BreakException:
            pass  # Выходим из цикла
    
    def visit_return(self, node: ReturnNode):
        """Выполнение оператора return"""
        value = None
        if node.value:
            value = self.visit_expression(node.value)
        raise ReturnException(value)
    
    def visit_call_stmt(self, node: CallStmtNode):
        """Выполнение вызова процедуры"""
        self.visit_call_expr(node.call)
    
    # ============ Выражения ============
    
    def visit_expression(self, node: ExpressionNode) -> Any:
        """Вычисление выражения"""
        if isinstance(node, BinOpNode):
            return self.visit_bin_op(node)
        elif isinstance(node, UnaryOpNode):
            return self.visit_unary_op(node)
        elif isinstance(node, IdentifierNode):
            return self.visit_identifier(node)
        elif isinstance(node, ArrayAccessNode):
            return self.visit_array_access(node)
        elif isinstance(node, CallNode):
            return self.visit_call_expr(node)
        elif isinstance(node, IntLiteralNode):
            return node.value
        elif isinstance(node, BoolLiteralNode):
            return node.value
        elif isinstance(node, CharLiteralNode):
            return node.value
        elif isinstance(node, StringLiteralNode):
            return node.value
        else:
            raise InterpreterError(f"Неизвестный тип выражения: {type(node)}")
    
    def visit_bin_op(self, node: BinOpNode) -> Any:
        """Вычисление бинарной операции"""
        left = self.visit_expression(node.left)
        
        # Ленивое вычисление для логических операций
        if node.op == "и":
            if not self.is_truthy(left):
                return False
            right = self.visit_expression(node.right)
            return self.is_truthy(right)
        elif node.op == "или":
            if self.is_truthy(left):
                return True
            right = self.visit_expression(node.right)
            return self.is_truthy(right)
        
        # Для остальных операций вычисляем правую часть
        right = self.visit_expression(node.right)
        
        # Арифметические операции
        if node.op == "+":
            return left + right
        elif node.op == "-":
            return left - right
        elif node.op == "*":
            return left * right
        elif node.op == "/":
            if right == 0:
                raise InterpreterError("Деление на ноль")
            return left // right  # Целочисленное деление
        elif node.op == "div":
            if right == 0:
                raise InterpreterError("Деление на ноль")
            return left // right
        elif node.op == "mod":
            if right == 0:
                raise InterpreterError("Деление на ноль")
            return left % right
        
        # Операции сравнения
        elif node.op == "=":
            return left == right
        elif node.op == "<>":
            return left != right
        elif node.op == ">":
            return left > right
        elif node.op == ">=":
            return left >= right
        elif node.op == "<":
            return left < right
        elif node.op == "<=":
            return left <= right
        
        else:
            raise InterpreterError(f"Неизвестная бинарная операция: {node.op}")
    
    def visit_unary_op(self, node: UnaryOpNode) -> Any:
        """Вычисление унарной операции"""
        operand = self.visit_expression(node.operand)
        
        if node.op == "+":
            return +operand
        elif node.op == "-":
            return -operand
        elif node.op == "не":
            return not self.is_truthy(operand)
        else:
            raise InterpreterError(f"Неизвестная унарная операция: {node.op}")
    
    def visit_identifier(self, node: IdentifierNode) -> Any:
        """Получение значения переменной"""
        return self.current_env.get(node.name)
    
    def visit_array_access(self, node: ArrayAccessNode) -> Any:
        """Доступ к элементу массива"""
        array_name = node.array.name
        index = self.visit_expression(node.index)
        array = self.current_env.get(array_name)
        
        if not isinstance(array, list):
            raise InterpreterError(f"'{array_name}' не является массивом")
        
        # Проверяем границы массива (индексы с 1)
        if index < 1 or index > len(array):
            raise InterpreterError(f"Индекс {index} выходит за границы массива")
        
        return array[index - 1]  # Преобразуем в 0-based индекс
    
    def visit_call_expr(self, node: CallNode) -> Any:
        """Вызов функции"""
        # Проверяем встроенные функции
        if node.name in BUILTIN_FUNCTIONS:
            return self.call_builtin_function(node.name, node.args)
        
        # Пользовательская функция
        if node.name not in self.functions:
            raise InterpreterError(f"Неопределенная функция '{node.name}'")
        
        func_decl = self.functions[node.name]
        
        # Проверяем количество аргументов
        if len(node.args) != len(func_decl.params):
            raise InterpreterError(f"Функция '{node.name}' ожидает {len(func_decl.params)} аргументов, получено {len(node.args)}")
        
        # Создаем новое окружение для функции
        old_env = self.current_env
        self.current_env = Environment(parent=self.global_env)
        
        try:
            # Связываем параметры с аргументами
            for param, arg in zip(func_decl.params, node.args):
                arg_value = self.visit_expression(arg)
                self.current_env.define(param.name, arg_value)
            
            # Выполняем тело функции
            self.visit_block(func_decl.block)
            
            # Если функция не вернула значение, возвращаем None (для процедур)
            return None
        
        except ReturnException as ret:
            return ret.value
        
        finally:
            self.current_env = old_env
    
    def call_builtin_function(self, name: str, args: List[ExpressionNode]) -> Any:
        """Вызов встроенной функции"""
        if name == "вывод":
            if len(args) != 1:
                raise InterpreterError("Функция 'вывод' принимает 1 аргумент")
            value = self.visit_expression(args[0])
            self.print_output(str(value) + "\n")
            return None
        
        elif name == "увел":
            if len(args) != 1:
                raise InterpreterError("Функция 'увел' принимает 1 аргумент")
            if not isinstance(args[0], IdentifierNode):
                raise InterpreterError("Функция 'увел' требует переменную")
            var_name = args[0].name
            current_value = self.current_env.get(var_name)
            self.current_env.set(var_name, current_value + 1)
            return None
        
        elif name == "умен":
            if len(args) != 1:
                raise InterpreterError("Функция 'умен' принимает 1 аргумент")
            if not isinstance(args[0], IdentifierNode):
                raise InterpreterError("Функция 'умен' требует переменную")
            var_name = args[0].name
            current_value = self.current_env.get(var_name)
            self.current_env.set(var_name, current_value - 1)
            return None
        
        elif name == "модуль":
            if len(args) != 1:
                raise InterpreterError("Функция 'модуль' принимает 1 аргумент")
            value = self.visit_expression(args[0])
            return abs(value)
        
        else:
            raise InterpreterError(f"Неизвестная встроенная функция: {name}")
    
    def is_truthy(self, value: Any) -> bool:
        """Проверяет, является ли значение истинным"""
        if isinstance(value, bool):
            return value
        elif isinstance(value, int):
            return value != 0
        elif value is None:
            return False
        else:
            return True


def interpret(ast: ProgramNode) -> List[str]:
    """Удобная функция для интерпретации программы"""
    interpreter = Interpreter()
    return interpreter.interpret(ast)


def run_program(ast: ProgramNode):
    """Запускает программу и выводит результат"""
    interpreter = Interpreter()
    try:
        interpreter.interpret(ast)
    except InterpreterError as e:
        print(f"Ошибка выполнения: {e}", file=sys.stderr)
        sys.exit(1)


# Экспорт
__all__ = ['Interpreter', 'InterpreterError', 'interpret', 'run_program']
