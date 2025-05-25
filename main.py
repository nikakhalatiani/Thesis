from core.properties import create_standard_registry, create_minimal_registry
from input.input_parser import InputParser
from config.property_inference_config import PropertyInferenceConfig
from core.function_under_test import FunctionUnderTest
from core.property_inference_engine import PropertyInferenceEngine
from config.grammar_config import GrammarConfig

import inspect
import importlib.machinery
import importlib.util


def load_user_module(path: str, module_name: str):
    loader = importlib.machinery.SourceFileLoader(module_name, path)
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def main(user_funcs_path: str = "input/calculator.py"):
    # 1) build property registry
    registry = create_minimal_registry()
    # registry = create_standard_registry()

    # 2) build base config
    default_parser = InputParser(InputParser.basic_recursion_with_built_in_detector)
    # TODO ask if custom distributions for grammar is available
    config = (PropertyInferenceConfig(registry, example_count=500)
              .set_default_grammar("grammars/digits_list.fan")
              .set_default_parser(default_parser)
              .set_early_stopping(False)
              .set_max_counterexamples(3)
              )

    # 3) dynamically load the user’s calculator.py
    module = load_user_module(user_funcs_path, "user_functions")
    functions = getattr(module, "Calculator")

    # 4) pick up any module-level comparator_*, converter_*, grammar_*, parser_* overrides
    comparator_overrides = {
        name[len("comparator_"):]: fn
        for name, fn in vars(module).items()
        if name.startswith("comparator_") and inspect.isfunction(fn)
    }

    converter_overrides = {
        name[len("converter_"):]: fn
        for name, fn in vars(module).items()
        if name.startswith("converter_") and inspect.isfunction(fn)
    }

    grammar_overrides = {
        name[len("grammar_"):]: spec
        if isinstance(spec, GrammarConfig) else
        (GrammarConfig(spec) if isinstance(spec, str)
         else GrammarConfig(config.default_grammar.path, extra_constraints=spec))
        for name, spec in vars(module).items()
        if name.startswith("grammar_")
    }

    # grammar_overrides: dict[str, GrammarConfig] = {}
    # for name, spec in vars(module).items():
    #     if not name.startswith("grammar_"):
    #         continue
    #     func_name = name[len("grammar_"):]
    #     if isinstance(spec, GrammarConfig):
    #         grammar_overrides[func_name] = spec
    #     elif isinstance(spec, str):
    #         grammar_overrides[func_name] = GrammarConfig(spec)
    #     elif isinstance(spec, list):
    #         grammar_overrides[func_name] = GrammarConfig(config.default_grammar.path, extra_constraints=spec)

    parser_overrides = {
        name[len("parser_"):]: obj
        for name, obj in vars(module).items()
        if name.startswith("parser_")
    }

    # 5) register every static method under Functions, wiring overrides by name
    for func_name, func in inspect.getmembers(functions, inspect.isfunction):
        comp = comparator_overrides.get(func_name) or getattr(func, "__comparator__", None)
        conv = converter_overrides.get(func_name) or getattr(func, "__converter__", None)
        gram = grammar_overrides.get(func_name) or getattr(func, "__grammar__", None)
        pars = parser_overrides.get(func_name) or getattr(func, "__parser__", None)

        fut = FunctionUnderTest(func, arg_converter=conv, result_comparator=comp)
        config.add_function(fut, grammar=gram, parser=pars)

    # specify the properties to test if none are provided all properties are tested
    # config.add_property("Commutativity")
    # config.add_property("Associativity")

    # 3) run
    engine: PropertyInferenceEngine = PropertyInferenceEngine(config)
    results = engine.run()

    # 4) pretty‑print
    for func_name, result in results.items():
        print(f"\n📊 Inferred Properties for {func_name}:")
        prop: str
        holds: bool
        for prop, holds in result["properties"].items():
            confidence = result["confidence"].get(prop, 0) * 100
            tests_run = result["total_tests"].get(prop, 0)
            status = "🟢" if holds else "🔴"
            decision = (
                f"{status} {prop} (Confidence: {confidence:.1f}%; Tests ran to infer: {tests_run})"
                # if holds
                # else f"{status} {prop} (Confidence: {100 - confidence:.1f}%; Tests run to infer: {tests_run})"
            )
            print(decision)
            counterexamples = result["counterexamples"][prop]
            for ex in counterexamples:
                if isinstance(ex, dict):
                    for call_repr, outcome in ex.items():
                        if isinstance(outcome, str):
                            print(f"\t {call_repr}: {outcome}")
                        else:
                            print(f"\t {call_repr}: {repr(outcome)}")
                else:
                    print(f"\t {ex}")


if __name__ == "__main__":
    main()
