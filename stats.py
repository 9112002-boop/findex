import time
import tracemalloc
from collections import Counter
from pathlib import Path
from iterators import iter_documents
from tokenizer import tokenize

def collect_stats(data_dir: Path) -> dict:
    tracemalloc.start()
    start_time = time.perf_counter()
    doc_count = 0
    total_tokens = 0
    term_freq = Counter()
    for doc_text in iter_documents(data_dir):
        doc_count += 1
        for token in tokenize(doc_text):
            total_tokens += 1
            term_freq[token] += 1
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return {'documents': doc_count, 'total_tokens': total_tokens, 'vocabulary_size': len(term_freq), 'time_seconds': round(time.perf_counter() - start_time, 4), 'peak_memory_mb': round(peak / 1024 / 1024, 2)}
