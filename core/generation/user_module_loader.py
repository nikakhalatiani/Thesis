import inspect
import importlib.util
from typing import Any

from config.grammar_config import GrammarConfig
from input.input_parser import InputParser


def load_user_module(path: str):
    """Load a Python module from a file path."""
    try:
        spec = importlib.util.spec_from_file_location("user_defined_functions", path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load module from {path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception as e:
        raise ImportError(f"Failed to load module from {path}: {e}") from e


def extract_overrides(module) -> dict[str, dict[str, Any]]:
    """Extract override configurations from a user module.

    Args:
        module: The loaded user module

    Returns:
        Dictionary containing override configurations for converter, grammar, parser, and comparator
    """
    overrides = {
        'converter': {},
        'grammar': {},
        'parser': {},
        'comparator': {}
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
    """Process grammar override value into a GrammarConfig object.

    Args:
        func_name: Name of the function this grammar is for
        value: The override value to process
        default_grammar: Default grammar configuration to fall back to

    Returns:
        Processed GrammarConfig object

    Raises:
        ValueError: If the grammar specification is invalid
    """
    if isinstance(value, GrammarConfig):
        return value
    elif isinstance(value, str):
        return GrammarConfig(value)
    elif isinstance(value, (list, tuple)):
        try:
            if value and isinstance(value[0], str) and value[0].endswith(".fan"):
                return GrammarConfig(value[0], extra_constraints=value[1:])
            else:
                return GrammarConfig(default_grammar.path, extra_constraints=value)
        except Exception as e:
            raise ValueError(f"Invalid grammar spec for {func_name}: {value}") from e
    else:
        raise ValueError(f"Unsupported grammar type for {func_name}: {type(value)}")


def process_parser_override(func_name: str, value: Any) -> InputParser:
    """Process parser override value into an InputParser object.

    Args:
        func_name: Name of the function this parser is for
        value: The override value to process

    Returns:
        Processed InputParser object

    Raises:
        ValueError: If the parser specification is invalid
    """
    if isinstance(value, InputParser):
        return value
    elif isinstance(value, str):
        val = value.strip()
        if val.startswith("<") and val.endswith(">"):
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


def extract_functions_from_classes(module, class_name: str = None) -> list[tuple]:
    """Extract functions from classes in the module.

    Args:
        module: The loaded user module
        class_name: Optional specific class name to extract from

    Returns:
        List of tuples containing (class, function_name, function_object)
    """
    if class_name:
        classes = [getattr(module, class_name)]
    else:
        classes = [
            obj for obj in vars(module).values()
            if inspect.isclass(obj) and obj.__module__ == module.__name__
        ]

    functions = []
    for cls in classes:
        for func_name, func in inspect.getmembers(cls, inspect.isfunction):
            functions.append((cls, func_name, func))

    return functions