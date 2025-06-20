import mel_parser

# Принудительно сбрасываем кэш
mel_parser._parser = None

try:
    with open('examples/test_functions_fixed.alg', 'r', encoding='utf-8') as f:
        source = f.read()
    
    print("Код для парсинга:")
    print(source)
    print("\n" + "="*50 + "\n")
    
    ast = mel_parser.parse(source)
    print("Парсинг успешен!")
    print("AST:", type(ast))
    
except Exception as e:
    print(f"Полная ошибка: {e}")
    import traceback
    traceback.print_exc() 