from collections import defaultdict
from pathlib import Path
from typing import Dict, List
import time
import tracemalloc

# Зверніть увагу на крапку перед iterators та tokenizer.
# Це означає, що ми шукаємо їх у тій самій папці (src/findex)
from .iterators import iter_documents
from .tokenizer import tokenize
from .models import Posting, DocMeta


class InvertedIndex:
    def __init__(self):
        # термін -> список постінгів
        self.postings: Dict[str, List[Posting]] = defaultdict(list)
        self.doc_meta: Dict[int, DocMeta] = {}
        self.doc_lengths: Dict[int, int] = {}

    def build(self, data_dir: Path):
        tracemalloc.start()
        start_time = time.perf_counter()

        doc_id = 0
        for doc_text in iter_documents(data_dir):
            # Тимчасовий словник для підрахунку частоти в межах одного документа
            term_freq = defaultdict(int)
            length = 0

            for token in tokenize(doc_text):
                term_freq[token] += 1
                length += 1

            # Зберігаємо метадані документа
            self.doc_meta[doc_id] = DocMeta(doc_id=doc_id, title=f"Doc {doc_id}", length=length)
            self.doc_lengths[doc_id] = length

            # Додаємо постінги
            for term, freq in term_freq.items():
                self.postings[term].append(Posting(doc_id=doc_id, freq=freq))

            doc_id += 1

        # Сортуємо постінги для кожного терміна за doc_id (обов'язково для merge)
        for term in self.postings:
            self.postings[term].sort(key=lambda x: x.doc_id)

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        elapsed = time.perf_counter() - start_time

        print(f"Index built: {doc_id} docs, {len(self.postings)} unique terms")
        print(f"Time: {elapsed:.2f}s, Peak memory: {peak / 1024 / 1024:.2f} MB")
        return self