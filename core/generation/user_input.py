import importlib.util
import inspect
from typing import Any

from config.grammar_config import GrammarConfig
from input.input_parser import InputParser


def load_user_module(path: str):
    spec = importlib.util.spec_from_file_location("user_defined_functions", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def get_user_classes(module, class_name: str | None = None) -> list[tuple[str, type]]:
    if class_name:
        if not hasattr(module, class_name):
            raise ValueError(f"Class '{class_name}' not found in module")
        return [(class_name, getattr(module, class_name))]

    classes = []
    for name, obj in inspect.getmembers(module, inspect.isclass):
        if obj.__module__ == module.__name__:
            classes.append((name, obj))
    if not classes:
        available = [name for name, obj in inspect.getmembers(module, inspect.isclass)]
        raise ValueError(f"No user-defined classes found in module. Available classes: {available}")
    return classes


def extract_overrides(module) -> dict[str, dict[str, Any]]:
    overrides = {
        'converter': {},
        'grammar': {},
        'parser': {},
        'comparator': {},
    }
    for name, value in vars(module).items():
        if name.startswith("converter_"):
            overrides['converter'][name[len("converter_"):]] = value
        elif name.startswith("grammar_"):
            overrides['grammar'][name[len("grammar_"):]] = value
        elif name.startswith("parser_"):
            overrides['parser'][name[len("parser_"):]] = value
        elif name.startswith("comparator_"):
            overrides['comparator'][name[len("comparator_"):]] = value
    return overrides


def process_grammar_override(func_name: str, value: Any, default_grammar: GrammarConfig) -> GrammarConfig:
    if isinstance(value, GrammarConfig):
        return value
    elif isinstance(value, str):
        return GrammarConfig(value)
    elif isinstance(value, (list, tuple)):
        if value and isinstance(value[0], str) and value[0].endswith('.fan'):
            return GrammarConfig(value[0], extra_constraints=list(value[1:]))
        return GrammarConfig(default_grammar.path, extra_constraints=list(value))
    else:
        raise ValueError(f"Unsupported grammar type for {func_name}: {type(value)}")


def process_parser_override(func_name: str, value: Any) -> InputParser:
    if isinstance(value, InputParser):
        return value
    elif isinstance(value, str):
        val = value.strip()
        if val.startswith('<') and val.endswith('>'):
            return InputParser.for_nonterminal(val)
        else:
            raise ValueError(f"String parser spec must be nonterminal like '<number>' for {func_name}: {value}")
    elif isinstance(value, list):
        if all(isinstance(v, str) for v in value):
            return InputParser.for_grammar_pattern(*value)
        else:
            raise ValueError(f"List parser spec must contain only strings for {func_name}: {value}")
    else:
        raise ValueError(f"Invalid parser spec for {func_name}: {value}")