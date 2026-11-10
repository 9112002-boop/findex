import time
import tracemalloc
from collections import defaultdict
from pathlib import Path
from typing import Any

from .iterators import iter_documents
from .models import DocMeta, Posting
from .tokenizer import tokenize


def build_partial(file_paths: list[Path], start_doc_id: int) -> dict[str, Any]:
    """
    Обробляє список файлів і повертає частковий індекс.
    doc_id починається з start_doc_id, щоб уникнути колізій при паралельній роботі.
    """
    postings: dict[str, list[Posting]] = defaultdict(list)
    doc_meta: dict[int, DocMeta] = {}

    current_doc_id = start_doc_id
    for file_path in sorted(file_paths):
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()

        term_freq = defaultdict(int)
        length = 0
        for token in tokenize(text):
            term_freq[token] += 1
            length += 1

        doc_meta[current_doc_id] = DocMeta(doc_id=current_doc_id, title=file_path.name, length=length)

        for term, freq in term_freq.items():
            postings[term].append(Posting(doc_id=current_doc_id, freq=freq))

        current_doc_id += 1

    return {"postings": dict(postings), "doc_meta": doc_meta}


class InvertedIndex:
    def __init__(self) -> None:
        self.postings: dict[str, list[Posting]] = defaultdict(list)
        self.doc_meta: dict[int, DocMeta] = {}

    @staticmethod
    def merge(partials: list[dict[str, Any]]) -> "InvertedIndex":
        """Зливає часткові індекси в один."""
        idx = InvertedIndex()
        for partial in partials:
            for term, postings in partial["postings"].items():
                idx.postings[term].extend(postings)
            idx.doc_meta.update(partial["doc_meta"])

        # Сортуємо постінги для кожного терміна за doc_id (як у лабі 2)
        for term in idx.postings:
            idx.postings[term].sort(key=lambda x: x.doc_id)

        return idx

    def build(self, data_dir: Path) -> None:
        """Послідовна збірка (для сумісності з лабою 4)."""
        tracemalloc.start()
        start_time = time.perf_counter()

        files = list(data_dir.glob("*.txt"))
        partial = build_partial(files, start_doc_id=0)

        self.postings = defaultdict(list, partial["postings"])
        self.doc_meta = partial["doc_meta"]

        for term in self.postings:
            self.postings[term].sort(key=lambda x: x.doc_id)

        _current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        elapsed = time.perf_counter() - start_time
        print(f"Index built: {len(self.doc_meta)} docs, {len(self.postings)} unique terms")
        print(f"Time: {elapsed:.2f}s, Peak memory: {peak / 1024 / 1024:.2f} MB")