
from typing import List, Dict, Any, Optional, Union
from mel_ast import *
from mel_types import *
from vm_core import *
from semantics import analyze


class CodeGenError(Exception):
    def __init__(self, message: str, position: Optional[SourcePosition] = None):
        self.message = message
        self.position = position
        super().__init__(self.format_message())

    def format_message(self) -> str:
        if self.position:
            return f"Ошибка кодогенерации на {self.position}: {self.message}"
        return f"Ошибка кодогенерации: {self.message}"


class Label:
    def __init__(self, name: str = ""):
        self.name = name
        self.address: Optional[int] = None
        self.references: List[int] = []

    def __str__(self) -> str:
        return f"Label({self.name}, addr={self.address})"


class VMCodeGenerator:

    def __init__(self):
        self.instructions: List[VMInstruction] = []
        self.constants: List[Any] = []
        self.constant_map: Dict[Any, int] = {}


        self.global_vars: Dict[str, int] = {}
        self.local_vars: Dict[str, int] = {}
        self.globals_count = 0
        self.locals_count = 0


        self.labels: Dict[str, Label] = {}
        self.label_counter = 0


        self.break_labels: List[Label] = []
        self.continue_labels: List[Label] = []


        self.functions: Dict[str, int] = {}
        self.current_function: Optional[str] = None

    def generate(self, ast: ProgramNode) -> VMProgram:

        errors = analyze(ast)
        if errors:
            error_msg = "; ".join(str(e) for e in errors)
            raise CodeGenError(f"Семантические ошибки: {error_msg}")


        self.reset()


        self.visit_program(ast)


        self.emit(OpCode.HALT)


        self.resolve_labels()

        return VMProgram(
            constants=self.constants,
            code=self.instructions,
            globals_count=self.globals_count
        )

    def reset(self):
        self.instructions.clear()
        self.constants.clear()
        self.constant_map.clear()
        self.global_vars.clear()
        self.local_vars.clear()
        self.labels.clear()
        self.break_labels.clear()
        self.continue_labels.clear()
        self.functions.clear()

        self.globals_count = 0
        self.locals_count = 0
        self.label_counter = 0
        self.current_function = None

    def emit(self, opcode: OpCode, arg: Any = None) -> int:
        instruction = VMInstruction(opcode, arg)
        address = len(self.instructions)
        self.instructions.append(instruction)
        return address

    def add_constant(self, value: Any) -> int:
        if value in self.constant_map:
            return self.constant_map[value]

        index = len(self.constants)
        self.constants.append(value)
        self.constant_map[value] = index
        return index

    def create_label(self, name: str = "") -> Label:
        if not name:
            name = f"L{self.label_counter}"
            self.label_counter += 1

        if name in self.labels:
            return self.labels[name]

        label = Label(name)
        self.labels[name] = label
        return label

    def mark_label(self, label: Label):
        label.address = len(self.instructions)

    def emit_jump(self, opcode: OpCode, label: Label) -> int:
        address = self.emit(opcode, 0)
        label.references.append(address)
        return address

    def resolve_labels(self):
        for label in self.labels.values():
            if label.address is None:
                raise CodeGenError(f"Неразрешенная метка: {label.name}")

            for ref_addr in label.references:
                self.instructions[ref_addr].arg = label.address



    def visit_program(self, node: ProgramNode):
        self.visit_block(node.block, is_global=True)

    def visit_block(self, node: BlockNode, is_global: bool = False):

        old_locals = self.local_vars.copy()
        old_locals_count = self.locals_count

        if not is_global:
            self.locals_count = 0
            self.local_vars.clear()

        try:

            for var_decl in node.var_decls:
                self.visit_var_decl(var_decl, is_global)


            for func_decl in node.func_decls:
                self.declare_function(func_decl)


            for func_decl in node.func_decls:
                self.visit_func_decl(func_decl)


            for stmt in node.statements:
                self.visit_statement(stmt)

        finally:

            if not is_global:
                self.local_vars = old_locals
                self.locals_count = old_locals_count

    def visit_var_decl(self, node: VarDeclNode, is_global: bool = False):
        if is_global:
            self.global_vars[node.name] = self.globals_count
            self.globals_count += 1
        else:
            self.local_vars[node.name] = self.locals_count
            self.locals_count += 1


        default_value = self.get_default_value_for_type(node.var_type)

        if is_global:
            self.emit_literal(default_value)
            self.emit(OpCode.STORE_GLOBAL, self.global_vars[node.name])
        else:
            self.emit_literal(default_value)
            self.emit(OpCode.STORE_LOCAL, self.local_vars[node.name])

    def declare_function(self, node: FuncDeclNode):

        self.functions[node.name] = -1

    def visit_func_decl(self, node: FuncDeclNode):

        func_address = len(self.instructions)
        self.functions[node.name] = func_address

        old_function = self.current_function
        self.current_function = node.name


        self.visit_block(node.block, is_global=False)


        if not node.return_type:

            self.emit(OpCode.RETURN)
        else:

            pass

        self.current_function = old_function

    def get_default_value_for_type(self, type_node: TypeNode) -> Any:
        if isinstance(type_node, SimpleTypeNode):
            if type_node.name == "цел":
                return 0
            elif type_node.name == "лог":
                return False
            elif type_node.name == "сим":
                return '\0'
            elif type_node.name == "строка":
                return ""
        elif isinstance(type_node, ArrayTypeNode):

            if isinstance(type_node.size, IntLiteralNode):
                size = type_node.size.value
                default_elem = self.get_default_value_for_type(type_node.element_type)
                return [default_elem] * size

        return 0



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
            raise CodeGenError(f"Неизвестный тип оператора: {type(node)}", node.meta)

    def visit_assign(self, node: AssignNode):

        self.visit_expression(node.value)


        if isinstance(node.target, IdentifierNode):

            var_name = node.target.name
            if var_name in self.local_vars:
                self.emit(OpCode.STORE_LOCAL, self.local_vars[var_name])
            elif var_name in self.global_vars:
                self.emit(OpCode.STORE_GLOBAL, self.global_vars[var_name])
            else:
                raise CodeGenError(f"Неизвестная переменная: {var_name}", node.meta)

        elif isinstance(node.target, ArrayAccessNode):


            self.visit_expression(node.target.array)
            self.visit_expression(node.target.index)


            self.emit(OpCode.STORE_ARRAY)

        else:
            raise CodeGenError(f"Недопустимая цель присваивания: {type(node.target)}", node.meta)

    def visit_if(self, node: IfNode):

        self.visit_expression(node.condition)


        if_id = self.label_counter
        else_label = self.create_label(f"else_{if_id}")
        end_label = self.create_label(f"end_if_{if_id}")


        self.emit_jump(OpCode.JMP_IF_FALSE, else_label)


        for stmt in node.then_block:
            self.visit_statement(stmt)


        self.emit_jump(OpCode.JMP, end_label)


        self.mark_label(else_label)


        if node.else_block:
            for stmt in node.else_block:
                self.visit_statement(stmt)


        self.mark_label(end_label)

    def visit_for(self, node: ForNode):

        self.visit_expression(node.start)


        var_name = node.var
        if var_name in self.local_vars:
            self.emit(OpCode.STORE_LOCAL, self.local_vars[var_name])
        elif var_name in self.global_vars:
            self.emit(OpCode.STORE_GLOBAL, self.global_vars[var_name])
        else:
            raise CodeGenError(f"Неизвестная переменная цикла: {var_name}", node.meta)


        loop_id = len(self.break_labels)
        loop_start = self.create_label(f"for_start_{loop_id}")
        loop_continue = self.create_label(f"for_continue_{loop_id}")
        loop_end = self.create_label(f"for_end_{loop_id}")


        self.break_labels.append(loop_end)
        self.continue_labels.append(loop_continue)

        try:

            self.mark_label(loop_start)



            if var_name in self.local_vars:
                self.emit(OpCode.LOAD_LOCAL, self.local_vars[var_name])
            else:
                self.emit(OpCode.LOAD_GLOBAL, self.global_vars[var_name])


            self.visit_expression(node.end)


            self.emit(OpCode.LE)


            self.emit_jump(OpCode.JMP_IF_FALSE, loop_end)


            for stmt in node.body:
                self.visit_statement(stmt)


            self.mark_label(loop_continue)


            if node.step:

                if var_name in self.local_vars:
                    self.emit(OpCode.LOAD_LOCAL, self.local_vars[var_name])
                else:
                    self.emit(OpCode.LOAD_GLOBAL, self.global_vars[var_name])


                self.visit_expression(node.step)
                self.emit(OpCode.ADD)


                if var_name in self.local_vars:
                    self.emit(OpCode.STORE_LOCAL, self.local_vars[var_name])
                else:
                    self.emit(OpCode.STORE_GLOBAL, self.global_vars[var_name])
            else:

                if var_name in self.local_vars:
                    self.emit(OpCode.LOAD_LOCAL, self.local_vars[var_name])
                else:
                    self.emit(OpCode.LOAD_GLOBAL, self.global_vars[var_name])

                self.emit(OpCode.PUSH_INT, 1)
                self.emit(OpCode.ADD)

                if var_name in self.local_vars:
                    self.emit(OpCode.STORE_LOCAL, self.local_vars[var_name])
                else:
                    self.emit(OpCode.STORE_GLOBAL, self.global_vars[var_name])


            self.emit_jump(OpCode.JMP, loop_start)


            self.mark_label(loop_end)

        finally:

            self.break_labels.pop()
            self.continue_labels.pop()

    def visit_while(self, node: WhileNode):
        loop_id = len(self.break_labels)
        loop_start = self.create_label(f"while_start_{loop_id}")
        loop_end = self.create_label(f"while_end_{loop_id}")

        self.break_labels.append(loop_end)
        self.continue_labels.append(loop_start)

        try:

            self.mark_label(loop_start)


            self.visit_expression(node.condition)
            self.emit_jump(OpCode.JMP_IF_FALSE, loop_end)


            for stmt in node.body:
                self.visit_statement(stmt)


            self.emit_jump(OpCode.JMP, loop_start)


            self.mark_label(loop_end)

        finally:
            self.break_labels.pop()
            self.continue_labels.pop()

    def visit_do_while(self, node: DoWhileNode):
        loop_id = len(self.break_labels)
        loop_start = self.create_label(f"do_while_start_{loop_id}")
        loop_condition = self.create_label(f"do_while_condition_{loop_id}")
        loop_end = self.create_label(f"do_while_end_{loop_id}")

        self.break_labels.append(loop_end)
        self.continue_labels.append(loop_condition)

        try:

            self.mark_label(loop_start)


            for stmt in node.body:
                self.visit_statement(stmt)


            self.mark_label(loop_condition)
            self.visit_expression(node.condition)
            self.emit_jump(OpCode.JMP_IF_FALSE, loop_start)


            self.mark_label(loop_end)

        finally:
            self.break_labels.pop()
            self.continue_labels.pop()

    def visit_break(self, node: BreakNode):
        if not self.break_labels:
            raise CodeGenError("Оператор 'стоп' вне цикла", node.meta)

        self.emit_jump(OpCode.JMP, self.break_labels[-1])

    def visit_continue(self, node: ContinueNode):
        if not self.continue_labels:
            raise CodeGenError("Оператор 'далее' вне цикла", node.meta)

        self.emit_jump(OpCode.JMP, self.continue_labels[-1])

    def visit_return(self, node: ReturnNode):
        if node.value:

            self.visit_expression(node.value)

        self.emit(OpCode.RETURN)

    def visit_call_stmt(self, node: CallStmtNode):
        self.visit_call_expr(node.call)

        self.emit(OpCode.POP)



    def visit_expression(self, node: ExpressionNode):
        if isinstance(node, BinOpNode):
            self.visit_bin_op(node)
        elif isinstance(node, UnaryOpNode):
            self.visit_unary_op(node)
        elif isinstance(node, IdentifierNode):
            self.visit_identifier(node)
        elif isinstance(node, ArrayAccessNode):
            self.visit_array_access(node)
        elif isinstance(node, CallNode):
            self.visit_call_expr(node)
        elif isinstance(node, IntLiteralNode):
            self.emit_literal(node.value)
        elif isinstance(node, BoolLiteralNode):
            self.emit_literal(node.value)
        elif isinstance(node, CharLiteralNode):
            self.emit_literal(node.value)
        elif isinstance(node, StringLiteralNode):
            self.emit_literal(node.value)
        else:
            raise CodeGenError(f"Неизвестный тип выражения: {type(node)}", node.meta)

    def visit_bin_op(self, node: BinOpNode):

        if node.op == "и":

            self.visit_expression(node.left)
            self.emit(OpCode.DUP)

            and_id = self.label_counter
            false_label = self.create_label(f"and_false_{and_id}")
            end_label = self.create_label(f"and_end_{and_id}")

            self.emit_jump(OpCode.JMP_IF_FALSE, false_label)


            self.emit(OpCode.POP)
            self.visit_expression(node.right)
            self.emit_jump(OpCode.JMP, end_label)


            self.mark_label(false_label)


            self.mark_label(end_label)

        elif node.op == "или":

            self.visit_expression(node.left)
            self.emit(OpCode.DUP)

            or_id = self.label_counter
            true_label = self.create_label(f"or_true_{or_id}")
            end_label = self.create_label(f"or_end_{or_id}")

            self.emit_jump(OpCode.JMP_IF_TRUE, true_label)


            self.emit(OpCode.POP)
            self.visit_expression(node.right)
            self.emit_jump(OpCode.JMP, end_label)


            self.mark_label(true_label)


            self.mark_label(end_label)

        else:

            self.visit_expression(node.left)
            self.visit_expression(node.right)


            op_map = {
                "+": OpCode.ADD,
                "-": OpCode.SUB,
                "*": OpCode.MUL,
                "/": OpCode.DIV,
                "div": OpCode.IDIV,
                "mod": OpCode.MOD,
                "=": OpCode.EQ,
                "<>": OpCode.NE,
                "<": OpCode.LT,
                "<=": OpCode.LE,
                ">": OpCode.GT,
                ">=": OpCode.GE
            }

            if node.op in op_map:
                self.emit(op_map[node.op])
            else:
                raise CodeGenError(f"Неизвестная бинарная операция: {node.op}", node.meta)

    def visit_unary_op(self, node: UnaryOpNode):
        self.visit_expression(node.operand)

        if node.op == "-":
            self.emit(OpCode.NEG)
        elif node.op == "+":

            pass
        elif node.op == "не":
            self.emit(OpCode.NOT)
        else:
            raise CodeGenError(f"Неизвестная унарная операция: {node.op}", node.meta)

    def visit_identifier(self, node: IdentifierNode):
        var_name = node.name

        if var_name in self.local_vars:
            self.emit(OpCode.LOAD_LOCAL, self.local_vars[var_name])
        elif var_name in self.global_vars:
            self.emit(OpCode.LOAD_GLOBAL, self.global_vars[var_name])
        else:
            raise CodeGenError(f"Неизвестная переменная: {var_name}", node.meta)

    def visit_array_access(self, node: ArrayAccessNode):
        self.visit_expression(node.array)
        self.visit_expression(node.index)
        self.emit(OpCode.LOAD_ARRAY)

    def visit_call_expr(self, node: CallNode):

        if node.name == "вывод":
            if len(node.args) != 1:
                raise CodeGenError("Функция 'вывод' принимает 1 аргумент", node.meta)
            self.visit_expression(node.args[0])
            self.emit(OpCode.PRINT)

            self.emit(OpCode.PUSH_INT, 0)

        elif node.name == "увел":
            if len(node.args) != 1:
                raise CodeGenError("Функция 'увел' принимает 1 аргумент", node.meta)

            arg = node.args[0]
            if isinstance(arg, IdentifierNode):
                var_name = arg.name
                if var_name in self.global_vars:
                    self.emit(OpCode.INC, self.global_vars[var_name])
                elif var_name in self.local_vars:

                    self.emit(OpCode.LOAD_LOCAL, self.local_vars[var_name])
                    self.emit(OpCode.PUSH_INT, 1)
                    self.emit(OpCode.ADD)
                    self.emit(OpCode.STORE_LOCAL, self.local_vars[var_name])
                else:
                    raise CodeGenError(f"Неизвестная переменная: {var_name}", node.meta)
            else:
                raise CodeGenError("Функция 'увел' требует переменную", node.meta)

            self.emit(OpCode.PUSH_INT, 0)

        elif node.name == "умен":
            if len(node.args) != 1:
                raise CodeGenError("Функция 'умен' принимает 1 аргумент", node.meta)

            arg = node.args[0]
            if isinstance(arg, IdentifierNode):
                var_name = arg.name
                if var_name in self.global_vars:
                    self.emit(OpCode.DEC, self.global_vars[var_name])
                elif var_name in self.local_vars:

                    self.emit(OpCode.LOAD_LOCAL, self.local_vars[var_name])
                    self.emit(OpCode.PUSH_INT, 1)
                    self.emit(OpCode.SUB)
                    self.emit(OpCode.STORE_LOCAL, self.local_vars[var_name])
                else:
                    raise CodeGenError(f"Неизвестная переменная: {var_name}", node.meta)
            else:
                raise CodeGenError("Функция 'умен' требует переменную", node.meta)

            self.emit(OpCode.PUSH_INT, 0)

        elif node.name == "модуль":
            if len(node.args) != 1:
                raise CodeGenError("Функция 'модуль' принимает 1 аргумент", node.meta)
            self.visit_expression(node.args[0])
            self.emit(OpCode.ABS)


        else:

            if node.name not in self.functions:
                raise CodeGenError(f"Неизвестная функция: {node.name}", node.meta)


            for arg in node.args:
                self.visit_expression(arg)


            func_addr = self.functions[node.name]
            num_locals = 0
            self.emit(OpCode.CALL, (func_addr, num_locals))

    def emit_literal(self, value: Any):
        if isinstance(value, int):
            self.emit(OpCode.PUSH_INT, value)
        elif isinstance(value, bool):
            self.emit(OpCode.PUSH_BOOL, value)
        elif isinstance(value, str):
            if len(value) == 1:
                self.emit(OpCode.PUSH_CHAR, value)
            else:
                self.emit(OpCode.PUSH_STRING, value)
        else:

            const_index = self.add_constant(value)
            self.emit(OpCode.PUSH_CONST, const_index)


def compile_to_vm(ast: ProgramNode) -> VMProgram:
    codegen = VMCodeGenerator()
    return codegen.generate(ast)



__all__ = ['CodeGenError', 'VMCodeGenerator', 'compile_to_vm']
