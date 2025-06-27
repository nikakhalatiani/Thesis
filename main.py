from typing import Any

from core.properties import minimal_registry
from input.input_parser import InputParser
from config.property_inference_config import PropertyInferenceConfig
from core.function_under_test import FunctionUnderTest, ComparisonStrategy
from core.property_inference_engine import PropertyInferenceEngine
from config.grammar_config import GrammarConfig

import inspect
import importlib.util


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


def process_grammar_override(func_name: str, value: Any, default_grammar) -> GrammarConfig:
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


def main(user_funcs_path: str = "input/user_input.py", class_name: str | None = None):
    registry = minimal_registry()

    default_parser = InputParser.for_numbers()
    config = (PropertyInferenceConfig(registry)
              .set_default_grammar("grammars/test.fan")
              .set_default_parser(default_parser)
              .set_comparison_strategy(ComparisonStrategy.FIRST_COMPATIBLE)
              .set_use_input_cache(True)
              .set_example_count(100)
              .set_max_counterexamples(3))

    module = load_user_module(user_funcs_path)

    if class_name:
        classes = [getattr(module, class_name)]
    else:
        classes = [
            obj for obj in vars(module).values()
            if inspect.isclass(obj) and obj.__module__ == module.__name__
        ]

    overrides = extract_overrides(module)

    for cls in classes:
        for func_name, func in inspect.getmembers(cls, inspect.isfunction):
            comp = overrides['comparator'].get(func_name) or getattr(func, "__comparator__", None)
            conv = overrides['converter'].get(func_name) or getattr(func, "__converter__", None)
            gram = overrides['grammar'].get(func_name) or getattr(func, "__grammar__", None)
            pars = overrides['parser'].get(func_name) or getattr(func, "__parser__", None)

            if gram and not isinstance(gram, GrammarConfig):
                gram = process_grammar_override(func_name, gram, config.default_grammar)

            if pars and not isinstance(pars, InputParser):
                pars = process_parser_override(func_name, pars)

            fut = FunctionUnderTest(func, arg_converter=conv, result_comparator=comp)
            config.add_function(fut, grammar=gram, parser=pars)

    engine: PropertyInferenceEngine = PropertyInferenceEngine(config)
    results = engine.run()

    for func_name, result in results.items():
        print(f"\n📊 Inferred Properties for {func_name}:")
        for prop, outcome in result["outcomes"].items():
            holds = outcome["holds"]
            tests_run = outcome["stats"]["total_count"]
            confidence = (outcome["stats"]["success_count"] / tests_run * 100) if tests_run > 0 else 0.0
            status = "🟢" if holds else "🔴"
            decision = (
                f"{status} {prop} "
                f"(Confidence: {confidence:.1f}%; Tests ran to infer: {tests_run})"
            )
            print(decision)
            messages = outcome["successes"] if holds else outcome["counterexamples"]
            for msg in messages:
                print(f"\t{msg}")

if __name__ == "__main__":
    main()
