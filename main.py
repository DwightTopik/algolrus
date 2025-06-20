import argparse
import sys
from pathlib import Path
from typing import Optional

# Настройка кодировки для Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from mel_parser import parse, ParseError
from mel_ast import ProgramNode


def read_source_file(filename: str) -> str:
    """Читает исходный файл"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"Ошибка: файл '{filename}' не найден", file=sys.stderr)
        sys.exit(1)
    except UnicodeDecodeError:
        print(f"Ошибка: не удается прочитать файл '{filename}' в кодировке UTF-8", file=sys.stderr)
        sys.exit(1)


def cmd_parse(args):
    """Команда парсинга - выводит AST"""
    source = read_source_file(args.input)
    
    try:
        ast = parse(source)
        print("Парсинг успешен!")
        print("\nAST:")
        
        # Безопасный вывод AST
        try:
            ast_str = ast.pretty()
            print(ast_str)
        except Exception as e:
            print(f"Ошибка при выводе AST: {e}")
            print(f"AST тип: {type(ast)}")
            print(f"AST имя: {getattr(ast, 'name', 'неизвестно')}")
            
    except ParseError as e:
        print(f"Ошибка парсинга: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_run(args):
    """Команда запуска через интерпретатор"""
    print("Интерпретатор пока не реализован", file=sys.stderr)
    sys.exit(1)


def cmd_compile(args):
    """Команда компиляции в байт-код VM"""
    print("VM компилятор пока не реализован", file=sys.stderr)
    sys.exit(1)


def main():
    """Главная функция"""
    parser = argparse.ArgumentParser(
        description="Компилятор русскоязычного подмножества Pascal",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  python main.py parse examples/hello.alg     # Парсинг и вывод AST
  python main.py run examples/hello.alg       # Запуск через интерпретатор
  python main.py compile examples/hello.alg   # Компиляция в байт-код VM
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Доступные команды')
    
    # Команда parse
    parse_parser = subparsers.add_parser('parse', help='Парсинг и вывод AST')
    parse_parser.add_argument('input', help='Входной файл .alg')
    parse_parser.set_defaults(func=cmd_parse)
    
    # Команда run
    run_parser = subparsers.add_parser('run', help='Запуск через интерпретатор')
    run_parser.add_argument('input', help='Входной файл .alg')
    run_parser.set_defaults(func=cmd_run)
    
    # Команда compile
    compile_parser = subparsers.add_parser('compile', help='Компиляция в байт-код VM')
    compile_parser.add_argument('input', help='Входной файл .alg')
    compile_parser.add_argument('-o', '--output', help='Выходной файл .avm')
    compile_parser.set_defaults(func=cmd_compile)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Выполняем команду
    args.func(args)


if __name__ == '__main__':
    main()

