from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from functools import cached_property


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
    def __init__(self, postings: dict[str, list[Posting]], doc_meta: dict[int, DocMeta]) -> None:
        self._postings: dict[str, list[Posting]] = postings
        self.doc_meta: dict[int, DocMeta] = doc_meta

    def __getitem__(self, term: str) -> list[Posting]:
        return self._postings[term]

    def __iter__(self) -> Iterator[str]:
        return iter(self._postings)

    def __len__(self) -> int:
        return len(self._postings)

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
        return len(self._postings.get(term, []))