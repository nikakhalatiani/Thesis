from core.property_tester import PropertyTester
from input.input_parser import InputParser
from config.property_inference_config import PropertyInferenceConfig
from config.property_registry import PropertyRegistry
from core.function_under_test import FunctionUnderTest
from core.property_inference_engine import PropertyInferenceEngine
from input.functions import Functions

import inspect

def main():
    # 1) build property registry
    registry = PropertyRegistry() \
        .register("Commutativity", PropertyTester.commutativity_test, 2)
    registry.register("Associativity", PropertyTester.associativity_test, 3)

    # 2) build config
    binary_parser = InputParser(InputParser.extract_elements_and_clean)
    config = (PropertyInferenceConfig(registry, example_count=100)
              .set_default_grammar("grammars/digits_list.fan")
              .set_default_parser(binary_parser)
              .set_early_stopping(False))

    # TODO think about what to do instead of defining comparator here and creating dictionaries for overrides
    def abs_compare(x, y):
        return abs(x) == abs(y)
    grammar_overrides = {"subtract": "grammars/digits_list.fan", "divide": "grammars/digits_list.fan"}
    parser_overrides = {"subtract": binary_parser}
    comparator_overrides = {"subtract": abs_compare}
    # TODO think about what to do when strings are passed and Error is raised without line below
    converter_overrides = {"multiply": int, "subtract": int, "divide": int}


    for name, func in inspect.getmembers(Functions, predicate=inspect.isfunction):
        converter = converter_overrides.get(name)
        comparator = comparator_overrides.get(name)
        fut = FunctionUnderTest(func, arg_converter=converter, result_comparator=comparator)
        grammar = grammar_overrides.get(name)
        parser = parser_overrides.get(name)
        config.add_function(fut, grammar, parser)

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
            confidence: int = result["confidence"].get(prop, 0) * 100
            status = "✅" if holds else "❌"
            decision = (
                f"{status} {prop} (Confidence: {confidence:.1f}%)"
                if holds
                else f"{status} {prop} (Confidence: {100 - confidence:.1f}%)"
            )
            print(decision)
            if not holds and prop in result["counter_examples"]:
                print(f"🚫 Counter-example: {result['counter_examples'][prop]}")


if __name__ == "__main__":
    main()
