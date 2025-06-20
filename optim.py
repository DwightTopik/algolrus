"""
Модуль оптимизаций для компилятора
Содержит различные проходы оптимизации AST и байт-кода
"""

from typing import List, Optional, Any, Union
from mel_ast import *
from mel_types import *


class OptimizationError(Exception):
    """Исключение оптимизации"""
    def __init__(self, message: str, position: Optional[SourcePosition] = None):
        self.message = message
        self.position = position
        super().__init__(self.format_message())
    
    def format_message(self) -> str:
        if self.position:
            return f"Ошибка оптимизации на {self.position}: {self.message}"
        return f"Ошибка оптимизации: {self.message}"


class ConstantFolder:
    """Оптимизатор для свертки константных выражений"""
    
    def __init__(self):
        self.optimizations_count = 0
    
    def optimize(self, ast: ProgramNode) -> ProgramNode:
        """Главный метод оптимизации - применяет свертку констант"""
        self.optimizations_count = 0
        optimized_ast = self.visit_program(ast)
        return optimized_ast
    
    def get_stats(self) -> dict:
        """Возвращает статистику оптимизаций"""
        return {
            "constant_folding": self.optimizations_count,
            "total": self.optimizations_count
        }
    
    # ============ Посетители узлов AST ============
    
    def visit_program(self, node: ProgramNode) -> ProgramNode:
        """Оптимизация программы"""
        optimized_block = self.visit_block(node.block)
        return ProgramNode(node.name, optimized_block, node.meta)
    
    def visit_block(self, node: BlockNode) -> BlockNode:
        """Оптимизация блока"""
        # Оптимизируем объявления переменных
        optimized_var_decls = []
        for var_decl in node.var_decls:
            optimized_var_decls.append(self.visit_var_decl(var_decl))
        
        # Оптимизируем функции
        optimized_func_decls = []
        for func_decl in node.func_decls:
            optimized_func_decls.append(self.visit_func_decl(func_decl))
        
        # Оптимизируем операторы
        optimized_statements = []
        for stmt in node.statements:
            optimized_stmt = self.visit_statement(stmt)
            if optimized_stmt:  # Может быть None если оператор удален
                optimized_statements.append(optimized_stmt)
        
        return BlockNode(
            var_decls=optimized_var_decls,
            func_decls=optimized_func_decls,
            statements=optimized_statements,
            meta=node.meta
        )
    
    def visit_var_decl(self, node: VarDeclNode) -> VarDeclNode:
        """Оптимизация объявления переменной"""
        # Пока ничего не оптимизируем в объявлениях
        return node
    
    def visit_func_decl(self, node: FuncDeclNode) -> FuncDeclNode:
        """Оптимизация функции"""
        optimized_block = self.visit_block(node.block)
        return FuncDeclNode(
            name=node.name,
            params=node.params,
            return_type=node.return_type,
            block=optimized_block,
            meta=node.meta
        )
    
    def visit_statement(self, node: StatementNode) -> Optional[StatementNode]:
        """Оптимизация оператора"""
        if isinstance(node, AssignNode):
            return self.visit_assign(node)
        elif isinstance(node, IfNode):
            return self.visit_if(node)
        elif isinstance(node, ForNode):
            return self.visit_for(node)
        elif isinstance(node, WhileNode):
            return self.visit_while(node)
        elif isinstance(node, DoWhileNode):
            return self.visit_do_while(node)
        elif isinstance(node, ReturnNode):
            return self.visit_return(node)
        elif isinstance(node, CallStmtNode):
            return self.visit_call_stmt(node)
        else:
            # Операторы break, continue не требуют оптимизации
            return node
    
    def visit_assign(self, node: AssignNode) -> AssignNode:
        """Оптимизация присваивания"""
        optimized_value = self.visit_expression(node.value)
        return AssignNode(node.target, optimized_value, node.meta)
    
    def visit_if(self, node: IfNode) -> Optional[StatementNode]:
        """Оптимизация условного оператора"""
        optimized_condition = self.visit_expression(node.condition)
        
        # Если условие - константа, можем убрать ветку
        if isinstance(optimized_condition, BoolLiteralNode):
            self.optimizations_count += 1
            if optimized_condition.value:
                # Условие всегда истинно - оставляем только then-ветку
                optimized_statements = []
                for stmt in node.then_block:
                    optimized_stmt = self.visit_statement(stmt)
                    if optimized_stmt:
                        optimized_statements.append(optimized_stmt)
                
                # Возвращаем составной оператор (блок)
                if len(optimized_statements) == 1:
                    return optimized_statements[0]
                elif len(optimized_statements) > 1:
                    # Создаем искусственный блок - можно обернуть в список операторов
                    return IfNode(
                        condition=BoolLiteralNode(True),
                        then_block=optimized_statements,
                        else_block=None,
                        meta=node.meta
                    )
                else:
                    return None  # Пустой блок - удаляем оператор
            else:
                # Условие всегда ложно - оставляем только else-ветку
                if node.else_block:
                    optimized_statements = []
                    for stmt in node.else_block:
                        optimized_stmt = self.visit_statement(stmt)
                        if optimized_stmt:
                            optimized_statements.append(optimized_stmt)
                    
                    if len(optimized_statements) == 1:
                        return optimized_statements[0]
                    elif len(optimized_statements) > 1:
                        return IfNode(
                            condition=BoolLiteralNode(True),
                            then_block=optimized_statements,
                            else_block=None,
                            meta=node.meta
                        )
                
                return None  # Удаляем весь if
        
        # Обычная оптимизация веток
        optimized_then = []
        for stmt in node.then_block:
            optimized_stmt = self.visit_statement(stmt)
            if optimized_stmt:
                optimized_then.append(optimized_stmt)
        
        optimized_else = None
        if node.else_block:
            optimized_else = []
            for stmt in node.else_block:
                optimized_stmt = self.visit_statement(stmt)
                if optimized_stmt:
                    optimized_else.append(optimized_stmt)
        
        return IfNode(
            condition=optimized_condition,
            then_block=optimized_then,
            else_block=optimized_else,
            meta=node.meta
        )
    
    def visit_for(self, node: ForNode) -> ForNode:
        """Оптимизация цикла for"""
        optimized_start = self.visit_expression(node.start)
        optimized_end = self.visit_expression(node.end)
        optimized_step = None
        if node.step:
            optimized_step = self.visit_expression(node.step)
        
        optimized_body = []
        for stmt in node.body:
            optimized_stmt = self.visit_statement(stmt)
            if optimized_stmt:
                optimized_body.append(optimized_stmt)
        
        return ForNode(
            var=node.var,
            start=optimized_start,
            end=optimized_end,
            step=optimized_step,
            body=optimized_body,
            meta=node.meta
        )
    
    def visit_while(self, node: WhileNode) -> Optional[WhileNode]:
        """Оптимизация цикла while"""
        optimized_condition = self.visit_expression(node.condition)
        
        # Если условие - константа false, удаляем цикл
        if isinstance(optimized_condition, BoolLiteralNode) and not optimized_condition.value:
            self.optimizations_count += 1
            return None
        
        optimized_body = []
        for stmt in node.body:
            optimized_stmt = self.visit_statement(stmt)
            if optimized_stmt:
                optimized_body.append(optimized_stmt)
        
        return WhileNode(
            condition=optimized_condition,
            body=optimized_body,
            meta=node.meta
        )
    
    def visit_do_while(self, node: DoWhileNode) -> DoWhileNode:
        """Оптимизация цикла do-while"""
        optimized_condition = self.visit_expression(node.condition)
        
        optimized_body = []
        for stmt in node.body:
            optimized_stmt = self.visit_statement(stmt)
            if optimized_stmt:
                optimized_body.append(optimized_stmt)
        
        return DoWhileNode(
            body=optimized_body,
            condition=optimized_condition,
            meta=node.meta
        )
    
    def visit_return(self, node: ReturnNode) -> ReturnNode:
        """Оптимизация return"""
        optimized_value = None
        if node.value:
            optimized_value = self.visit_expression(node.value)
        
        return ReturnNode(optimized_value, node.meta)
    
    def visit_call_stmt(self, node: CallStmtNode) -> CallStmtNode:
        """Оптимизация вызова процедуры"""
        optimized_call = self.visit_call_expr(node.call)
        return CallStmtNode(optimized_call, node.meta)
    
    # ============ Выражения ============
    
    def visit_expression(self, node: ExpressionNode) -> ExpressionNode:
        """Оптимизация выражения"""
        if isinstance(node, BinOpNode):
            return self.visit_bin_op(node)
        elif isinstance(node, UnaryOpNode):
            return self.visit_unary_op(node)
        elif isinstance(node, ArrayAccessNode):
            return self.visit_array_access(node)
        elif isinstance(node, CallNode):
            return self.visit_call_expr(node)
        else:
            # Литералы и идентификаторы не требуют оптимизации
            return node
    
    def visit_bin_op(self, node: BinOpNode) -> ExpressionNode:
        """Оптимизация бинарной операции - основная логика constant folding"""
        # Сначала оптимизируем операнды
        optimized_left = self.visit_expression(node.left)
        optimized_right = self.visit_expression(node.right)
        
        # Проверяем, являются ли оба операнда константами
        if self.is_constant(optimized_left) and self.is_constant(optimized_right):
            # Вычисляем константное выражение
            try:
                result = self.evaluate_constant_expression(node.op, optimized_left, optimized_right)
                if result is not None:
                    self.optimizations_count += 1
                    return result
            except Exception:
                # Если не удалось вычислить (например, деление на ноль), оставляем как есть
                pass
        
        # Специальные случаи оптимизации
        optimized = self.apply_algebraic_optimizations(node.op, optimized_left, optimized_right)
        if optimized:
            return optimized
        
        # Если оптимизация не применилась, возвращаем обновленный узел
        return BinOpNode(optimized_left, node.op, optimized_right, node.meta)
    
    def visit_unary_op(self, node: UnaryOpNode) -> ExpressionNode:
        """Оптимизация унарной операции"""
        optimized_operand = self.visit_expression(node.operand)
        
        # Если операнд - константа, вычисляем результат
        if self.is_constant(optimized_operand):
            try:
                result = self.evaluate_unary_constant(node.op, optimized_operand)
                if result is not None:
                    self.optimizations_count += 1
                    return result
            except Exception:
                pass
        
        return UnaryOpNode(node.op, optimized_operand, node.meta)
    
    def visit_array_access(self, node: ArrayAccessNode) -> ArrayAccessNode:
        """Оптимизация доступа к массиву"""
        optimized_array = self.visit_expression(node.array)
        optimized_index = self.visit_expression(node.index)
        
        return ArrayAccessNode(optimized_array, optimized_index, node.meta)
    
    def visit_call_expr(self, node: CallNode) -> CallNode:
        """Оптимизация вызова функции"""
        optimized_args = []
        for arg in node.args:
            optimized_args.append(self.visit_expression(arg))
        
        return CallNode(node.name, optimized_args, node.meta)
    
    # ============ Вспомогательные методы ============
    
    def is_constant(self, node: ExpressionNode) -> bool:
        """Проверяет, является ли выражение константой"""
        return isinstance(node, (IntLiteralNode, BoolLiteralNode, CharLiteralNode, StringLiteralNode))
    
    def get_constant_value(self, node: ExpressionNode) -> Any:
        """Получает значение константного выражения"""
        if isinstance(node, IntLiteralNode):
            return node.value
        elif isinstance(node, BoolLiteralNode):
            return node.value
        elif isinstance(node, CharLiteralNode):
            return node.value
        elif isinstance(node, StringLiteralNode):
            return node.value
        else:
            raise OptimizationError(f"Не константное выражение: {type(node)}")
    
    def create_constant_node(self, value: Any) -> ExpressionNode:
        """Создает узел константы по значению"""
        if isinstance(value, int):
            return IntLiteralNode(value)
        elif isinstance(value, bool):
            return BoolLiteralNode(value)
        elif isinstance(value, str) and len(value) == 1:
            return CharLiteralNode(value)
        elif isinstance(value, str):
            return StringLiteralNode(value)
        else:
            raise OptimizationError(f"Неподдерживаемый тип константы: {type(value)}")
    
    def evaluate_constant_expression(self, op: str, left: ExpressionNode, right: ExpressionNode) -> Optional[ExpressionNode]:
        """Вычисляет константное бинарное выражение"""
        left_val = self.get_constant_value(left)
        right_val = self.get_constant_value(right)
        
        try:
            # Арифметические операции
            if op == "+":
                return self.create_constant_node(left_val + right_val)
            elif op == "-":
                return self.create_constant_node(left_val - right_val)
            elif op == "*":
                return self.create_constant_node(left_val * right_val)
            elif op == "/" or op == "div":
                if right_val == 0:
                    return None  # Деление на ноль - не оптимизируем
                return self.create_constant_node(left_val // right_val)
            elif op == "mod":
                if right_val == 0:
                    return None
                return self.create_constant_node(left_val % right_val)
            
            # Операции сравнения
            elif op == "=":
                return self.create_constant_node(left_val == right_val)
            elif op == "<>":
                return self.create_constant_node(left_val != right_val)
            elif op == "<":
                return self.create_constant_node(left_val < right_val)
            elif op == "<=":
                return self.create_constant_node(left_val <= right_val)
            elif op == ">":
                return self.create_constant_node(left_val > right_val)
            elif op == ">=":
                return self.create_constant_node(left_val >= right_val)
            
            # Логические операции
            elif op == "и":
                return self.create_constant_node(bool(left_val) and bool(right_val))
            elif op == "или":
                return self.create_constant_node(bool(left_val) or bool(right_val))
            
        except Exception:
            return None
        
        return None
    
    def evaluate_unary_constant(self, op: str, operand: ExpressionNode) -> Optional[ExpressionNode]:
        """Вычисляет константное унарное выражение"""
        operand_val = self.get_constant_value(operand)
        
        try:
            if op == "-":
                return self.create_constant_node(-operand_val)
            elif op == "+":
                return self.create_constant_node(operand_val)
            elif op == "не":
                return self.create_constant_node(not bool(operand_val))
        except Exception:
            return None
        
        return None
    
    def apply_algebraic_optimizations(self, op: str, left: ExpressionNode, right: ExpressionNode) -> Optional[ExpressionNode]:
        """Применяет алгебраические оптимизации (x + 0, x * 1, etc.)"""
        # x + 0 = x
        if op == "+" and isinstance(right, IntLiteralNode) and right.value == 0:
            self.optimizations_count += 1
            return left
        
        # 0 + x = x
        if op == "+" and isinstance(left, IntLiteralNode) and left.value == 0:
            self.optimizations_count += 1
            return right
        
        # x - 0 = x
        if op == "-" and isinstance(right, IntLiteralNode) and right.value == 0:
            self.optimizations_count += 1
            return left
        
        # x * 1 = x
        if op == "*" and isinstance(right, IntLiteralNode) and right.value == 1:
            self.optimizations_count += 1
            return left
        
        # 1 * x = x
        if op == "*" and isinstance(left, IntLiteralNode) and left.value == 1:
            self.optimizations_count += 1
            return right
        
        # x * 0 = 0
        if op == "*" and isinstance(right, IntLiteralNode) and right.value == 0:
            self.optimizations_count += 1
            return IntLiteralNode(0)
        
        # 0 * x = 0
        if op == "*" and isinstance(left, IntLiteralNode) and left.value == 0:
            self.optimizations_count += 1
            return IntLiteralNode(0)
        
        # x / 1 = x
        if (op == "/" or op == "div") and isinstance(right, IntLiteralNode) and right.value == 1:
            self.optimizations_count += 1
            return left
        
        # x и истина = x
        if op == "и" and isinstance(right, BoolLiteralNode) and right.value:
            self.optimizations_count += 1
            return left
        
        # истина и x = x
        if op == "и" and isinstance(left, BoolLiteralNode) and left.value:
            self.optimizations_count += 1
            return right
        
        # x и ложь = ложь
        if op == "и" and isinstance(right, BoolLiteralNode) and not right.value:
            self.optimizations_count += 1
            return BoolLiteralNode(False)
        
        # ложь и x = ложь
        if op == "и" and isinstance(left, BoolLiteralNode) and not left.value:
            self.optimizations_count += 1
            return BoolLiteralNode(False)
        
        # x или ложь = x
        if op == "или" and isinstance(right, BoolLiteralNode) and not right.value:
            self.optimizations_count += 1
            return left
        
        # ложь или x = x
        if op == "или" and isinstance(left, BoolLiteralNode) and not left.value:
            self.optimizations_count += 1
            return right
        
        # x или истина = истина
        if op == "или" and isinstance(right, BoolLiteralNode) and right.value:
            self.optimizations_count += 1
            return BoolLiteralNode(True)
        
        # истина или x = истина
        if op == "или" and isinstance(left, BoolLiteralNode) and left.value:
            self.optimizations_count += 1
            return BoolLiteralNode(True)
        
        return None


def optimize_ast(ast: ProgramNode, enable_constant_folding: bool = True) -> tuple[ProgramNode, dict]:
    """
    Применяет оптимизации к AST
    Возвращает оптимизированный AST и статистику оптимизаций
    """
    optimized_ast = ast
    stats = {}
    
    if enable_constant_folding:
        folder = ConstantFolder()
        optimized_ast = folder.optimize(optimized_ast)
        stats.update(folder.get_stats())
    
    return optimized_ast, stats


# Экспорт
__all__ = [
    'OptimizationError', 'ConstantFolder', 'optimize_ast'
]
