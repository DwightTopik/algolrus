import sys
import os

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

print("Testing simple parse...")

try:
    from lark import Lark
    
    # Простая грамматика для тестирования
    simple_grammar = '''
    program: "алг" IDENTIFIER ";" "кон" "кон"
    IDENTIFIER: /[а-яё_][а-яё0-9_]*/i
    %import common.WS
    %ignore WS
    '''
    
    print("Creating parser...")
    parser = Lark(simple_grammar, start='program', parser='lalr')
    print("Parser created")
    
    print("Testing parse...")
    result = parser.parse("алг тест; кон кон")
    print("Parse successful:", result)
    
    print("Testing full parser...")
    from mel_parser import parse
    
    test_program = "алг тест; кон кон"
    ast = parse(test_program)
    print("Full parser successful:", type(ast))
    print(f"Program name: {ast.name}")
    
    print("Тест простого парсинга завершен успешно")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc() 