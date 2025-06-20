from lark import Lark
from mel_parser import GRAMMAR, MelASTBuilder

# Тестируем только type_spec
type_grammar = '''
start: type_spec

type_spec: simple_type
         | array_type

simple_type: "цел"      -> integer_type
           | "лог"      -> boolean_type
           | "сим"      -> char_type
           | "строка"   -> string_type

array_type: "таб" "[" INTEGER "]" simple_type

INTEGER: /\\d+/

%import common.WS
%ignore WS
'''

print("Тестируем типы...")

try:
    parser = Lark(type_grammar, start='start', parser='lalr')
    print("Парсер создан")
    
    # Тестируем простой тип
    tree = parser.parse("цел")
    print("Простой тип парсится:", tree)
    
    # Тестируем массив
    tree = parser.parse("таб[5] цел")
    print("Массив парсится:", tree)
    
    # Тестируем с трансформером
    transformer = MelASTBuilder()
    
    tree = parser.parse("цел")
    result = transformer.transform(tree)
    print("Простой тип с трансформером:", result)
    
    tree = parser.parse("таб[5] цел")
    result = transformer.transform(tree)
    print("Массив с трансформером:", result)
    
except Exception as e:
    print(f"Ошибка: {e}")
    import traceback
    traceback.print_exc() 