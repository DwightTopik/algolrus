"""
Генератор байт-кода для виртуальной машины
Преобразует AST в последовательность инструкций VM
"""

from typing import List, Dict, Any, Optional, Union
from mel_ast import *
from mel_types import *
from vm_core import *
from semantics import analyze


class CodeGenError(Exception):
    """Исключение кодогенерации"""
    def __init__(self, message: str, position: Optional[SourcePosition] = None):
        self.message = message
        self.position = position
        super().__init__(self.format_message())
    
    def format_message(self) -> str:
        if self.position:
            return f"Ошибка кодогенерации на {self.position}: {self.message}"
        return f"Ошибка кодогенерации: {self.message}"


class Label:
    """Метка для переходов"""
    def __init__(self, name: str = ""):
        self.name = name
        self.address: Optional[int] = None
        self.references: List[int] = []  # Адреса инструкций, ссылающихся на эту метку
    
    def __str__(self) -> str:
        return f"Label({self.name}, addr={self.address})"


class VMCodeGenerator:
    """Генератор байт-кода для виртуальной машины"""
    
    def __init__(self):
        self.instructions: List[VMInstruction] = []
        self.constants: List[Any] = []
        self.constant_map: Dict[Any, int] = {}  # Кэш констант
        
        # Управление переменными
        self.global_vars: Dict[str, int] = {}   # имя -> индекс
        self.local_vars: Dict[str, int] = {}    # имя -> индекс
        self.globals_count = 0
        self.locals_count = 0
        
        # Управление метками
        self.labels: Dict[str, Label] = {}
        self.label_counter = 0
        
        # Стек контекстов (для циклов, функций)
        self.break_labels: List[Label] = []
        self.continue_labels: List[Label] = []
        
        # Функции
        self.functions: Dict[str, int] = {}  # имя -> адрес
        self.current_function: Optional[str] = None
    
    def generate(self, ast: ProgramNode) -> VMProgram:
        """Главный метод генерации байт-кода"""
        # Сначала проводим семантический анализ
        errors = analyze(ast)
        if errors:
            error_msg = "; ".join(str(e) for e in errors)
            raise CodeGenError(f"Семантические ошибки: {error_msg}")
        
        # Сбрасываем состояние
        self.reset()
        
        # Генерируем код для программы
        self.visit_program(ast)
        
        # Добавляем инструкцию завершения
        self.emit(OpCode.HALT)
        
        # Разрешаем все метки
        self.resolve_labels()
        
        return VMProgram(
            constants=self.constants,
            code=self.instructions,
            globals_count=self.globals_count
        )
    
    def reset(self):
        """Сброс состояния генератора"""
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
        """Генерировать инструкцию"""
        instruction = VMInstruction(opcode, arg)
        address = len(self.instructions)
        self.instructions.append(instruction)
        return address
    
    def add_constant(self, value: Any) -> int:
        """Добавить константу в таблицу"""
        if value in self.constant_map:
            return self.constant_map[value]
        
        index = len(self.constants)
        self.constants.append(value)
        self.constant_map[value] = index
        return index
    
    def create_label(self, name: str = "") -> Label:
        """Создать новую метку"""
        if not name:
            name = f"L{self.label_counter}"
            self.label_counter += 1
        
        if name in self.labels:
            return self.labels[name]
        
        label = Label(name)
        self.labels[name] = label
        return label
    
    def mark_label(self, label: Label):
        """Установить адрес метки"""
        label.address = len(self.instructions)
    
    def emit_jump(self, opcode: OpCode, label: Label) -> int:
        """Генерировать переход на метку"""
        address = self.emit(opcode, 0)  # Временный адрес
        label.references.append(address)
        return address
    
    def resolve_labels(self):
        """Разрешить все ссылки на метки"""
        for label in self.labels.values():
            if label.address is None:
                raise CodeGenError(f"Неразрешенная метка: {label.name}")
            
            for ref_addr in label.references:
                self.instructions[ref_addr].arg = label.address
    
    # ============ Посетители узлов AST ============
    
    def visit_program(self, node: ProgramNode):
        """Генерация кода для программы"""
        self.visit_block(node.block, is_global=True)
    
    def visit_block(self, node: BlockNode, is_global: bool = False):
        """Генерация кода для блока"""
        # Сохраняем текущее состояние локальных переменных
        old_locals = self.local_vars.copy()
        old_locals_count = self.locals_count
        
        if not is_global:
            self.locals_count = 0
            self.local_vars.clear()
        
        try:
            # Обрабатываем объявления переменных
            for var_decl in node.var_decls:
                self.visit_var_decl(var_decl, is_global)
            
            # Обрабатываем объявления функций
            for func_decl in node.func_decls:
                self.declare_function(func_decl)
            
            # Генерируем код функций
            for func_decl in node.func_decls:
                self.visit_func_decl(func_decl)
            
            # Генерируем код операторов
            for stmt in node.statements:
                self.visit_statement(stmt)
        
        finally:
            # Восстанавливаем состояние
            if not is_global:
                self.local_vars = old_locals
                self.locals_count = old_locals_count
    
    def visit_var_decl(self, node: VarDeclNode, is_global: bool = False):
        """Генерация кода для объявления переменной"""
        if is_global:
            self.global_vars[node.name] = self.globals_count
            self.globals_count += 1
        else:
            self.local_vars[node.name] = self.locals_count
            self.locals_count += 1
        
        # Инициализируем переменную значением по умолчанию
        default_value = self.get_default_value_for_type(node.var_type)
        
        if is_global:
            self.emit_literal(default_value)
            self.emit(OpCode.STORE_GLOBAL, self.global_vars[node.name])
        else:
            self.emit_literal(default_value)
            self.emit(OpCode.STORE_LOCAL, self.local_vars[node.name])
    
    def declare_function(self, node: FuncDeclNode):
        """Объявить функцию (запомнить адрес)"""
        # Адрес будет установлен при генерации кода функции
        self.functions[node.name] = -1
    
    def visit_func_decl(self, node: FuncDeclNode):
        """Генерация кода для функции"""
        # Устанавливаем адрес функции
        func_address = len(self.instructions)
        self.functions[node.name] = func_address
        
        old_function = self.current_function
        self.current_function = node.name
        
        # Генерируем код тела функции
        self.visit_block(node.block, is_global=False)
        
        # Добавляем возврат если его нет
        if not node.return_type:
            # Процедура - просто возврат
            self.emit(OpCode.RETURN)
        else:
            # Функция должна вернуть значение (это проверяется в семантике)
            pass
        
        self.current_function = old_function
    
    def get_default_value_for_type(self, type_node: TypeNode) -> Any:
        """Получить значение по умолчанию для типа"""
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
            # Создаем массив с значениями по умолчанию
            if isinstance(type_node.size, IntLiteralNode):
                size = type_node.size.value
                default_elem = self.get_default_value_for_type(type_node.element_type)
                return [default_elem] * size
        
        return 0  # Fallback
    
    # ============ Операторы ============
    
    def visit_statement(self, node: StatementNode):
        """Генерация кода для оператора"""
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
        """Генерация кода для присваивания"""
        # Генерируем код для значения
        self.visit_expression(node.value)
        
        # Генерируем код для цели присваивания
        if isinstance(node.target, IdentifierNode):
            # Простая переменная
            var_name = node.target.name
            if var_name in self.local_vars:
                self.emit(OpCode.STORE_LOCAL, self.local_vars[var_name])
            elif var_name in self.global_vars:
                self.emit(OpCode.STORE_GLOBAL, self.global_vars[var_name])
            else:
                raise CodeGenError(f"Неизвестная переменная: {var_name}", node.meta)
        
        elif isinstance(node.target, ArrayAccessNode):
            # Элемент массива
            # Сначала вычисляем массив и индекс
            self.visit_expression(node.target.array)  # массив на стеке
            self.visit_expression(node.target.index)  # индекс на стеке
            # Значение уже на стеке
            # Стек: [значение, массив, индекс] -> STORE_ARRAY переставляет в [массив, индекс, значение]
            self.emit(OpCode.STORE_ARRAY)
        
        else:
            raise CodeGenError(f"Недопустимая цель присваивания: {type(node.target)}", node.meta)
    
    def visit_if(self, node: IfNode):
        """Генерация кода для условного оператора"""
        # Вычисляем условие
        self.visit_expression(node.condition)
        
        # Метки (уникальные)
        if_id = self.label_counter
        else_label = self.create_label(f"else_{if_id}")
        end_label = self.create_label(f"end_if_{if_id}")
        
        # Переход на else если условие ложно
        self.emit_jump(OpCode.JMP_IF_FALSE, else_label)
        
        # Код then-ветки
        for stmt in node.then_block:
            self.visit_statement(stmt)
        
        # Переход на конец (пропускаем else)
        self.emit_jump(OpCode.JMP, end_label)
        
        # Метка else
        self.mark_label(else_label)
        
        # Код else-ветки (если есть)
        if node.else_block:
            for stmt in node.else_block:
                self.visit_statement(stmt)
        
        # Метка конца
        self.mark_label(end_label)
    
    def visit_for(self, node: ForNode):
        """Генерация кода для цикла for"""
        # Инициализация переменной цикла
        self.visit_expression(node.start)
        
        # Сохраняем значение в переменную цикла
        var_name = node.var
        if var_name in self.local_vars:
            self.emit(OpCode.STORE_LOCAL, self.local_vars[var_name])
        elif var_name in self.global_vars:
            self.emit(OpCode.STORE_GLOBAL, self.global_vars[var_name])
        else:
            raise CodeGenError(f"Неизвестная переменная цикла: {var_name}", node.meta)
        
        # Метки для цикла (с уникальными именами)
        loop_id = len(self.break_labels)  # Используем глубину вложенности как ID
        loop_start = self.create_label(f"for_start_{loop_id}")
        loop_continue = self.create_label(f"for_continue_{loop_id}")
        loop_end = self.create_label(f"for_end_{loop_id}")
        
        # Добавляем метки в стек для break/continue
        self.break_labels.append(loop_end)
        self.continue_labels.append(loop_continue)
        
        try:
            # Начало цикла
            self.mark_label(loop_start)
            
            # Проверяем условие продолжения (переменная <= конечное значение)
            # Загружаем переменную цикла
            if var_name in self.local_vars:
                self.emit(OpCode.LOAD_LOCAL, self.local_vars[var_name])
            else:
                self.emit(OpCode.LOAD_GLOBAL, self.global_vars[var_name])
            
            # Загружаем конечное значение
            self.visit_expression(node.end)
            
            # Сравниваем
            self.emit(OpCode.LE)  # переменная <= конец
            
            # Если условие ложно, выходим из цикла
            self.emit_jump(OpCode.JMP_IF_FALSE, loop_end)
            
            # Тело цикла
            for stmt in node.body:
                self.visit_statement(stmt)
            
            # Метка continue
            self.mark_label(loop_continue)
            
            # Инкремент переменной (шаг)
            if node.step:
                # Загружаем переменную
                if var_name in self.local_vars:
                    self.emit(OpCode.LOAD_LOCAL, self.local_vars[var_name])
                else:
                    self.emit(OpCode.LOAD_GLOBAL, self.global_vars[var_name])
                
                # Добавляем шаг
                self.visit_expression(node.step)
                self.emit(OpCode.ADD)
                
                # Сохраняем обратно
                if var_name in self.local_vars:
                    self.emit(OpCode.STORE_LOCAL, self.local_vars[var_name])
                else:
                    self.emit(OpCode.STORE_GLOBAL, self.global_vars[var_name])
            else:
                # Шаг по умолчанию = 1
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
            
            # Возврат к началу цикла
            self.emit_jump(OpCode.JMP, loop_start)
            
            # Конец цикла
            self.mark_label(loop_end)
        
        finally:
            # Убираем метки из стека
            self.break_labels.pop()
            self.continue_labels.pop()
    
    def visit_while(self, node: WhileNode):
        """Генерация кода для цикла while"""
        loop_id = len(self.break_labels)
        loop_start = self.create_label(f"while_start_{loop_id}")
        loop_end = self.create_label(f"while_end_{loop_id}")
        
        self.break_labels.append(loop_end)
        self.continue_labels.append(loop_start)
        
        try:
            # Начало цикла
            self.mark_label(loop_start)
            
            # Проверяем условие
            self.visit_expression(node.condition)
            self.emit_jump(OpCode.JMP_IF_FALSE, loop_end)
            
            # Тело цикла
            for stmt in node.body:
                self.visit_statement(stmt)
            
            # Возврат к началу
            self.emit_jump(OpCode.JMP, loop_start)
            
            # Конец цикла
            self.mark_label(loop_end)
        
        finally:
            self.break_labels.pop()
            self.continue_labels.pop()
    
    def visit_do_while(self, node: DoWhileNode):
        """Генерация кода для цикла do-while"""
        loop_id = len(self.break_labels)
        loop_start = self.create_label(f"do_while_start_{loop_id}")
        loop_condition = self.create_label(f"do_while_condition_{loop_id}")
        loop_end = self.create_label(f"do_while_end_{loop_id}")
        
        self.break_labels.append(loop_end)
        self.continue_labels.append(loop_condition)
        
        try:
            # Начало цикла
            self.mark_label(loop_start)
            
            # Тело цикла
            for stmt in node.body:
                self.visit_statement(stmt)
            
            # Проверка условия
            self.mark_label(loop_condition)
            self.visit_expression(node.condition)
            self.emit_jump(OpCode.JMP_IF_FALSE, loop_start)  # Если условие ложно, повторяем
            
            # Конец цикла
            self.mark_label(loop_end)
        
        finally:
            self.break_labels.pop()
            self.continue_labels.pop()
    
    def visit_break(self, node: BreakNode):
        """Генерация кода для break"""
        if not self.break_labels:
            raise CodeGenError("Оператор 'стоп' вне цикла", node.meta)
        
        self.emit_jump(OpCode.JMP, self.break_labels[-1])
    
    def visit_continue(self, node: ContinueNode):
        """Генерация кода для continue"""
        if not self.continue_labels:
            raise CodeGenError("Оператор 'далее' вне цикла", node.meta)
        
        self.emit_jump(OpCode.JMP, self.continue_labels[-1])
    
    def visit_return(self, node: ReturnNode):
        """Генерация кода для return"""
        if node.value:
            # Вычисляем возвращаемое значение
            self.visit_expression(node.value)
        
        self.emit(OpCode.RETURN)
    
    def visit_call_stmt(self, node: CallStmtNode):
        """Генерация кода для вызова процедуры"""
        self.visit_call_expr(node.call)
        # Убираем результат со стека (для процедур)
        self.emit(OpCode.POP)
    
    # ============ Выражения ============
    
    def visit_expression(self, node: ExpressionNode):
        """Генерация кода для выражения"""
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
        """Генерация кода для бинарной операции"""
        # Для логических операций нужна ленивая оценка
        if node.op == "и":
            # Ленивое И: если левая часть ложна, результат ложь
            self.visit_expression(node.left)
            self.emit(OpCode.DUP)  # Дублируем для проверки
            
            and_id = self.label_counter
            false_label = self.create_label(f"and_false_{and_id}")
            end_label = self.create_label(f"and_end_{and_id}")
            
            self.emit_jump(OpCode.JMP_IF_FALSE, false_label)
            
            # Левая часть истинна, вычисляем правую
            self.emit(OpCode.POP)  # Убираем дубликат
            self.visit_expression(node.right)
            self.emit_jump(OpCode.JMP, end_label)
            
            # Левая часть ложна
            self.mark_label(false_label)
            # Результат уже на стеке (ложь)
            
            self.mark_label(end_label)
            
        elif node.op == "или":
            # Ленивое ИЛИ: если левая часть истинна, результат истина
            self.visit_expression(node.left)
            self.emit(OpCode.DUP)  # Дублируем для проверки
            
            or_id = self.label_counter
            true_label = self.create_label(f"or_true_{or_id}")
            end_label = self.create_label(f"or_end_{or_id}")
            
            self.emit_jump(OpCode.JMP_IF_TRUE, true_label)
            
            # Левая часть ложна, вычисляем правую
            self.emit(OpCode.POP)  # Убираем дубликат
            self.visit_expression(node.right)
            self.emit_jump(OpCode.JMP, end_label)
            
            # Левая часть истинна
            self.mark_label(true_label)
            # Результат уже на стеке (истина)
            
            self.mark_label(end_label)
        
        else:
            # Обычные операции - вычисляем обе части
            self.visit_expression(node.left)
            self.visit_expression(node.right)
            
            # Генерируем соответствующую операцию
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
        """Генерация кода для унарной операции"""
        self.visit_expression(node.operand)
        
        if node.op == "-":
            self.emit(OpCode.NEG)
        elif node.op == "+":
            # Унарный плюс ничего не делает
            pass
        elif node.op == "не":
            self.emit(OpCode.NOT)
        else:
            raise CodeGenError(f"Неизвестная унарная операция: {node.op}", node.meta)
    
    def visit_identifier(self, node: IdentifierNode):
        """Генерация кода для идентификатора"""
        var_name = node.name
        
        if var_name in self.local_vars:
            self.emit(OpCode.LOAD_LOCAL, self.local_vars[var_name])
        elif var_name in self.global_vars:
            self.emit(OpCode.LOAD_GLOBAL, self.global_vars[var_name])
        else:
            raise CodeGenError(f"Неизвестная переменная: {var_name}", node.meta)
    
    def visit_array_access(self, node: ArrayAccessNode):
        """Генерация кода для доступа к массиву"""
        self.visit_expression(node.array)
        self.visit_expression(node.index)
        self.emit(OpCode.LOAD_ARRAY)
    
    def visit_call_expr(self, node: CallNode):
        """Генерация кода для вызова функции"""
        # Встроенные функции
        if node.name == "вывод":
            if len(node.args) != 1:
                raise CodeGenError("Функция 'вывод' принимает 1 аргумент", node.meta)
            self.visit_expression(node.args[0])
            self.emit(OpCode.PRINT)
            # Функция вывод не возвращает значение, но для совместимости оставляем 0
            self.emit(OpCode.PUSH_INT, 0)
        
        elif node.name == "увел":
            if len(node.args) != 1:
                raise CodeGenError("Функция 'увел' принимает 1 аргумент", node.meta)
            # Получаем переменную для инкремента
            arg = node.args[0]
            if isinstance(arg, IdentifierNode):
                var_name = arg.name
                if var_name in self.global_vars:
                    self.emit(OpCode.INC, self.global_vars[var_name])
                elif var_name in self.local_vars:
                    # Для локальных переменных делаем инкремент вручную
                    self.emit(OpCode.LOAD_LOCAL, self.local_vars[var_name])
                    self.emit(OpCode.PUSH_INT, 1)
                    self.emit(OpCode.ADD)
                    self.emit(OpCode.STORE_LOCAL, self.local_vars[var_name])
                else:
                    raise CodeGenError(f"Неизвестная переменная: {var_name}", node.meta)
            else:
                raise CodeGenError("Функция 'увел' требует переменную", node.meta)
            # Процедура не возвращает значение
            self.emit(OpCode.PUSH_INT, 0)
        
        elif node.name == "умен":
            if len(node.args) != 1:
                raise CodeGenError("Функция 'умен' принимает 1 аргумент", node.meta)
            # Аналогично увел
            arg = node.args[0]
            if isinstance(arg, IdentifierNode):
                var_name = arg.name
                if var_name in self.global_vars:
                    self.emit(OpCode.DEC, self.global_vars[var_name])
                elif var_name in self.local_vars:
                    # Для локальных переменных делаем декремент вручную
                    self.emit(OpCode.LOAD_LOCAL, self.local_vars[var_name])
                    self.emit(OpCode.PUSH_INT, 1)
                    self.emit(OpCode.SUB)
                    self.emit(OpCode.STORE_LOCAL, self.local_vars[var_name])
                else:
                    raise CodeGenError(f"Неизвестная переменная: {var_name}", node.meta)
            else:
                raise CodeGenError("Функция 'умен' требует переменную", node.meta)
            # Процедура не возвращает значение
            self.emit(OpCode.PUSH_INT, 0)
        
        elif node.name == "модуль":
            if len(node.args) != 1:
                raise CodeGenError("Функция 'модуль' принимает 1 аргумент", node.meta)
            self.visit_expression(node.args[0])
            self.emit(OpCode.ABS)
            # Функция возвращает значение, которое уже на стеке
        
        else:
            # Пользовательские функции
            if node.name not in self.functions:
                raise CodeGenError(f"Неизвестная функция: {node.name}", node.meta)
            
            # Генерируем код для аргументов
            for arg in node.args:
                self.visit_expression(arg)
            
            # Вызываем функцию
            func_addr = self.functions[node.name]
            num_locals = 0  # Пока не поддерживаем локальные переменные в функциях
            self.emit(OpCode.CALL, (func_addr, num_locals))
    
    def emit_literal(self, value: Any):
        """Генерация кода для литерала"""
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
            # Сложные константы через таблицу
            const_index = self.add_constant(value)
            self.emit(OpCode.PUSH_CONST, const_index)


def compile_to_vm(ast: ProgramNode) -> VMProgram:
    """Удобная функция для компиляции AST в байт-код VM"""
    codegen = VMCodeGenerator()
    return codegen.generate(ast)


# Экспорт
__all__ = ['CodeGenError', 'VMCodeGenerator', 'compile_to_vm']
