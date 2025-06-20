import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import mel_parser

                              
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