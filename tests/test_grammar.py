print("Testing grammar creation...")

try:
    from lark import Lark
    from mel_parser import GRAMMAR
    
    print("Creating parser with full grammar...")
    parser = Lark(GRAMMAR, start='program', parser='lalr')
    print("Parser created successfully")
    
except Exception as e:
    print(f"Error creating parser: {e}")
    import traceback
    traceback.print_exc() 