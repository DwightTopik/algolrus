print("Testing simple parse...")

try:
    from lark import Lark
    
    # Простейшая грамматика для теста
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
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc() 