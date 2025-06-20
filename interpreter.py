import sys
from typing import Any, Dict, List, Optional, Union
from mel_ast import *
from mel_types import *
from semantics import analyze


class InterpreterError(Exception):
    def __init__(self, message: str, position: Optional[SourcePosition] = None):
        self.message = message
        self.position = position
        super().__init__(self.format_message())

    def format_message(self) -> str:
        if self.position:
            return f"Ошибка выполнения на {self.position}: {self.message}"
        return f"Ошибка выполнения: {self.message}"


class BreakException(Exception):
    pass


class ContinueException(Exception):
    pass


class ReturnException(Exception):
    def __init__(self, value: Any = None):
        self.value = value


class Environment:

    def __init__(self, parent: Optional['Environment'] = None):
        self.parent = parent
        self.variables: Dict[str, Any] = {}

    def define(self, name: str, value: Any):
        self.variables[name] = value

    def get(self, name: str) -> Any:
        if name in self.variables:
            return self.variables[name]
        if self.parent:
            return self.parent.get(name)
        raise InterpreterError(f"Неопределенная переменная '{name}'")

    def set(self, name: str, value: Any):
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
        if name in self.variables:
            return True
        if self.parent:
            return self.parent.has(name)
        return False


class Interpreter:

    def __init__(self):
        self.global_env = Environment()
        self.current_env = self.global_env
        self.functions: Dict[str, FuncDeclNode] = {}
        self.output_buffer: List[str] = []

    def interpret(self, ast: ProgramNode) -> List[str]:
        errors = analyze(ast)
        if errors:
            error_messages = [str(error) for error in errors]
            raise InterpreterError(f"Семантические ошибки:\n" + "\n".join(error_messages))

        self.output_buffer = []
        try:
            self.visit_program(ast)
        except ReturnException:
            pass

        return self.output_buffer

    def print_output(self, text: str):
        self.output_buffer.append(text)
        print(text, end='')


    def visit_program(self, node: ProgramNode):
        self.visit_block(node.block)

    def visit_block(self, node: BlockNode):
        old_env = self.current_env
        self.current_env = Environment(parent=old_env)

        try:
            for var_decl in node.var_decls:
                self.visit_var_decl(var_decl)

            for func_decl in node.func_decls:
                self.functions[func_decl.name] = func_decl

            for stmt in node.statements:
                self.visit_statement(stmt)

        finally:
            self.current_env = old_env

    def visit_var_decl(self, node: VarDeclNode):
        var_type = self.get_type_from_node(node.var_type)
        default_value = get_default_value(var_type)
        self.current_env.define(node.name, default_value)

    def get_type_from_node(self, type_node: TypeNode) -> Type:
        if isinstance(type_node, SimpleTypeNode):
            return type_from_string(type_node.name)
        elif isinstance(type_node, ArrayTypeNode):
            element_type = self.get_type_from_node(type_node.element_type)
            size = self.visit_expression(type_node.size)
            return ArrayType(element_type, size)
        else:
            raise InterpreterError(f"Неизвестный тип: {type(type_node)}")


    def visit_statement(self, node: StatementNode):
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
        value = self.visit_expression(node.value)

        if isinstance(node.target, IdentifierNode):
            self.current_env.set(node.target.name, value)
        elif isinstance(node.target, ArrayAccessNode):
            array_name = node.target.array.name
            index = self.visit_expression(node.target.index)
            array = self.current_env.get(array_name)

            if not isinstance(array, list):
                raise InterpreterError(f"'{array_name}' не является массивом")

            if index < 1 or index > len(array):
                raise InterpreterError(f"Индекс {index} выходит за границы массива")

            array[index - 1] = value
        else:
            raise InterpreterError(f"Недопустимая левая часть присваивания: {type(node.target)}")

    def visit_if(self, node: IfNode):
        condition = self.visit_expression(node.condition)

        if self.is_truthy(condition):
            for stmt in node.then_block:
                self.visit_statement(stmt)
        elif node.else_block:
            for stmt in node.else_block:
                self.visit_statement(stmt)

    def visit_for(self, node: ForNode):
        start_value = self.visit_expression(node.start)
        end_value = self.visit_expression(node.end)
        step_value = 1

        if node.step:
            step_value = self.visit_expression(node.step)

        self.current_env.set(node.var, start_value)

        try:
            if step_value > 0:
                while self.current_env.get(node.var) <= end_value:
                    try:
                        for stmt in node.body:
                            self.visit_statement(stmt)
                    except ContinueException:
                        pass


                    current_val = self.current_env.get(node.var)
                    self.current_env.set(node.var, current_val + step_value)
            else:
                while self.current_env.get(node.var) >= end_value:
                    try:
                        for stmt in node.body:
                            self.visit_statement(stmt)
                    except ContinueException:
                        pass

                    current_val = self.current_env.get(node.var)
                    self.current_env.set(node.var, current_val + step_value)

        except BreakException:
            pass

    def visit_while(self, node: WhileNode):
        try:
            while self.is_truthy(self.visit_expression(node.condition)):
                try:
                    for stmt in node.body:
                        self.visit_statement(stmt)
                except ContinueException:
                    continue
        except BreakException:
            pass

    def visit_do_while(self, node: DoWhileNode):
        try:
            while True:
                try:
                    for stmt in node.body:
                        self.visit_statement(stmt)
                except ContinueException:
                    pass


                if not self.is_truthy(self.visit_expression(node.condition)):
                    break
        except BreakException:
            pass

    def visit_return(self, node: ReturnNode):
        value = None
        if node.value:
            value = self.visit_expression(node.value)
        raise ReturnException(value)

    def visit_call_stmt(self, node: CallStmtNode):
        self.visit_call_expr(node.call)



    def visit_expression(self, node: ExpressionNode) -> Any:
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
        left = self.visit_expression(node.left)


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


        right = self.visit_expression(node.right)


        if node.op == "+":
            return left + right
        elif node.op == "-":
            return left - right
        elif node.op == "*":
            return left * right
        elif node.op == "/":
            if right == 0:
                raise InterpreterError("Деление на ноль")
            return left // right
        elif node.op == "div":
            if right == 0:
                raise InterpreterError("Деление на ноль")
            return left // right
        elif node.op == "mod":
            if right == 0:
                raise InterpreterError("Деление на ноль")
            return left % right


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
        return self.current_env.get(node.name)

    def visit_array_access(self, node: ArrayAccessNode) -> Any:
        array_name = node.array.name
        index = self.visit_expression(node.index)
        array = self.current_env.get(array_name)

        if not isinstance(array, list):
            raise InterpreterError(f"'{array_name}' не является массивом")


        if index < 1 or index > len(array):
            raise InterpreterError(f"Индекс {index} выходит за границы массива")

        return array[index - 1]

    def visit_call_expr(self, node: CallNode) -> Any:

        if node.name in BUILTIN_FUNCTIONS:
            return self.call_builtin_function(node.name, node.args)


        if node.name not in self.functions:
            raise InterpreterError(f"Неопределенная функция '{node.name}'")

        func_decl = self.functions[node.name]


        if len(node.args) != len(func_decl.params):
            raise InterpreterError(f"Функция '{node.name}' ожидает {len(func_decl.params)} аргументов, получено {len(node.args)}")


        old_env = self.current_env
        self.current_env = Environment(parent=old_env)

        try:

            for param, arg in zip(func_decl.params, node.args):
                arg_value = self.visit_expression(arg)
                self.current_env.define(param.name, arg_value)


            self.visit_block(func_decl.block)


            return None

        except ReturnException as ret:
            return ret.value

        finally:
            self.current_env = old_env

    def call_builtin_function(self, name: str, args: List[ExpressionNode]) -> Any:
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
        if isinstance(value, bool):
            return value
        elif isinstance(value, int):
            return value != 0
        elif value is None:
            return False
        else:
            return True


def interpret(ast: ProgramNode) -> List[str]:
    interpreter = Interpreter()
    return interpreter.interpret(ast)


def run_program(ast: ProgramNode):
    interpreter = Interpreter()
    try:
        interpreter.interpret(ast)
    except InterpreterError as e:
        print(f"Ошибка выполнения: {e}", file=sys.stderr)
        sys.exit(1)



__all__ = ['Interpreter', 'InterpreterError', 'interpret', 'run_program']
