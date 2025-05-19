from collections.abc import Callable
from typing import Any
from config.grammar_config import GrammarConfig


def comparator(fn: Callable[[Any, Any], bool]):
    def decorate(f: Callable):
        setattr(f, "__comparator__", fn)
        return f

    return decorate


def converter(fn: Callable[[Any], Any]):
    def decorate(f: Callable):
        setattr(f, "__converter__", fn)
        return f

    return decorate


def grammar(path: str, *, extra_constraints: list[str] | None = None):
    def decorate(f: Callable):
        setattr(f, "__grammar__", GrammarConfig(path, extra_constraints))
        return f
    return decorate

def parser(parser_obj):
    def decorate(f: Callable):
        setattr(f, "__parser__", parser_obj)
        return f

    return decorate
