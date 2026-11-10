import numpy as np
from .models import Index


class BM25ScorerNumpy:
    def __init__(self, index: Index, k1: float = 1.5, b: float = 0.75):
        self.index = index
        self.k1 = k1
        self.b = b

        # Конвертуємо всі постінги в масиви NumPy (один раз при створенні)
        self.numpy_postings = {}
        for term, postings in index._postings.items():
            doc_ids = np.array([p.doc_id for p in postings], dtype=np.int32)
            freqs = np.array([p.freq for p in postings], dtype=np.int32)
            self.numpy_postings[term] = (doc_ids, freqs)

        # Довжини документів як один масив
        self.doc_lengths = np.zeros(index.num_docs, dtype=np.float32)
        for doc_id, meta in index.doc_meta.items():
            self.doc_lengths[doc_id] = meta.length

        self.avg_doc_length = np.mean(self.doc_lengths) if len(self.doc_lengths) > 0 else 1.0

    def score(self, query_terms: list[str], k: int = 10) -> list[tuple[int, float]]:
        # Ініціалізуємо масив балів для всіх документів
        scores = np.zeros(self.index.num_docs, dtype=np.float32)

        for term in query_terms:
            if term not in self.numpy_postings:
                continue

            doc_ids, freqs = self.numpy_postings[term]
            df = len(doc_ids)
            N = self.index.num_docs

            if N == 0:
                continue

            # Обчислюємо IDF
            idf = np.log((N - df + 0.5) / (df + 0.5) + 1.0)

            # Векторизоване обчислення BM25
            tf = freqs.astype(np.float32)
            doc_len = self.doc_lengths[doc_ids]

            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (1 - self.b + self.b * (doc_len / self.avg_doc_length))

            # Додаємо бали до відповідних документів (np.add.at працює з дублікатами)
            np.add.at(scores, doc_ids, idf * (numerator / denominator))

        # Беремо топ-k через argpartition
        if len(scores) <= k:
            top_indices = np.argsort(scores)[::-1]
        else:
            top_indices = np.argpartition(scores, -k)[-k:]
            top_indices = top_indices[np.argsort(scores[top_indices])[::-1]]

        # Повертаємо список (doc_id, score) для тих, у кого score > 0
        return [(int(idx), float(scores[idx])) for idx in top_indices if scores[idx] > 0]