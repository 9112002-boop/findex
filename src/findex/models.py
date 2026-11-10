from dataclasses import dataclass
from functools import cached_property
from collections.abc import Mapping
from typing import Iterator


@dataclass(frozen=True, slots=True)
class DocMeta:
    doc_id: int
    title: str
    length: int


@dataclass(frozen=True, slots=True)
class Posting:
    doc_id: int
    freq: int


@dataclass(order=True)
class SearchResult:
    score: float
    doc_id: int
    snippet: str = ""


class Index(Mapping[str, list[Posting]]):
    """Обгортка над словником постінгів, що реалізує протокол Mapping."""

    def __init__(self, postings: dict[str, list[Posting]], doc_meta: dict[int, DocMeta]) -> None:
        self._postings = postings
        self.doc_meta = doc_meta

    def __getitem__(self, term: str) -> list[Posting]:
        return self._postings[term]

    def __iter__(self) -> Iterator[str]:
        return iter(self._postings)

    def __len__(self) -> int:
        return len(self._postings)

    def __repr__(self) -> str:
        return f"<Index: {len(self)} terms, {len(self.doc_meta)} docs>"

    @property
    def num_docs(self) -> int:
        return len(self.doc_meta)

    @cached_property
    def avg_doc_length(self) -> float:
        if not self.doc_meta:
            return 0.0
        total_len = sum(meta.length for meta in self.doc_meta.values())
        return total_len / len(self.doc_meta)

    def df(self, term: str) -> int:
        """Document Frequency - кількість документів, де зустрічається термін."""
        return len(self._postings.get(term, []))