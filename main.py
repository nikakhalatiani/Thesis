from collections.abc import Callable
from typing import Any

from core.properties import create_standard_registry, create_minimal_registry
from input.input_parser import InputParser
from config.property_inference_config import PropertyInferenceConfig
from core.function_under_test import FunctionUnderTest, ComparisonStrategy
from core.property_inference_engine import PropertyInferenceEngine
from config.grammar_config import GrammarConfig

import inspect


def load_user_module(path: str):
    import importlib.util
    spec = importlib.util.spec_from_file_location("user_defined_functions", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main(user_funcs_path: str = "input/user_input.py", class_name: str | None = None):
    # 1) build property registry
    registry = create_minimal_registry()
    # registry = create_standard_registry()

    # 2) build base config
    default_parser = InputParser.for_number_values()
    config = (PropertyInferenceConfig(registry, example_count = 10)
              .set_default_grammar("grammars/test.fan")
              .set_default_parser(default_parser)
              .set_max_counterexamples(3)
              .set_comparison_strategy(ComparisonStrategy.FIRST_COMPATIBLE)  # Set your preferred strategy here
              )

    # 3) dynamically load the user’s module
    module = load_user_module(user_funcs_path)

    # Determine which classes to inspect
    if class_name:
        classes = [getattr(module, class_name)]
    else:
        classes = [
            obj for obj in vars(module).values()
            if inspect.isclass(obj) and obj.__module__ == module.__name__
        ]

    # 4) pick up any module-level comparator_*, converter_*, grammar_*, parser_* overrides
    converter_overrides: dict[str, Any] = {}
    grammar_overrides: dict[str, GrammarConfig] = {}
    parser_overrides: dict[str, Any] = {}
    comparator_overrides: dict[str, Callable] = {}

    for name, value in vars(module).items():
        if name.startswith("converter_"):
            func_name = name[len("converter_"):]
            converter_overrides[func_name] = value

        elif name.startswith("grammar_"):
            func_name = name[len("grammar_"):]
            if isinstance(value, GrammarConfig):
                grammar_overrides[func_name] = value
            elif isinstance(value, str):
                grammar_overrides[func_name] = GrammarConfig(value)
            else:
                try:
                    path_candidate = value[0]
                    if isinstance(path_candidate, str) and path_candidate.endswith(".fan"):
                        path = path_candidate
                        constraints = value[1:]
                    else:
                        path = config.default_grammar.path
                        constraints = value
                    grammar_overrides[func_name] = GrammarConfig(path, extra_constraints=constraints)
                except Exception as e:
                    raise ValueError(f"Invalid grammar spec format for {name}: {value}") from e

        elif name.startswith("parser_"):
            func_name = name[len("parser_"):]
            parser_overrides[func_name] = value

        elif name.startswith("comparator_"):
            func_name = name[len("comparator_"):]
            comparator_overrides[func_name] = value

    # 5) register every static method under discovered classes, wiring overrides by name
    for cls in classes:
        for func_name, func in inspect.getmembers(cls, inspect.isfunction):
            comp = comparator_overrides.get(func_name) or getattr(func, "__comparator__", None)
            conv = converter_overrides.get(func_name) or getattr(func, "__converter__", None)
            gram = grammar_overrides.get(func_name) or getattr(func, "__grammar__", None)
            pars = parser_overrides.get(func_name) or getattr(func, "__parser__", None)

            fut = FunctionUnderTest(func, arg_converter=conv, result_comparator=comp)
            config.add_function(fut, grammar=gram, parser=pars)
        # config.add_combination(CombinedFunctionUnderTest((fut, fut)), grammar=GrammarConfig("grammars/digits_list.fan", ["int(<term>) == 0"]), parser=pars)

    # specify the properties to test if none are provided all properties are tested
    # config.add_property_by_name("Commutativity")
    # config.add_property_by_name("Associativity")
    # config.add_property_by_name("Distributivity")
    # config.add_property_by_name("Idempotence")


    # 3) run
    # import time
    # start_time = time.perf_counter()
    engine: PropertyInferenceEngine = PropertyInferenceEngine(config)
    results = engine.run()
    # end_time = time.perf_counter()
    # print(f"Execution time: {end_time - start_time:.4f} seconds")

    # 4) pretty‑print
    for func_name, result in results.items():
        print(f"\n📊 Inferred Properties for {func_name}:")
        prop: str
        holds: bool
        for prop, outcome in result["outcomes"].items():
            holds = outcome["holds"]
            tests_run = outcome["stats"]["total_count"]
            confidence = (outcome["stats"]["success_count"] / tests_run * 100) if tests_run > 0 else 0.0
            status = "🟢" if holds else "🔴"
            decision = (
                f"{status} {prop} "
                f"(Confidence: {confidence:.1f}%; Tests ran to infer: {tests_run})"
                # if holds
                # else f"{status} {prop} (Confidence: {100 - confidence:.1f}%; Tests run to infer: {tests_run})"
            )
            print(decision)
            for ex in outcome["counterexamples"]:
                print(f"\t{ex}")


if __name__ == "__main__":
    main()
