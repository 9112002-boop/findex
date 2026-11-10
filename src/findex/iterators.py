from collections.abc import Generator
from pathlib import Path


def iter_documents(data_dir: str | Path) -> Generator[str, None, None]:
    data_path = Path(data_dir)
    for file_path in sorted(data_path.glob('*.txt')):
        with open(file_path, 'r', encoding='utf-8') as f:
            yield f.read()
