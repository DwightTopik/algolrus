from mel_parser import parse

try:
    with open('examples/complete_test.alg', 'r', encoding='utf-8') as f:
        source = f.read()
    
    print("Парсинг complete_test.alg...")
    ast = parse(source)
    
    print(f"AST создан: {type(ast)}")
    print(f"Имя программы: {ast.name}")
    print(f"Количество переменных: {len(ast.block.var_decls)}")
    print(f"Количество операторов: {len(ast.block.statements)}")
    
    print("\nПеременные:")
    for var in ast.block.var_decls[:5]:  # Первые 5
        print(f"  {var.name}: {var.var_type}")
        
    print("\nПервые 5 операторов:")
    for i, stmt in enumerate(ast.block.statements[:5]):
        print(f"  {i+1}. {type(stmt).__name__}")
        
    print(f"\n... и ещё {len(ast.block.statements) - 5} операторов")
    print("✅ AST корректно построен!")
    
except Exception as e:
    print(f"Ошибка: {e}")
    import traceback
    traceback.print_exc() 