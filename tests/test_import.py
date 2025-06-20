import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
print("Starting import test...")

try:
    print("Importing lark...")
    from lark import Lark, Transformer, Token, Tree
    print("lark imported ok")
    
    print("Importing mel_ast...")
    from mel_ast import *
    print("mel_ast imported ok")
    
    print("Importing mel_parser...")
    import mel_parser
    print("mel_parser imported ok")
    
    print("Testing parse function...")
    result = mel_parser.parse("алг тест; кон кон")
    print("Parse result:", type(result))
    
except Exception as e:
    print(f"Error during import: {e}")
    import traceback
    traceback.print_exc() 