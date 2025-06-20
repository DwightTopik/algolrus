from mel_parser import parse

try:
    source = "алг тест; кон кон"
    print(f"Парсинг: {source}")
    
    ast = parse(source)
    print(f"AST создан: {type(ast)}")
    print(f"AST имя: {ast.name}")
    
    print("Вызываем pretty()...")
    pretty_result = ast.pretty()
    print(f"Pretty result type: {type(pretty_result)}")
    print(f"Pretty result length: {len(pretty_result)}")
    
    if pretty_result:
        print("Pretty result:")
        print(repr(pretty_result))
        print("---")
        print(pretty_result)
    else:
        print("Pretty result is empty!")
        
except Exception as e:
    print(f"Ошибка: {e}")
    import traceback
    traceback.print_exc() 