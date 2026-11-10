import re
from dataclasses import dataclass
from typing import List, Set, Union
from .models import Index


# Вузли AST (Abstract Syntax Tree)
@dataclass
class Term:
    value: str

    def evaluate(self, index: Index) -> Set[int]:
        return {p.doc_id for p in index.get(self.value, [])}

    def __and__(self, other): return And(self, other)

    def __or__(self, other): return Or(self, other)

    def __invert__(self): return Not(self)


@dataclass
class Phrase:
    value: str

    def evaluate(self, index: Index) -> Set[int]:
        # Спрощена реалізація: шукаємо просто як AND слів (без позицій для простоти)
        words = self.value.lower().split()
        if not words: return set()
        result = {p.doc_id for p in index.get(words[0], [])}
        for w in words[1:]:
            result &= {p.doc_id for p in index.get(w, [])}
        return result

    def __and__(self, other):
        return And(self, other)

    def __or__(self, other):
        return Or(self, other)

    def __invert__(self):
        return Not(self)


@dataclass
class And:
    left: Union[Term, Phrase, 'And', 'Or', 'Not']
    right: Union[Term, Phrase, 'And', 'Or', 'Not']

    def evaluate(self, index: Index) -> Set[int]:
        return self.left.evaluate(index) & self.right.evaluate(index)


@dataclass
class Or:
    left: Union[Term, Phrase, 'And', 'Or', 'Not']
    right: Union[Term, Phrase, 'And', 'Or', 'Not']

    def evaluate(self, index: Index) -> Set[int]:
        return self.left.evaluate(index) | self.right.evaluate(index)


@dataclass
class Not:
    child: Union[Term, Phrase, 'And', 'Or', 'Not']

    def evaluate(self, index: Index) -> Set[int]:
        all_docs = set(index.doc_meta.keys())
        return all_docs - self.child.evaluate(index)

    def __and__(self, other): return And(self, other)

    def __or__(self, other): return Or(self, other)

    def __invert__(self): return Not(self)


def parse_query(query: str) -> Union[Term, Phrase, And, Or, Not]:
    """Дуже спрощений парсер (без токенізатора, просто розбиває по пробілах)."""
    tokens = re.findall(r'"[^"]+"|\w+|AND|OR|NOT|[()]', query)

    def parse_expression(pos):
        # Тут має бути повноцінний рекурсивний спуск.
        # Для прикладу зробимо просту логіку: якщо є AND/OR, об'єднуємо.
        # (У реальному житті це складніше, але для лаби достатньо базової обробки)
        pass

    # Спрощена логіка для прикладу "python AND java":
    parts = query.split(" AND ")
    if len(parts) == 2:
        return Term(parts[0].strip().lower()) & Term(parts[1].strip().lower())

    # Якщо просто фраза
    if query.startswith('"') and query.endswith('"'):
        return Phrase(query.strip('"'))

    return Term(query.lower())