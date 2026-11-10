import argparse
import sys
from pathlib import Path

# Імпорти для побудови індексу (Лаба 2)
from .index import InvertedIndex
from .storage import save_pickle, load_pickle

# Імпорти для пошуку (Лаба 3)
from .models import Index
from .search import search
from .iterators import iter_documents


def main():
    parser = argparse.ArgumentParser(description="Findex Search Engine (Lab 03)")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # 1. Команда побудови індексу
    index_parser = subparsers.add_parser("index", help="Build and save inverted index")
    index_parser.add_argument("data_dir", type=Path, help="Directory with text files")
    index_parser.add_argument("--out", type=Path, default=Path("index.bin"), help="Output index file")

    # 2. Команда пошуку
    search_parser = subparsers.add_parser("search", help="Search the index")
    search_parser.add_argument("index_file", type=Path, help="Path to index file")
    search_parser.add_argument("query", type=str, help="Search query")

    # Аргументи для вибору алгоритму ранжування
    search_parser.add_argument(
        "--scorer",
        choices=["tfidf", "bm25"],
        default="tfidf",
        help="Ranking algorithm to use"
    )

    args = parser.parse_args()

    if args.command == "index":
        index = InvertedIndex()
        index.build(args.data_dir)
        save_pickle(index, args.out)
        print(f"Index saved to {args.out}")

    elif args.command == "search":
        # Завантажуємо дані з pickle
        data = load_pickle(args.index_file)

        # Створюємо об'єкт Index (наш новий клас-обгортка з models.py)
        index = Index(postings=data['postings'], doc_meta=data['doc_meta'])

        # Завантажуємо тексти документів у пам'ять для генерації сніпетів
        # (для великих корпусів це не оптимально, але для лаби підходить)
        corpus_dict = {}
        data_dir = Path("data")
        if data_dir.exists():
            for i, text in enumerate(iter_documents(data_dir)):
                corpus_dict[i] = text

        # Викликаємо функцію пошуку з ранжуванням
        print(f"Searching for: '{args.query}' using {args.scorer.upper()} scorer")

        try:
            results = search(
                index=index,
                query=args.query,
                scorer_type=args.scorer,
                top_k=5,
                corpus_dict=corpus_dict
            )

            if not results:
                print("No results found.")
            else:
                print(f"\n--- Top {len(results)} results ---")
                for r in results:
                    print(f"Doc ID: {r.doc_id} | Score: {r.score}")
                    if r.snippet:
                        print(f"   Snippet: {r.snippet}")
                    print("-" * 60)

        except Exception as e:
            print(f"Error during search: {e}")


if __name__ == "__main__":
    main()