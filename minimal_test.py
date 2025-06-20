import sys
sys.stdout.reconfigure(encoding='utf-8')

print("Test started")

try:
    from mel_parser import parse
    print("Parser imported")
    
    source = "алг тест; кон кон"
    print(f"Parsing: {source}")
    
    ast = parse(source)
    print(f"AST type: {type(ast)}")
    print(f"AST name: {ast.name}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc() 