import time
import tracemalloc
from collections import Counter
from pathlib import Path
from iterators import iter_documents
from tokenizer import tokenize

def collect_stats_greedy(data_dir: Path) -> dict:
    tracemalloc.start()
    start_time = time.perf_counter()
    documents = list(iter_documents(data_dir))
    all_tokens = []
    for doc in documents:
        all_tokens.extend(tokenize(doc))
    term_freq = Counter(all_tokens)
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return {'documents': len(documents), 'total_tokens': len(all_tokens), 'vocabulary_size': len(term_freq), 'time_seconds': round(time.perf_counter() - start_time, 4), 'peak_memory_mb': round(peak / 1024 / 1024, 2)}
