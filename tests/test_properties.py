from hypothesis import given, strategies as st
from findex.tokenizer import tokenize

@given(st.text())
def test_tokenize_never_crashes(text: str):
    tokens = list(tokenize(text))
    assert isinstance(tokens, list)
