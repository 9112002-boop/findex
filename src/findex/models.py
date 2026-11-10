from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class DocMeta:
    doc_id: int
    title: str
    length: int

@dataclass(frozen=True, slots=True)
class Posting:
    doc_id: int
    freq: int