from mel_parser import parse

source = '''алг тест;
нач
    а : цел;
кон
    а := 1 + 2;
кон'''

try:
    print("Parsing...")
    ast = parse(source)
    print("AST created:", type(ast))
    print("Calling pretty()...")
    result = ast.pretty()
    print('Result length:', len(result))
    print('Result repr:', repr(result))
    if result:
        print('Result:')
        print(result)
    else:
        print('Result is empty or None')
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc() 