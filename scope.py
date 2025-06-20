from typing import Dict, Optional, List, Any
from dataclasses import dataclass
from mel_types import Type, FunctionType
from mel_ast import SourcePosition


class SemanticError(Exception):
    """Исключение для семантических ошибок"""
    def __init__(self, message: str, position: Optional[SourcePosition] = None):
        self.message = message
        self.position = position
        super().__init__(self.format_message())
    
    def format_message(self) -> str:
        if self.position:
            return f"Семантическая ошибка на {self.position}: {self.message}"
        return f"Семантическая ошибка: {self.message}"


@dataclass
class Symbol:
    """Символ в таблице символов"""
    name: str
    symbol_type: Type
    category: str  # 'var', 'func', 'param'
    position: Optional[SourcePosition] = None
    value: Optional[Any] = None  # Для константных значений
    
    # Дополнительные атрибуты для VM
    local_index: Optional[int] = None  # Индекс в локальном кадре
    is_global: bool = False


class Scope:
    """Область видимости"""
    
    def __init__(self, parent: Optional['Scope'] = None, name: str = ""):
        self.parent = parent
        self.name = name
        self.symbols: Dict[str, Symbol] = {}
        self.children: List['Scope'] = []
        
        # Для VM - отслеживание локальных переменных
        self.local_count = 0
        
        if parent:
            parent.children.append(self)
    
    def declare(self, name: str, symbol: Symbol) -> None:
        """Объявляет символ в текущей области видимости"""
        if name in self.symbols:
            existing = self.symbols[name]
            raise SemanticError(
                f"Символ '{name}' уже объявлен в этой области видимости",
                symbol.position
            )
        
        # Для переменных присваиваем индекс в локальном кадре
        if symbol.category == 'var' and not symbol.is_global:
            symbol.local_index = self.local_count
            self.local_count += 1
        
        self.symbols[name] = symbol
    
    def lookup(self, name: str) -> Optional[Symbol]:
        """Ищет символ в текущей и родительских областях видимости"""
        if name in self.symbols:
            return self.symbols[name]
        
        if self.parent:
            return self.parent.lookup(name)
        
        return None
    
    def lookup_local(self, name: str) -> Optional[Symbol]:
        """Ищет символ только в текущей области видимости"""
        return self.symbols.get(name)
    
    def resolve(self, name: str, position: Optional[SourcePosition] = None) -> Symbol:
        """Ищет символ и бросает исключение, если не найден"""
        symbol = self.lookup(name)
        if symbol is None:
            raise SemanticError(f"Неизвестный идентификатор '{name}'", position)
        return symbol
    
    def get_all_symbols(self) -> Dict[str, Symbol]:
        """Возвращает все символы в области видимости"""
        return self.symbols.copy()
    
    def get_depth(self) -> int:
        """Возвращает глубину вложенности области видимости"""
        depth = 0
        current = self.parent
        while current:
            depth += 1
            current = current.parent
        return depth
    
    def is_global(self) -> bool:
        """Проверяет, является ли область глобальной"""
        return self.parent is None
    
    def __str__(self) -> str:
        return f"Scope({self.name}, symbols={len(self.symbols)})"
    
    def pretty_print(self, indent: int = 0) -> str:
        """Красивый вывод области видимости"""
        spaces = "  " * indent
        result = f"{spaces}{self.name or 'unnamed'} ({len(self.symbols)} symbols)\n"
        
        for name, symbol in self.symbols.items():
            result += f"{spaces}  {name}: {symbol.symbol_type} ({symbol.category})\n"
        
        for child in self.children:
            result += child.pretty_print(indent + 1)
        
        return result


class ScopeManager:
    """Менеджер областей видимости"""
    
    def __init__(self):
        self.global_scope = Scope(name="global")
        self.current_scope = self.global_scope
        self.scope_stack: List[Scope] = [self.global_scope]
    
    def enter_scope(self, name: str = "") -> Scope:
        """Входит в новую область видимости"""
        new_scope = Scope(parent=self.current_scope, name=name)
        self.current_scope = new_scope
        self.scope_stack.append(new_scope)
        return new_scope
    
    def exit_scope(self) -> Optional[Scope]:
        """Выходит из текущей области видимости"""
        if len(self.scope_stack) <= 1:
            raise SemanticError("Попытка выйти из глобальной области видимости")
        
        old_scope = self.scope_stack.pop()
        self.current_scope = self.scope_stack[-1]
        return old_scope
    
    def declare(self, name: str, symbol: Symbol) -> None:
        """Объявляет символ в текущей области видимости"""
        self.current_scope.declare(name, symbol)
    
    def lookup(self, name: str) -> Optional[Symbol]:
        """Ищет символ начиная с текущей области видимости"""
        return self.current_scope.lookup(name)
    
    def resolve(self, name: str, position: Optional[SourcePosition] = None) -> Symbol:
        """Ищет символ и бросает исключение, если не найден"""
        return self.current_scope.resolve(name, position)
    
    def get_current_scope(self) -> Scope:
        """Возвращает текущую область видимости"""
        return self.current_scope
    
    def get_global_scope(self) -> Scope:
        """Возвращает глобальную область видимости"""
        return self.global_scope
    
    def is_in_global_scope(self) -> bool:
        """Проверяет, находимся ли в глобальной области видимости"""
        return self.current_scope == self.global_scope
    
    def get_scope_depth(self) -> int:
        """Возвращает текущую глубину вложенности"""
        return len(self.scope_stack) - 1
    
    def pretty_print(self) -> str:
        """Красивый вывод всех областей видимости"""
        return self.global_scope.pretty_print()


def create_builtin_scope() -> Scope:
    """Создает область видимости с встроенными функциями"""
    from mel_types import BUILTIN_FUNCTIONS
    
    builtin_scope = Scope(name="builtin")
    
    for name, func_type in BUILTIN_FUNCTIONS.items():
        symbol = Symbol(
            name=name,
            symbol_type=func_type,
            category='builtin',
            is_global=True
        )
        builtin_scope.declare(name, symbol)
    
    return builtin_scope


def create_scope_manager_with_builtins() -> ScopeManager:
    """Создает менеджер областей видимости с встроенными функциями"""
    manager = ScopeManager()
    
    # Добавляем встроенные функции в глобальную область
    from mel_types import BUILTIN_FUNCTIONS
    
    for name, func_type in BUILTIN_FUNCTIONS.items():
        symbol = Symbol(
            name=name,
            symbol_type=func_type,
            category='builtin',
            is_global=True
        )
        manager.declare(name, symbol)
    
    return manager


# Экспорт
__all__ = [
    'SemanticError', 'Symbol', 'Scope', 'ScopeManager',
    'create_builtin_scope', 'create_scope_manager_with_builtins'
]
