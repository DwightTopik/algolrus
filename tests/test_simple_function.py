import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import mel_parser
import importlib

                              
mel_parser._parser = None

                      
importlib.reload(mel_parser)

try:
    with open('examples/simple_function.alg', 'r', encoding='utf-8') as f:
        source = f.read()
    
    print("Тестируем простую функцию:")
    print(source)
    print("\n" + "="*50 + "\n")
    
    ast = mel_parser.parse(source)
    print(" УСПЕХ! Простая функция работает!")
    print(f"Количество функций: {len(ast.block.func_decls)}")
    
except Exception as e:
    print(f" Ошибка: {e}")
    import traceback
    traceback.print_exc() 