from lark import Lark, Transformer, Token, Tree
from lark.exceptions import LarkError
from typing import List, Optional, Any, Union
from mel_ast import *



GRAMMAR = r"""
    // Основная программа
    program: "алг" IDENTIFIER ";" block "кон"

    // Блок программы
    block: var_section? func_section? stmt_list

    // Раздел переменных
    var_section: "нач" var_decl_list "кон"

    var_decl_list: var_decl+

    var_decl: IDENTIFIER ":" type_spec ";"

    // Раздел функций
    func_section: func_section_keyword func_decl+ "кон"
    func_section_keyword: IDENTIFIER

    func_decl: func_keyword IDENTIFIER "(" param_list? ")" (":" type_spec)? ";" func_body_with_vars "кон"
             | func_keyword IDENTIFIER "(" param_list? ")" (":" type_spec)? ";" func_body_no_vars "кон"
             | func_keyword IDENTIFIER "(" param_list? ")" (":" type_spec)? ";" func_body_empty_vars "кон"
    func_keyword: IDENTIFIER

    func_body_with_vars: "нач" var_decl_list "кон" stmt_list
    func_body_no_vars: stmt_list
    func_body_empty_vars: "кон" stmt_list

    param_list: param ("," param)*

    param: IDENTIFIER ":" type_spec

    // Типы
    type_spec: simple_type
             | array_type

    simple_type: "цел"      -> integer_type
               | "лог"      -> boolean_type
               | "сим"      -> char_type
               | "строка"   -> string_type

    array_type: "таб" "[" INTEGER "]" simple_type

    // Список операторов
    stmt_list: statement*

    // Операторы
    statement: var_assignment ";"
             | array_assignment ";"
             | if_stmt
             | for_stmt
             | while_stmt
             | do_while_stmt
             | break_stmt
             | continue_stmt
             | return_stmt ";"
             | call_stmt ";"

    var_assignment: IDENTIFIER ASSIGN expression
    array_assignment: IDENTIFIER "[" expression "]" ASSIGN expression

    // Операторы
    if_stmt: "если" expression "то" stmt_list ("иначе" stmt_list)? "все"

    for_stmt: "для" IDENTIFIER "от" expression "до" expression ("шаг" expression)? stmt_list "кц"

    while_stmt: "пока" expression stmt_list "кц"

    do_while_stmt: "цикл" stmt_list "до" expression

    break_stmt: "стоп"

    continue_stmt: "далее"

    return_stmt: "знач" expression?

    call_stmt: call_expr

    // Выражения
    expression: or_expr

    or_expr: and_expr ("или" and_expr)*

    and_expr: not_expr ("и" not_expr)*

    not_expr: "не" comparison -> unary_not
            | comparison

    comparison: arith_expr (comp_op arith_expr)*

    comp_op: COMP_OP

    arith_expr: term (add_op term)*

    add_op: ADD_OP

    term: factor (mul_op factor)*

    mul_op: MUL_OP

    factor: "+" factor     -> unary_plus
          | "-" factor     -> unary_minus
          | primary

    primary: IDENTIFIER
           | INTEGER
           | BOOLEAN
           | CHAR
           | STRING
           | array_access
           | call_expr
           | "(" expression ")"

    array_access: IDENTIFIER "[" expression "]"

    call_expr: IDENTIFIER "(" arg_list? ")"

    arg_list: expression ("," expression)*

    // Токены
    ASSIGN: ":="
    INTEGER: /\d+/

    // Операторы как токены (должны быть перед IDENTIFIER)
    COMP_OP: "=" | "<>" | ">" | ">=" | "<" | "<="
    ADD_OP: "+" | "-"
    MUL_OP.2: "*" | "/" | "div" | "mod"

    // BOOLEAN должен быть перед IDENTIFIER для правильного приоритета
    BOOLEAN.1: "да" | "нет"
    CHAR: /'([^'\\]|\\.)'/
    STRING: /"([^"\\]|\\.)*"/

    // IDENTIFIER (после всех других токенов)
    IDENTIFIER: /[а-яёa-z_][а-яёa-z0-9_]*/i

    // Комментарии и пробелы
    COMMENT: "|" /[^\r\n]*/
    %import common.WS
    %ignore WS
    %ignore COMMENT
"""


class ParseError(Exception):
    def __init__(self, message: str, line: Optional[int] = None, column: Optional[int] = None):
        self.message = message
        self.line = line
        self.column = column
        super().__init__(self.format_message())

    def format_message(self) -> str:
        if self.line is not None and self.column is not None:
            return f"Синтаксическая ошибка на {self.line}:{self.column}: {self.message}"
        return f"Синтаксическая ошибка: {self.message}"


