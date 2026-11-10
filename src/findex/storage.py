import pickle
import time
import tracemalloc
from pathlib import Path


def save_pickle(index, filepath: Path):
    tracemalloc.start()
    start = time.perf_counter()
    data = {
        'postings': dict(index.postings),
        'doc_meta': index.doc_meta,
        'doc_lengths': index.doc_lengths
    }
    with open(filepath, 'wb') as f:
        pickle.dump(data, f)
    elapsed = time.perf_counter() - start
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    size_mb = filepath.stat().st_size / 1024 / 1024
    print(f"Saved to {filepath} ({size_mb:.2f} MB) in {elapsed:.4f}s, Peak: {peak/1024/1024:.2f} MB")

def load_pickle(filepath: Path):
    # УВАГА: pickle небезпечний для завантаження файлів з ненадійних джерел!
    tracemalloc.start()
    start = time.perf_counter()
    with open(filepath, 'rb') as f:
        data = pickle.load(f)
    elapsed = time.perf_counter() - start
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f"Loaded from {filepath} in {elapsed:.4f}s, Peak: {peak/1024/1024:.2f} MB")
    return data