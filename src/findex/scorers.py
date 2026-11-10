import math

from .models import Index


class TfIdfScorer:
    def __init__(self, index: Index):
        self.index = index

    def score(self, query_terms: list[str]) -> dict[int, float]:
        scores = {}
        N = self.index.num_docs
        if N == 0:
            return scores

        for term in query_terms:
            df = self.index.df(term)
            if df == 0:
                continue

            # Виправлена формула IDF зі згладжуванням (Smoothing)
            # Гарантує, що навіть якщо термін є у всіх документах (df == N), idf > 0
            idf = math.log((N + 1) / (df + 1)) + 1.0

            for posting in self.index[term]:
                tf = posting.freq
                doc_len = self.index.doc_meta[posting.doc_id].length

                # Нормалізація на довжину документа
                tf_norm = tf / doc_len if doc_len > 0 else 0
                score = tf_norm * idf

                scores[posting.doc_id] = scores.get(posting.doc_id, 0.0) + score

        return scores


class BM25Scorer:
    def __init__(self, index: Index, k1: float = 1.5, b: float = 0.75):
        self.index = index
        self.k1 = k1
        self.b = b

    def score(self, query_terms: list[str]) -> dict[int, float]:
        scores = {}
        N = self.index.num_docs
        avgdl = self.index.avg_doc_length
        if N == 0 or avgdl == 0:
            return scores

        for term in query_terms:
            df = self.index.df(term)
            if df == 0:
                continue

            # Формула IDF для BM25
            idf = math.log((N - df + 0.5) / (df + 0.5) + 1.0)

            for posting in self.index[term]:
                tf = posting.freq
                doc_len = self.index.doc_meta[posting.doc_id].length

                # Формула BM25
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * (doc_len / avgdl))
                score = idf * (numerator / denominator)

                scores[posting.doc_id] = scores.get(posting.doc_id, 0.0) + score

        return scores