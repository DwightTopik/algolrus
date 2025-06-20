from lark import Lark

                                
working_grammar = '''
start: program

program: "алг" IDENTIFIER ";" block "кон"

block: var_section? "кон" func_section_or_empty stmt_list

func_section_or_empty: func_section
                     | empty

empty:

var_section: "нач" var_decl_list
var_decl_list: var_decl+
var_decl: IDENTIFIER ":" type_spec ";"

func_section: func_section_keyword func_decl+ "кон"
func_section_keyword: IDENTIFIER

func_decl: func_keyword IDENTIFIER "(" param_list? ")" (":" type_spec)? ";" func_body "кон"
func_keyword: IDENTIFIER

func_body: stmt_list

stmt_list: statement*
statement: assignment ";"
assignment: IDENTIFIER ASSIGN IDENTIFIER
ASSIGN: ":="

param_list: param ("," param)*
param: IDENTIFIER ":" type_spec

type_spec: simple_type
simple_type: "цел" | "лог" | "сим"

IDENTIFIER: /[а-яёa-z_][а-яёa-z0-9_]*/i

%import common.WS
%ignore WS
'''

                          
class TestTransformer:
    def func_section_keyword(self, items):
        keyword = str(items[0])
        if keyword != "функции":
            raise Exception(f"Ожидается 'функции', получено '{keyword}'")
        return keyword
    
    def func_keyword(self, items):
        keyword = str(items[0])
        if keyword != "функция":
            raise Exception(f"Ожидается 'функция', получено '{keyword}'")
        return keyword

try:
    parser = Lark(working_grammar, start='start', parser='lalr')
    print("Парсер создан успешно")
    
                     
    test_code = '''алг тест;
нач
    а : цел;
кон
функции
    функция тест() : цел;
    кон
кон
    а := б;
кон'''
    
    print("Тестируем код:")
    print(test_code)
    print("\n" + "="*50 + "\n")
    
    tree = parser.parse(test_code)
    print(" Парсинг успешен!")
    print("Дерево разбора:", tree)
    
except Exception as e:
    print(f" Ошибка: {e}")
    import traceback
    traceback.print_exc() 