class MelASTBuilder(Transformer):

    def _get_position(self, token_or_tree) -> Optional[SourcePosition]:
        if hasattr(token_or_tree, 'line') and hasattr(token_or_tree, 'column'):
            return SourcePosition(token_or_tree.line, token_or_tree.column)
        elif hasattr(token_or_tree, 'meta') and token_or_tree.meta:
            return SourcePosition(token_or_tree.meta.line, token_or_tree.meta.column)
        return None

    def _convert_token_to_node(self, token):
        if not hasattr(token, 'type'):
            return token

        if token.type == 'IDENTIFIER':
            return IdentifierNode(name=str(token))
        elif token.type == 'INTEGER':
            return IntLiteralNode(value=int(token))
        elif token.type == 'BOOLEAN':
            return BoolLiteralNode(value=str(token) == "да")
        elif token.type == 'CHAR':
            return CharLiteralNode(value=str(token)[1:-1])
        elif token.type == 'STRING':
            return StringLiteralNode(value=str(token)[1:-1])
        else:
            return token


    def program(self, items):
        name_token, block = items[0], items[1]
        return ProgramNode(
            name=str(name_token),
            block=block,
            meta=self._get_position(name_token)
        )

    def block(self, items):
        var_decls = []
        func_decls = []
        statements = []

        for item in items:
            if item is None:

                continue
            elif isinstance(item, list):

                if len(item) > 0:
                    if isinstance(item[0], VarDeclNode):
                        var_decls.extend(item)
                    elif isinstance(item[0], FuncDeclNode):
                        func_decls.extend(item)
                    elif isinstance(item[0], StatementNode):
                        statements.extend(item)
                    else:
                        statements.extend(item)
            elif isinstance(item, VarDeclNode):
                var_decls.append(item)
            elif isinstance(item, FuncDeclNode):
                func_decls.append(item)
            elif isinstance(item, StatementNode):
                statements.append(item)

        return BlockNode(var_decls=var_decls, func_decls=func_decls, statements=statements)

    def var_section(self, items):
        return items[0]

    def var_decl_list(self, items):
        return items

    def var_decl(self, items):
        name_token, type_spec = items[0], items[1]
        return VarDeclNode(
            name=str(name_token),
            var_type=type_spec,
            meta=self._get_position(name_token)
        )

    def func_section_keyword(self, items):
        keyword = str(items[0])
        if keyword != "функции":
            raise ParseError(f"Ожидается 'функции', получено '{keyword}'")
        return keyword

    def func_keyword(self, items):
        keyword = str(items[0])
        if keyword != "функция":
            raise ParseError(f"Ожидается 'функция', получено '{keyword}'")
        return keyword



    def func_section(self, items):


        return items[1:]

    def func_decl(self, items):

        func_keyword = items[0]
        name_token = items[1]
        params = []
        return_type = None
        block = None


        for item in items[2:]:
            if isinstance(item, list):

                params = item
            elif isinstance(item, TypeNode):

                return_type = item
            elif isinstance(item, BlockNode):

                block = item

        return FuncDeclNode(
            name=str(name_token),
            params=params or [],
            return_type=return_type,
            block=block,
            meta=self._get_position(name_token)
        )

    def param_list(self, items):
        return items

    def param(self, items):
        name_token, param_type = items[0], items[1]
        return ParamNode(
            name=str(name_token),
            param_type=param_type,
            meta=self._get_position(name_token)
        )

    def func_body_with_vars(self, items):

        var_decls = items[0] if items[0] else []
        statements = items[1] if items[1] else []
        return BlockNode(var_decls=var_decls, statements=statements)

    def func_body_no_vars(self, items):

        statements = items[0] if items else []
        return BlockNode(statements=statements)

    def func_body_empty_vars(self, items):

        statements = items[0] if items else []
        return BlockNode(statements=statements)


    def type_spec(self, items):
        return items[0]


    def integer_type(self, items):
        return SimpleTypeNode(name="цел")

    def boolean_type(self, items):
        return SimpleTypeNode(name="лог")

    def char_type(self, items):
        return SimpleTypeNode(name="сим")

    def string_type(self, items):
        return SimpleTypeNode(name="строка")

    def array_type(self, items):
        size_token, element_type = items[0], items[1]

        if isinstance(size_token, IntLiteralNode):
            size_expr = size_token
        else:

            size_expr = IntLiteralNode(value=int(size_token))
        return ArrayTypeNode(size=size_expr, element_type=element_type)


    def stmt_list(self, items):
        return items

    def statement(self, items):
        return items[0]

    def var_assignment(self, items):

        target_name, assign_token, value = items[0], items[1], items[2]
        target = IdentifierNode(name=str(target_name))
        value = self._convert_token_to_node(value)
        return AssignNode(target=target, value=value)

    def array_assignment(self, items):


        if len(items) == 4:

            array_name, index, assign_token, value = items[0], items[1], items[2], items[3]
        else:

            array_name, index, assign_token, value = items[0], items[2], items[4], items[5]

        array_node = IdentifierNode(name=str(array_name))
        index = self._convert_token_to_node(index)
        value = self._convert_token_to_node(value)
        return AssignNode(target=ArrayAccessNode(array=array_node, index=index), value=value)

    def if_stmt(self, items):
        condition = items[0]
        then_block = items[1] if len(items) > 1 else []
        else_block = items[2] if len(items) > 2 else None

        return IfNode(
            condition=condition,
            then_block=then_block,
            else_block=else_block
        )

    def for_stmt(self, items):
        var_token = items[0]
        start_expr = items[1]
        end_expr = items[2]

        step_expr = None
        body = []

        if len(items) == 4:
            body = items[3]
        elif len(items) == 5:
            step_expr = items[3]
            body = items[4]

        return ForNode(
            var=str(var_token),
            start=start_expr,
            end=end_expr,
            step=step_expr,
            body=body
        )

    def while_stmt(self, items):
        condition, body = items[0], items[1]
        return WhileNode(condition=condition, body=body)

    def do_while_stmt(self, items):
        body, condition = items[0], items[1]
        return DoWhileNode(body=body, condition=condition)

    def break_stmt(self, items):
        return BreakNode()

    def continue_stmt(self, items):
        return ContinueNode()

    def return_stmt(self, items):
        value = items[0] if items else None
        return ReturnNode(value=value)

    def call_stmt(self, items):
        return CallStmtNode(call=items[0])


    def expression(self, items):
        return items[0]

    def factor(self, items):
        return items[0]



    def not_expr(self, items):
        return items[0]

    def comparison(self, items):
        return items[0] if len(items) == 1 else self._build_binary_chain(items)

    def arith_expr(self, items):
        return items[0] if len(items) == 1 else self._build_binary_chain(items)

    def add_op(self, items):

        return str(items[0])

    def term(self, items):
        return items[0] if len(items) == 1 else self._build_binary_chain(items)

    def mul_op(self, items):

        return str(items[0])

    def comp_op(self, items):

        return str(items[0])



    def _build_binary_chain(self, items):
        if len(items) == 1:
            return self._convert_token_to_node(items[0])

        result = self._convert_token_to_node(items[0])
        for i in range(1, len(items), 2):
            if i + 1 < len(items):
                op_item = items[i]
                right = self._convert_token_to_node(items[i + 1])


                if isinstance(op_item, str):

                    op = op_item
                elif hasattr(op_item, 'data'):


                    if op_item.children:
                        op = str(op_item.children[0])
                    else:

                        if op_item.data == 'add_op':
                            op = "+"
                        elif op_item.data == 'mul_op':
                            op = "*"
                        elif op_item.data == 'comp_op':
                            op = "="
                        else:
                            op = "?"
                elif hasattr(op_item, 'value'):
                    op = str(op_item.value)
                elif hasattr(op_item, 'type'):
                    op = str(op_item)
                else:
                    op = str(op_item)

                result = BinOpNode(left=result, op=op, right=right)
        return result

    def _extract_operator(self, op_item):

        if isinstance(op_item, str):
            return op_item


        if hasattr(op_item, 'value'):
            return str(op_item.value)


        if hasattr(op_item, 'type'):

            return str(op_item)


        if hasattr(op_item, 'data'):
            return str(op_item.data)


        op_str = str(op_item)


        import re


        match = re.search(r"'([^']*)'", op_str)
        if match:
            return match.group(1)


        if 'add_op' in op_str:
            if '+' in op_str:
                return '+'
            elif '-' in op_str:
                return '-'
        elif 'mul_op' in op_str:
            if '*' in op_str:
                return '*'
            elif '/' in op_str:
                return '/'
            elif 'div' in op_str:
                return 'div'
            elif 'mod' in op_str:
                return 'mod'
        elif 'comp_op' in op_str:
            if '<>' in op_str:
                return '<>'
            elif '>=' in op_str:
                return '>='
            elif '<=' in op_str:
                return '<='
            elif '>' in op_str:
                return '>'
            elif '<' in op_str:
                return '<'
            elif '=' in op_str:
                return '='

        return op_str

    def or_expr(self, items):
        if len(items) == 1:
            return items[0]
        else:
            return self._build_binary_chain_with_op(items, "или")

    def and_expr(self, items):
        if len(items) == 1:
            return items[0]
        else:
            return self._build_binary_chain_with_op(items, "и")

    def _build_binary_chain_with_op(self, items, op):
        result = self._convert_token_to_node(items[0])
        for i in range(1, len(items)):
            right = self._convert_token_to_node(items[i])
            result = BinOpNode(left=result, op=op, right=right)
        return result





    def unary_not(self, items):
        return UnaryOpNode(op="не", operand=self._convert_token_to_node(items[0]))

    def unary_plus(self, items):
        return UnaryOpNode(op="+", operand=self._convert_token_to_node(items[0]))

    def unary_minus(self, items):
        return UnaryOpNode(op="-", operand=self._convert_token_to_node(items[0]))

    def primary(self, items):
        item = items[0]

        if hasattr(item, 'type'):
            if item.type == 'IDENTIFIER':
                return IdentifierNode(name=str(item))
            elif item.type == 'INTEGER':
                return IntLiteralNode(value=int(item))
            elif item.type == 'BOOLEAN':
                value = str(item) == "да"
                return BoolLiteralNode(value=value)
            elif item.type == 'CHAR':
                char_str = str(item)[1:-1]
                return CharLiteralNode(value=char_str)
            elif item.type == 'STRING':
                string_str = str(item)[1:-1]
                return StringLiteralNode(value=string_str)

        elif isinstance(item, str):
            return IdentifierNode(name=item)
        return item

    def array_access(self, items):
        array_name, index = items[0], items[1]
        array_node = IdentifierNode(name=str(array_name))
        return ArrayAccessNode(array=array_node, index=index)

    def call_expr(self, items):
        name_token = items[0]
        args = items[1] if len(items) > 1 else []

        return CallNode(
            name=str(name_token),
            args=args
        )

    def arg_list(self, items):
        return items


    def IDENTIFIER(self, token):
        return str(token)

    def INTEGER(self, token):
        return IntLiteralNode(value=int(token))

    def BOOLEAN(self, token):
        value = str(token) == "да"
        return BoolLiteralNode(value=value)

    def CHAR(self, token):

        char_str = str(token)[1:-1]
        if char_str.startswith('\\'):

            if char_str == '\\n':
                char_str = '\n'
            elif char_str == '\\t':
                char_str = '\t'
            elif char_str == '\\r':
                char_str = '\r'
            elif char_str == '\\\\':
                char_str = '\\'
            elif char_str == "\\'":
                char_str = "'"

        return CharLiteralNode(value=char_str)

    def STRING(self, token):

        string_str = str(token)[1:-1]
        string_str = string_str.replace('\\n', '\n')
        string_str = string_str.replace('\\t', '\t')
        string_str = string_str.replace('\\r', '\r')
        string_str = string_str.replace('\\\\', '\\')
        string_str = string_str.replace('\\"', '"')

        return StringLiteralNode(value=string_str)



_parser = None


def _get_parser():
    global _parser
    if _parser is None:
        _parser = Lark(GRAMMAR, start='program', parser='lalr')
    return _parser


def parse(source: str) -> ProgramNode:
    try:
        parser = _get_parser()
        tree = parser.parse(source)
        transformer = MelASTBuilder()
        ast = transformer.transform(tree)
        return ast
    except LarkError as e:

        line = getattr(e, 'line', None)
        column = getattr(e, 'column', None)
        raise ParseError(str(e), line, column)
    except Exception as e:
        raise ParseError(f"Неожиданная ошибка при парсинге: {e}")


def parse_expression(source: str) -> ExpressionNode:
    try:

        expr_parser = Lark(GRAMMAR, start='expression', parser='lalr')
        tree = expr_parser.parse(source)
        transformer = MelASTBuilder()
        ast = transformer.transform(tree)
        return ast
    except LarkError as e:
        line = getattr(e, 'line', None)
        column = getattr(e, 'column', None)
        raise ParseError(str(e), line, column)



__all__ = ['parse', 'parse_expression', 'ParseError', 'MelASTBuilder']
