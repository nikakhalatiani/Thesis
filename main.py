from core.evaluation.library import minimal_registry
from util.input_parser import InputParser
from core.config import PropertyInferenceConfig
from util.function_under_test import FunctionUnderTest, ComparisonStrategy
from core.property_inference_engine import PropertyInferenceEngine
from core.generation import (
    load_user_module,
    extract_overrides,
    process_grammar_override,
    process_parser_override,
    extract_functions_from_classes
)


def print_constraints_evolution(constraints_history):
    """Print how constraints evolved during testing."""
    if not constraints_history:
        print("🔄 No constraint evolution (property held on first attempt)")
        return

    print(f"🔄 Constraint evolution ({len(constraints_history)} iterations):")
    for i, constraints in enumerate(constraints_history, 1):
        if constraints:
            print(f"\tIteration {i}: {', '.join(constraints)}")
        else:
            print(f"\tIteration {i}: No new constraints inferred")


def main(user_funcs_path: str = "input/user_input.py", class_name: str | None = None):
    registry = minimal_registry()

    default_parser = InputParser.for_numbers()
    config = (PropertyInferenceConfig(registry)
              .set_default_grammar("grammars/ints.fan")
              .set_default_parser(default_parser)
              .set_comparison_strategy(ComparisonStrategy.FIRST_COMPATIBLE)
              .set_use_input_cache(True)
              .set_example_count(100)
              .set_max_counterexamples(3)
              .set_max_feedback_attempts(2)
              .set_feedback_enabled(False))

    module = load_user_module(user_funcs_path)
    overrides = extract_overrides(module)
    functions = extract_functions_from_classes(module, class_name)

    for cls, func_name, func in functions:
        comp = overrides['comparator'].get(func_name) or getattr(func, "__comparator__", None)
        conv = overrides['converter'].get(func_name) or getattr(func, "__converter__", None)
        gram = overrides['grammar'].get(func_name) or getattr(func, "__grammar__", None)
        pars = overrides['parser'].get(func_name) or getattr(func, "__parser__", None)

        if gram and not isinstance(gram, type(config.default_grammar)):
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
            constraints_history = result["constraints_history"][prop]
            decision = (
                f"{status} {prop} "
                f"(Confidence: {confidence:.1f}%; Tests ran to infer: {tests_run})"
            )
            print(decision)
            if constraints_history:
                print_constraints_evolution(constraints_history)
            messages = outcome["successes"] if holds else outcome["counterexamples"]
            for msg in messages:
                print(f"\t{msg}")


if __name__ == "__main__":
    main()
