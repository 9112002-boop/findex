import time
import heapq
from functools import wraps, lru_cache
from typing import List, Dict, Callable
from .models import Index, SearchResult
from .scorers import TfIdfScorer, BM25Scorer
from .query_parser import parse_query


def timed(func: Callable):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        print(f"[@timed] {func.__name__} took {elapsed:.4f}s")
        return result

    return wrapper


def make_snippet(text: str, query_terms: List[str], window: int = 80) -> str:
    """Створює сніпет навколо першого входження терміна."""
    text_lower = text.lower()
    for term in query_terms:
        idx = text_lower.find(term)
        if idx != -1:
            start = max(0, idx - window)
            end = min(len(text), idx + len(term) + window)
            snippet = text[start:end]
            # Підсвітка (проста)
            for t in query_terms:
                snippet = snippet.replace(t, f"**{t}**")
                snippet = snippet.replace(t.capitalize(), f"**{t.capitalize()}**")
            return f"...{snippet}..."
    return text[:window] + "..."


@timed
def search(index: Index, query: str, scorer_type: str = "tfidf", top_k: int = 10, corpus_dict: dict = None) -> List[
    SearchResult]:
    """Головна функція пошуку з ранжуванням."""
    # Оцінка
    if scorer_type == "bm25":
        scorer = BM25Scorer(index)
    else:
        scorer = TfIdfScorer(index)

    # Отримуємо AST запиту (для простоти беремо терміни з нього)
    # У реальному житті тут треба витягнути всі Term з AST
    terms = [t.lower() for t in query.split() if t.isalnum()]

    scores = scorer.score(terms)

    # Беремо топ-k через heapq
    top_docs = heapq.nlargest(top_k, scores.items(), key=lambda x: x[1])

    results = []
    for doc_id, score in top_docs:
        # Генеруємо сніпет (якщо є текст)
        snip = ""
        if corpus_dict and doc_id in corpus_dict:
            snip = make_snippet(corpus_dict[doc_id], terms)

        results.append(SearchResult(score=round(score, 4), doc_id=doc_id, snippet=snip))

    return results