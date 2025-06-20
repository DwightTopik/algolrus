from lark import Lark

# Простая грамматика для тестирования функций
func_grammar = '''
start: func_section

func_section: "функции" func_decl+

func_decl: "функция" IDENTIFIER "(" param_list? ")" (":" type_spec)? ";" block "кон"

param_list: param ("," param)*
param: IDENTIFIER ":" type_spec

type_spec: simple_type
simple_type: "цел" | "лог" | "сим"

block: "кон" stmt_list
stmt_list: statement*
statement: assignment ";"
assignment: IDENTIFIER ":=" IDENTIFIER

IDENTIFIER: /[а-яёa-z_][а-яёa-z0-9_]*/i

%import common.WS
%ignore WS
'''

try:
    parser = Lark(func_grammar, start='start', parser='lalr')
    print("Парсер создан успешно")
    
    # Тестируем простую функцию
    test_code = '''функции
    функция тест() : цел;
    кон
        а := б;
    кон
'''
    
    print("Тестируем код:", repr(test_code))
    tree = parser.parse(test_code)
    print("Парсинг успешен:", tree)
    
except Exception as e:
    print(f"Ошибка: {e}")
    import traceback
    traceback.print_exc() 