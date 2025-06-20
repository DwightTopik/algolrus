import argparse
import sys
from pathlib import Path
from typing import Optional

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from mel_parser import parse, ParseError
from mel_ast import ProgramNode


def read_source_file(filename: str) -> str:
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
    source = read_source_file(args.input)

    try:
        ast = parse(source)
        print("Парсинг успешен!")
        print("\nAST:")


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
    from interpreter import run_program

    source = read_source_file(args.input)

    try:
        ast = parse(source)


        if hasattr(args, 'optimize') and args.optimize:
            from optim import optimize_ast
            ast, stats = optimize_ast(ast)
            if hasattr(args, 'verbose') and args.verbose:
                print(f"Применено оптимизаций: {stats.get('total', 0)}")

        print(f"Запуск программы '{ast.name}'...")
        run_program(ast)
        print("\nПрограмма завершена успешно.")
    except ParseError as e:
        print(f"Ошибка парсинга: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_compile(args):
    from vm_codegen import compile_to_vm
    from vm_core import run_vm_program

    source = read_source_file(args.input)

    try:
        ast = parse(source)
        print(f"Компиляция программы '{ast.name}'...")


        if hasattr(args, 'optimize') and args.optimize:
            from optim import optimize_ast
            ast, stats = optimize_ast(ast)
            if hasattr(args, 'verbose') and args.verbose:
                print(f"Применено AST оптимизаций: {stats.get('total', 0)}")


        program = compile_to_vm(ast)


        if hasattr(args, 'optimize') and args.optimize:
            from optim import optimize_bytecode
            original_size = len(program.code)
            program, peephole_stats = optimize_bytecode(program)
            optimized_size = len(program.code)
            if hasattr(args, 'verbose') and args.verbose:
                print(f"Peephole оптимизации: {peephole_stats.get('total', 0)}")
                print(f"Размер байт-кода: {original_size} → {optimized_size} (-{original_size - optimized_size})")

        if args.output:

            program.save_to_file(args.output)
            print(f"Байт-код сохранен в '{args.output}'")
        else:

            print("Запуск скомпилированной программы...")
            output = run_vm_program(program)


            if output:
                for line in output:
                    print(line)

            print("\nПрограмма завершена успешно.")

    except ParseError as e:
        print(f"Ошибка парсинга: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Ошибка компиляции: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_vm(args):
    from vm_core import VMProgram, run_vm_program

    try:

        program = VMProgram.load_from_file(args.input)

        print(f"Запуск VM программы...")
        output = run_vm_program(program)


        if output:
            for line in output:
                print(line)

        print("\nПрограмма завершена успешно.")

    except FileNotFoundError:
        print(f"Файл '{args.input}' не найден", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Ошибка выполнения: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Компилятор русскоязычного подмножества Pascal",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  python main.py parse examples/hello.alg
  python main.py run examples/hello.alg
  python main.py compile examples/hello.alg
  python main.py vm hello.avm
"""
    )

    subparsers = parser.add_subparsers(dest='command', help='Доступные команды')


    parse_parser = subparsers.add_parser('parse', help='Парсинг исходного кода')
    parse_parser.add_argument('input', help='Входной файл .alg')
    parse_parser.set_defaults(func=cmd_parse)


    run_parser = subparsers.add_parser('run', help='Интерпретация программы')
    run_parser.add_argument('input', help='Входной файл .alg')
    run_parser.add_argument('-O', '--optimize', action='store_true', help='Включить оптимизации')
    run_parser.add_argument('-v', '--verbose', action='store_true', help='Подробный вывод')
    run_parser.set_defaults(func=cmd_run)


    compile_parser = subparsers.add_parser('compile', help='Компиляция в байт-код VM')
    compile_parser.add_argument('input', help='Входной файл .alg')
    compile_parser.add_argument('-o', '--output', help='Выходной файл .avm')
    compile_parser.add_argument('-O', '--optimize', action='store_true', help='Включить оптимизации')
    compile_parser.add_argument('-v', '--verbose', action='store_true', help='Подробный вывод')
    compile_parser.set_defaults(func=cmd_compile)


    vm_parser = subparsers.add_parser('vm', help='Запуск VM программы')
    vm_parser.add_argument('input', help='Входной файл .avm')
    vm_parser.set_defaults(func=cmd_vm)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()