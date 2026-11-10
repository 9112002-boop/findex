import argparse
import sys
from pathlib import Path
from .index import InvertedIndex
from .search import search_set, search_merge
from .storage import save_pickle, load_pickle


def main():
    parser = argparse.ArgumentParser(description="Findex Search Engine")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Команда побудови індексу
    index_parser = subparsers.add_parser("index")
    index_parser.add_argument("data_dir", type=Path, help="Directory with text files")
    index_parser.add_argument("--out", type=Path, default=Path("index.bin"), help="Output index file")

    # Команда пошуку
    search_parser = subparsers.add_parser("search")
    search_parser.add_argument("index_file", type=Path, help="Path to index file")
    search_parser.add_argument("query", type=str, help="Search query (terms separated by space)")
    search_parser.add_argument("--engine", choices=["merge", "set"], default="merge", help="Search algorithm")

    args = parser.parse_args()

    if args.command == "index":
        index = InvertedIndex()
        index.build(args.data_dir)
        save_pickle(index, args.out)
        print(f"Index saved to {args.out}")

    elif args.command == "search":
        data = load_pickle(args.index_file)

        # Відновлюємо об'єкт індексу зі словника
        class LoadedIndex:
            pass

        index = LoadedIndex()
        index.postings = data['postings']
        index.doc_meta = data['doc_meta']

        terms = args.query.lower().split()
        print(f"Searching for: {terms} using {args.engine} engine")

        if args.engine == "set":
            results = search_set(index, terms)
            print(f"Found {len(results)} docs: {sorted(results)}")
        else:
            results = search_merge(index, terms)
            print(f"Found {len(results)} docs: {results}")


if __name__ == "__main__":
    main()