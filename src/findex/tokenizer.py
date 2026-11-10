import re
import unicodedata
from typing import Iterator

TOKEN_PATTERN = re.compile(r"[\w']+(?:-[\w']+)*", re.UNICODE)

def tokenize(text: str) -> Iterator[str]:
    normalized = unicodedata.normalize("NFKC", text)
    for match in TOKEN_PATTERN.finditer(normalized):
        yield match.group().lower()
