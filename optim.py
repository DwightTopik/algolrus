
from typing import List, Optional, Any, Union
from mel_ast import *
from mel_types import *


class OptimizationError(Exception):
    def __init__(self, message: str, position: Optional[SourcePosition] = None):
        self.message = message
        self.position = position
        super().__init__(self.format_message())

    def format_message(self) -> str:
        if self.position:
            return f"Ошибка оптимизации на {self.position}: {self.message}"
        return f"Ошибка оптимизации: {self.message}"


class ConstantFolder:

    def __init__(self):
        self.optimizations_count = 0

    def optimize(self, ast: ProgramNode) -> ProgramNode:
        self.optimizations_count = 0
        optimized_ast = self.visit_program(ast)
        return optimized_ast

    def get_stats(self) -> dict:
        return {
            "constant_folding": self.optimizations_count,
            "total": self.optimizations_count
        }



    def visit_program(self, node: ProgramNode) -> ProgramNode:
        optimized_block = self.visit_block(node.block)
        return ProgramNode(node.name, optimized_block, node.meta)

    def visit_block(self, node: BlockNode) -> BlockNode:

        optimized_var_decls = []
        for var_decl in node.var_decls:
            optimized_var_decls.append(self.visit_var_decl(var_decl))


        optimized_func_decls = []
        for func_decl in node.func_decls:
            optimized_func_decls.append(self.visit_func_decl(func_decl))


        optimized_statements = []
        for stmt in node.statements:
            optimized_stmt = self.visit_statement(stmt)
            if optimized_stmt:
                optimized_statements.append(optimized_stmt)

        return BlockNode(
            var_decls=optimized_var_decls,
            func_decls=optimized_func_decls,
            statements=optimized_statements,
            meta=node.meta
        )

    def visit_var_decl(self, node: VarDeclNode) -> VarDeclNode:

        return node

    def visit_func_decl(self, node: FuncDeclNode) -> FuncDeclNode:
        optimized_block = self.visit_block(node.block)
        return FuncDeclNode(
            name=node.name,
            params=node.params,
            return_type=node.return_type,
            block=optimized_block,
            meta=node.meta
        )

    def visit_statement(self, node: StatementNode) -> Optional[StatementNode]:
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

            return node

    def visit_assign(self, node: AssignNode) -> AssignNode:
        optimized_value = self.visit_expression(node.value)
        return AssignNode(node.target, optimized_value, node.meta)

    def visit_if(self, node: IfNode) -> Optional[StatementNode]:
        optimized_condition = self.visit_expression(node.condition)


        if isinstance(optimized_condition, BoolLiteralNode):
            self.optimizations_count += 1
            if optimized_condition.value:

                optimized_statements = []
                for stmt in node.then_block:
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
                else:
                    return None
            else:

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

                return None


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
        optimized_condition = self.visit_expression(node.condition)


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
        optimized_value = None
        if node.value:
            optimized_value = self.visit_expression(node.value)

        return ReturnNode(optimized_value, node.meta)

    def visit_call_stmt(self, node: CallStmtNode) -> CallStmtNode:
        optimized_call = self.visit_call_expr(node.call)
        return CallStmtNode(optimized_call, node.meta)



    def visit_expression(self, node: ExpressionNode) -> ExpressionNode:
        if isinstance(node, BinOpNode):
            return self.visit_bin_op(node)
        elif isinstance(node, UnaryOpNode):
            return self.visit_unary_op(node)
        elif isinstance(node, ArrayAccessNode):
            return self.visit_array_access(node)
        elif isinstance(node, CallNode):
            return self.visit_call_expr(node)
        else:

            return node

    def visit_bin_op(self, node: BinOpNode) -> ExpressionNode:

        optimized_left = self.visit_expression(node.left)
        optimized_right = self.visit_expression(node.right)


        if self.is_constant(optimized_left) and self.is_constant(optimized_right):

            try:
                result = self.evaluate_constant_expression(node.op, optimized_left, optimized_right)
                if result is not None:
                    self.optimizations_count += 1
                    return result
            except Exception:

                pass


        optimized = self.apply_algebraic_optimizations(node.op, optimized_left, optimized_right)
        if optimized:
            return optimized


        return BinOpNode(optimized_left, node.op, optimized_right, node.meta)

    def visit_unary_op(self, node: UnaryOpNode) -> ExpressionNode:
        optimized_operand = self.visit_expression(node.operand)


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
        optimized_array = self.visit_expression(node.array)
        optimized_index = self.visit_expression(node.index)

        return ArrayAccessNode(optimized_array, optimized_index, node.meta)

    def visit_call_expr(self, node: CallNode) -> CallNode:
        optimized_args = []
        for arg in node.args:
            optimized_args.append(self.visit_expression(arg))

        return CallNode(node.name, optimized_args, node.meta)



    def is_constant(self, node: ExpressionNode) -> bool:
        return isinstance(node, (IntLiteralNode, BoolLiteralNode, CharLiteralNode, StringLiteralNode))

    def get_constant_value(self, node: ExpressionNode) -> Any:
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
        left_val = self.get_constant_value(left)
        right_val = self.get_constant_value(right)

        try:

            if op == "+":
                return self.create_constant_node(left_val + right_val)
            elif op == "-":
                return self.create_constant_node(left_val - right_val)
            elif op == "*":
                return self.create_constant_node(left_val * right_val)
            elif op == "/" or op == "div":
                if right_val == 0:
                    return None
                return self.create_constant_node(left_val // right_val)
            elif op == "mod":
                if right_val == 0:
                    return None
                return self.create_constant_node(left_val % right_val)


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


            elif op == "и":
                return self.create_constant_node(bool(left_val) and bool(right_val))
            elif op == "или":
                return self.create_constant_node(bool(left_val) or bool(right_val))

        except Exception:
            return None

        return None

    def evaluate_unary_constant(self, op: str, operand: ExpressionNode) -> Optional[ExpressionNode]:
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

        if op == "+" and isinstance(right, IntLiteralNode) and right.value == 0:
            self.optimizations_count += 1
            return left


        if op == "+" and isinstance(left, IntLiteralNode) and left.value == 0:
            self.optimizations_count += 1
            return right


        if op == "-" and isinstance(right, IntLiteralNode) and right.value == 0:
            self.optimizations_count += 1
            return left


        if op == "*" and isinstance(right, IntLiteralNode) and right.value == 1:
            self.optimizations_count += 1
            return left


        if op == "*" and isinstance(left, IntLiteralNode) and left.value == 1:
            self.optimizations_count += 1
            return right


        if op == "*" and isinstance(right, IntLiteralNode) and right.value == 0:
            self.optimizations_count += 1
            return IntLiteralNode(0)


        if op == "*" and isinstance(left, IntLiteralNode) and left.value == 0:
            self.optimizations_count += 1
            return IntLiteralNode(0)


        if (op == "/" or op == "div") and isinstance(right, IntLiteralNode) and right.value == 1:
            self.optimizations_count += 1
            return left


        if op == "и" and isinstance(right, BoolLiteralNode) and right.value:
            self.optimizations_count += 1
            return left


        if op == "и" and isinstance(left, BoolLiteralNode) and left.value:
            self.optimizations_count += 1
            return right


        if op == "и" and isinstance(right, BoolLiteralNode) and not right.value:
            self.optimizations_count += 1
            return BoolLiteralNode(False)


        if op == "и" and isinstance(left, BoolLiteralNode) and not left.value:
            self.optimizations_count += 1
            return BoolLiteralNode(False)


        if op == "или" and isinstance(right, BoolLiteralNode) and not right.value:
            self.optimizations_count += 1
            return left


        if op == "или" and isinstance(left, BoolLiteralNode) and not left.value:
            self.optimizations_count += 1
            return right


        if op == "или" and isinstance(right, BoolLiteralNode) and right.value:
            self.optimizations_count += 1
            return BoolLiteralNode(True)


        if op == "или" and isinstance(left, BoolLiteralNode) and left.value:
            self.optimizations_count += 1
            return BoolLiteralNode(True)

        return None


class PeepholeOptimizer:

    def __init__(self):
        self.optimizations_count = 0

    def optimize(self, program) -> tuple:
        from vm_core import VMProgram, VMInstruction, OpCode

        self.optimizations_count = 0
        optimized_code = []
        i = 0

        while i < len(program.code):

            optimization_applied = False


            if (i + 1 < len(program.code) and
                program.code[i].opcode.value.startswith('PUSH') and
                program.code[i + 1].opcode == OpCode.POP):


                i += 2
                self.optimizations_count += 1
                optimization_applied = True


            elif (i + 1 < len(program.code) and
                  program.code[i].opcode == OpCode.PUSH_INT and
                  program.code[i].arg == 0 and
                  program.code[i + 1].opcode == OpCode.ADD):


                i += 2
                self.optimizations_count += 1
                optimization_applied = True


            elif (i + 1 < len(program.code) and
                  program.code[i].opcode == OpCode.PUSH_INT and
                  program.code[i].arg == 1 and
                  program.code[i + 1].opcode == OpCode.MUL):


                i += 2
                self.optimizations_count += 1
                optimization_applied = True


            elif (i + 1 < len(program.code) and
                  program.code[i].opcode == OpCode.PUSH_INT and
                  program.code[i].arg == 0 and
                  program.code[i + 1].opcode == OpCode.MUL):


                optimized_code.append(VMInstruction(OpCode.PUSH_INT, 0))
                i += 2
                self.optimizations_count += 1
                optimization_applied = True


            elif (i + 1 < len(program.code) and
                  program.code[i].opcode == OpCode.PUSH_INT and
                  program.code[i].arg == 1 and
                  program.code[i + 1].opcode == OpCode.DIV):


                i += 2
                self.optimizations_count += 1
                optimization_applied = True


            elif (i + 2 < len(program.code) and
                  program.code[i].opcode == OpCode.PUSH_INT and
                  program.code[i + 1].opcode == OpCode.PUSH_INT and
                  program.code[i + 2].opcode == OpCode.ADD):


                result = program.code[i].arg + program.code[i + 1].arg
                optimized_code.append(VMInstruction(OpCode.PUSH_INT, result))
                i += 3
                self.optimizations_count += 1
                optimization_applied = True


            elif (i + 2 < len(program.code) and
                  program.code[i].opcode == OpCode.PUSH_INT and
                  program.code[i + 1].opcode == OpCode.PUSH_INT and
                  program.code[i + 2].opcode == OpCode.SUB):


                result = program.code[i].arg - program.code[i + 1].arg
                optimized_code.append(VMInstruction(OpCode.PUSH_INT, result))
                i += 3
                self.optimizations_count += 1
                optimization_applied = True


            elif (i + 2 < len(program.code) and
                  program.code[i].opcode == OpCode.PUSH_INT and
                  program.code[i + 1].opcode == OpCode.PUSH_INT and
                  program.code[i + 2].opcode == OpCode.MUL):


                result = program.code[i].arg * program.code[i + 1].arg
                optimized_code.append(VMInstruction(OpCode.PUSH_INT, result))
                i += 3
                self.optimizations_count += 1
                optimization_applied = True


            elif (i + 1 < len(program.code) and
                  program.code[i].opcode == OpCode.JMP_IF_FALSE and
                  program.code[i + 1].opcode == OpCode.JMP and
                  program.code[i].arg == i + 2):


                optimized_code.append(VMInstruction(OpCode.JMP_IF_TRUE, program.code[i + 1].arg))
                i += 2
                self.optimizations_count += 1
                optimization_applied = True


            elif program.code[i].opcode == OpCode.NOP:

                i += 1
                self.optimizations_count += 1
                optimization_applied = True


            if not optimization_applied:
                optimized_code.append(program.code[i])
                i += 1


        optimized_program = VMProgram(
            constants=program.constants,
            code=optimized_code,
            globals_count=program.globals_count
        )

        return optimized_program, self.get_stats()

    def get_stats(self) -> dict:
        return {
            "peephole": self.optimizations_count,
            "total": self.optimizations_count
        }


def optimize_ast(ast: ProgramNode, enable_constant_folding: bool = True) -> tuple[ProgramNode, dict]:
    optimized_ast = ast
    stats = {}

    if enable_constant_folding:
        folder = ConstantFolder()
        optimized_ast = folder.optimize(optimized_ast)
        stats.update(folder.get_stats())

    return optimized_ast, stats


def optimize_bytecode(program, enable_peephole: bool = True) -> tuple:
    optimized_program = program
    stats = {}

    if enable_peephole:
        optimizer = PeepholeOptimizer()
        optimized_program, peephole_stats = optimizer.optimize(optimized_program)
        stats.update(peephole_stats)

    return optimized_program, stats



__all__ = [
    'OptimizationError', 'ConstantFolder', 'PeepholeOptimizer',
    'optimize_ast', 'optimize_bytecode'
]
