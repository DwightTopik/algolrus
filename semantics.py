
from typing import Optional, List, Dict, Any
from mel_ast import *
from mel_types import *
from scope import *


class SemanticAnalyzer:

    def __init__(self):
        self.scope_manager = create_scope_manager_with_builtins()
        self.errors: List[SemanticError] = []
        self.current_function: Optional[FuncDeclNode] = None

    def analyze(self, ast: ProgramNode) -> List[SemanticError]:
        self.errors = []
        try:
            self.visit_program(ast)
        except Exception as e:

            if not isinstance(e, SemanticError):
                self.errors.append(SemanticError(f"Внутренняя ошибка анализатора: {e}"))

        return self.errors

    def add_error(self, message: str, position: Optional[SourcePosition] = None):
        self.errors.append(SemanticError(message, position))



    def visit_program(self, node: ProgramNode):

        self.scope_manager.enter_scope(f"program_{node.name}")

        try:
            self.visit_block(node.block)
            node.type = VOID
        finally:
            self.scope_manager.exit_scope()

    def visit_block(self, node: BlockNode):


        for var_decl in node.var_decls:
            self.visit_var_decl(var_decl)


        for func_decl in node.func_decls:
            self.declare_function_signature(func_decl)


        for func_decl in node.func_decls:
            self.visit_func_decl(func_decl)


        for stmt in node.statements:
            self.visit_statement(stmt)

    def visit_var_decl(self, node: VarDeclNode):

        var_type = self.visit_type(node.var_type)
        if var_type is None:
            self.add_error(f"Неизвестный тип для переменной '{node.name}'", node.meta)
            return


        symbol = Symbol(
            name=node.name,
            symbol_type=var_type,
            category='var',
            position=node.meta,
            is_global=self.scope_manager.is_in_global_scope()
        )

        try:
            self.scope_manager.declare(node.name, symbol)
            node.type = var_type
        except SemanticError as e:
            self.add_error(e.message, node.meta)

    def declare_function_signature(self, node: FuncDeclNode):

        param_types = []
        for param in node.params:
            param_type = self.visit_type(param.param_type)
            if param_type is None:
                self.add_error(f"Неизвестный тип параметра '{param.name}'", param.meta)
                return
            param_types.append(param_type)


        return_type = None
        if node.return_type:
            return_type = self.visit_type(node.return_type)
            if return_type is None:
                self.add_error(f"Неизвестный тип возврата функции '{node.name}'", node.meta)
                return


        func_type = FunctionType(param_types, return_type)


        symbol = Symbol(
            name=node.name,
            symbol_type=func_type,
            category='func',
            position=node.meta,
            is_global=True
        )

        try:
            self.scope_manager.declare(node.name, symbol)
            node.type = func_type
        except SemanticError as e:
            self.add_error(e.message, node.meta)

    def visit_func_decl(self, node: FuncDeclNode):

        old_function = self.current_function
        self.current_function = node

        self.scope_manager.enter_scope(f"function_{node.name}")

        try:

            for param in node.params:
                param_type = self.visit_type(param.param_type)
                if param_type:
                    symbol = Symbol(
                        name=param.name,
                        symbol_type=param_type,
                        category='param',
                        position=param.meta
                    )
                    try:
                        self.scope_manager.declare(param.name, symbol)
                        param.type = param_type
                    except SemanticError as e:
                        self.add_error(e.message, param.meta)


            self.visit_block(node.block)


            if node.return_type and not self.has_return_statement(node.block):
                self.add_error(f"Функция '{node.name}' должна содержать оператор 'знач'", node.meta)

        finally:
            self.scope_manager.exit_scope()
            self.current_function = old_function

    def has_return_statement(self, block: BlockNode) -> bool:
        for stmt in block.statements:
            if isinstance(stmt, ReturnNode):
                return True

        return False

    def visit_type(self, node: TypeNode) -> Optional[Type]:
        if isinstance(node, SimpleTypeNode):
            return type_from_string(node.name)
        elif isinstance(node, ArrayTypeNode):
            element_type = self.visit_type(node.element_type)
            if element_type is None:
                return None


            size_value = None
            if isinstance(node.size, IntLiteralNode):
                size_value = node.size.value
                if size_value <= 0:
                    self.add_error(f"Размер массива должен быть положительным числом", node.meta)
                    return None
            else:
                self.add_error(f"Размер массива должен быть константой", node.meta)
                return None

            return ArrayType(element_type, size_value)

        return None



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
            self.visit_break(node)
        elif isinstance(node, ContinueNode):
            self.visit_continue(node)
        elif isinstance(node, ReturnNode):
            self.visit_return(node)
        elif isinstance(node, CallStmtNode):
            self.visit_call_stmt(node)
        else:
            self.add_error(f"Неизвестный тип оператора: {type(node)}", getattr(node, 'meta', None))

    def visit_assign(self, node: AssignNode):

        target_type = self.visit_expression(node.target)


        value_type = self.visit_expression(node.value)


        if target_type and value_type:
            if not is_assignable(value_type, target_type):
                self.add_error(
                    f"Несовместимые типы: нельзя присвоить {value_type} переменной типа {target_type}",
                    node.meta
                )

        node.type = VOID

    def visit_if(self, node: IfNode):

        condition_type = self.visit_expression(node.condition)
        if condition_type and condition_type != BOOLEAN:
            self.add_error(f"Условие должно быть логического типа, получен {condition_type}", node.meta)


        for stmt in node.then_block:
            self.visit_statement(stmt)

        if node.else_block:
            for stmt in node.else_block:
                self.visit_statement(stmt)

        node.type = VOID

    def visit_for(self, node: ForNode):

        try:
            var_symbol = self.scope_manager.resolve(node.var, node.meta)
            if var_symbol.symbol_type != INTEGER:
                self.add_error(f"Переменная цикла '{node.var}' должна быть целого типа", node.meta)
        except SemanticError as e:
            self.add_error(e.message, node.meta)


        start_type = self.visit_expression(node.start)
        end_type = self.visit_expression(node.end)

        if start_type and start_type != INTEGER:
            self.add_error(f"Начальное значение цикла должно быть целого типа", node.meta)
        if end_type and end_type != INTEGER:
            self.add_error(f"Конечное значение цикла должно быть целого типа", node.meta)


        if node.step:
            step_type = self.visit_expression(node.step)
            if step_type and step_type != INTEGER:
                self.add_error(f"Шаг цикла должен быть целого типа", node.meta)


        for stmt in node.body:
            self.visit_statement(stmt)

        node.type = VOID

    def visit_while(self, node: WhileNode):

        condition_type = self.visit_expression(node.condition)
        if condition_type and condition_type != BOOLEAN:
            self.add_error(f"Условие цикла должно быть логического типа", node.meta)


        for stmt in node.body:
            self.visit_statement(stmt)

        node.type = VOID

    def visit_do_while(self, node: DoWhileNode):

        for stmt in node.body:
            self.visit_statement(stmt)


        condition_type = self.visit_expression(node.condition)
        if condition_type and condition_type != BOOLEAN:
            self.add_error(f"Условие цикла должно быть логического типа", node.meta)

        node.type = VOID

    def visit_break(self, node: BreakNode):

        node.type = VOID

    def visit_continue(self, node: ContinueNode):

        node.type = VOID

    def visit_return(self, node: ReturnNode):
        if not self.current_function:
            self.add_error("Оператор 'знач' может использоваться только внутри функции", node.meta)
            return


        expected_type = self.current_function.return_type
        if expected_type is None:
            expected_type = VOID
        else:
            expected_type = self.visit_type(expected_type)

        if node.value:

            actual_type = self.visit_expression(node.value)
            if actual_type and expected_type:
                if expected_type == VOID:
                    self.add_error("Процедура не может возвращать значение", node.meta)
                elif not is_assignable(actual_type, expected_type):
                    self.add_error(
                        f"Несовместимый тип возврата: ожидается {expected_type}, получен {actual_type}",
                        node.meta
                    )
        else:

            if expected_type and expected_type != VOID:
                self.add_error(f"Функция должна возвращать значение типа {expected_type}", node.meta)

        node.type = VOID

    def visit_call_stmt(self, node: CallStmtNode):
        call_type = self.visit_call_expr(node.call)


        if call_type and call_type != VOID:
            self.add_error("Результат функции не используется", node.meta)

        node.type = VOID



    def visit_expression(self, node: ExpressionNode) -> Optional[Type]:
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
            return self.visit_int_literal(node)
        elif isinstance(node, BoolLiteralNode):
            return self.visit_bool_literal(node)
        elif isinstance(node, CharLiteralNode):
            return self.visit_char_literal(node)
        elif isinstance(node, StringLiteralNode):
            return self.visit_string_literal(node)
        else:
            self.add_error(f"Неизвестный тип выражения: {type(node)}", getattr(node, 'meta', None))
            return None

    def visit_bin_op(self, node: BinOpNode) -> Optional[Type]:
        left_type = self.visit_expression(node.left)
        right_type = self.visit_expression(node.right)

        if left_type is None or right_type is None:
            return None

        result_type = get_binary_op_result_type(node.op, left_type, right_type)
        if result_type is None:
            self.add_error(
                f"Недопустимая операция '{node.op}' для типов {left_type} и {right_type}",
                node.meta
            )
            return None

        node.type = result_type
        return result_type

    def visit_unary_op(self, node: UnaryOpNode) -> Optional[Type]:
        operand_type = self.visit_expression(node.operand)

        if operand_type is None:
            return None

        result_type = get_unary_op_result_type(node.op, operand_type)
        if result_type is None:
            self.add_error(
                f"Недопустимая унарная операция '{node.op}' для типа {operand_type}",
                node.meta
            )
            return None

        node.type = result_type
        return result_type

    def visit_identifier(self, node: IdentifierNode) -> Optional[Type]:
        try:
            symbol = self.scope_manager.resolve(node.name, node.meta)
            node.type = symbol.symbol_type
            return symbol.symbol_type
        except SemanticError as e:
            self.add_error(e.message, node.meta)
            return None

    def visit_array_access(self, node: ArrayAccessNode) -> Optional[Type]:
        array_type = self.visit_expression(node.array)
        index_type = self.visit_expression(node.index)


        if index_type and index_type != INTEGER:
            self.add_error(f"Индекс массива должен быть целого типа", node.meta)


        if array_type:
            if not isinstance(array_type, ArrayType):
                self.add_error(f"Попытка индексации не-массива", node.meta)
                return None

            node.type = array_type.element_type
            return array_type.element_type

        return None

    def visit_call_expr(self, node: CallNode) -> Optional[Type]:

        if node.name == "вывод":
            if len(node.args) != 1:
                self.add_error(f"Функция 'вывод' ожидает 1 аргумент, получено {len(node.args)}", node.meta)
                return None


            self.visit_expression(node.args[0])
            node.type = VOID
            return VOID

        try:
            symbol = self.scope_manager.resolve(node.name, node.meta)

            if not isinstance(symbol.symbol_type, FunctionType):
                self.add_error(f"'{node.name}' не является функцией", node.meta)
                return None

            func_type = symbol.symbol_type


            if len(node.args) != len(func_type.param_types):
                self.add_error(
                    f"Функция '{node.name}' ожидает {len(func_type.param_types)} аргументов, получено {len(node.args)}",
                    node.meta
                )
                return None


            for i, (arg, expected_type) in enumerate(zip(node.args, func_type.param_types)):
                actual_type = self.visit_expression(arg)
                if actual_type and not is_assignable(actual_type, expected_type):
                    self.add_error(
                        f"Аргумент {i+1} функции '{node.name}': ожидается {expected_type}, получен {actual_type}",
                        node.meta
                    )


            return_type = func_type.return_type or VOID
            node.type = return_type
            return return_type

        except SemanticError as e:
            self.add_error(e.message, node.meta)
            return None



    def visit_int_literal(self, node: IntLiteralNode) -> Type:
        node.type = INTEGER
        node.const_value = node.value
        return INTEGER

    def visit_bool_literal(self, node: BoolLiteralNode) -> Type:
        node.type = BOOLEAN
        node.const_value = node.value
        return BOOLEAN

    def visit_char_literal(self, node: CharLiteralNode) -> Type:
        node.type = CHAR
        node.const_value = node.value
        return CHAR

    def visit_string_literal(self, node: StringLiteralNode) -> Type:
        node.type = STRING
        node.const_value = node.value
        return STRING


def analyze(ast: ProgramNode) -> List[SemanticError]:
    analyzer = SemanticAnalyzer()
    return analyzer.analyze(ast)


def check_semantics(ast: ProgramNode) -> bool:
    errors = analyze(ast)
    if errors:
        for error in errors:
            print(f"Семантическая ошибка: {error}")
        return False
    return True



__all__ = ['SemanticAnalyzer', 'analyze', 'check_semantics']
