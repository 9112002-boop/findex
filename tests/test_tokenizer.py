import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tokenizer import tokenize


def test_apostrophe():
    assert list(tokenize("don't")) == ["don't"]

def test_hyphen():
    assert list(tokenize("well-known")) == ["well-known"]

def test_numbers():
    assert list(tokenize("2024")) == ["2024"]

def test_unicode():
    assert list(tokenize("file")) == ["file"]
