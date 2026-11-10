from typing import List, Set
from .models import Posting

def search_set(index, query_terms: List[str]) -> Set[int]:
    """Пошук через множини."""
    if not query_terms:
        return set()
    result_set = {p.doc_id for p in index.postings.get(query_terms[0], [])}
    for term in query_terms[1:]:
        term_set = {p.doc_id for p in index.postings.get(term, [])}
        result_set.intersection_update(term_set)
    return result_set

def search_merge(index, query_terms: List[str]) -> List[int]:
    """Пошук через двовказівниковий merge."""
    if not query_terms:
        return []
    lists = []
    for term in query_terms:
        postings = index.postings.get(term, [])
        lists.append([p.doc_id for p in postings])
    if not lists:
        return []
    lists.sort(key=len)
    result = lists[0]
    for i in range(1, len(lists)):
        result = _intersect_two_sorted(result, lists[i])
        if not result:
            break
    return result

def _intersect_two_sorted(list1: List[int], list2: List[int]) -> List[int]:
    result = []
    p1, p2 = 0, 0
    while p1 < len(list1) and p2 < len(list2):
        if list1[p1] == list2[p2]:
            result.append(list1[p1])
            p1 += 1
            p2 += 1
        elif list1[p1] < list2[p2]:
            p1 += 1
        else:
            p2 += 1
    return result