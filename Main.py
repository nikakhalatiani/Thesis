from fandango import Fandango
from fandango.language.tree import DerivationTree

from PropertyTester import PropertyTester
from InputParser import InputParser
from PropertyInferenceConfig import PropertyInferenceConfig
from PropertyRegistry import PropertyRegistry
from FunctionUnderTest import FunctionUnderTest


def commutativity_test(function: FunctionUnderTest, inputs: tuple) -> tuple[bool, dict[str, str] | None]:
    # assert isinstance(inputs, tuple), "Inputs should be a tuple"
    a, b = inputs
    result1 = function.call(a, b)
    result2 = function.call(b, a)
    success: bool = function.compare_results(result1, result2)

    if success:
        return True, None
    else:
        return False, {
            f"{function.func.__name__}({a},{b})": result1 if isinstance(result1, str) else repr(result1),
            f"{function.func.__name__}({b},{a})": result2 if isinstance(result2, str) else repr(result2),
        }


# def associativity_test(function: FunctionUnderTest, inputs: tuple) -> tuple[bool, dict[str, str] | None]:
#     a, b, c = inputs
#     result1 = function.call(a, function.call(b, c))
#     result2 = function.call(function.call(a, b), c)
#     success: bool = function.compare_results(result1, result2)
#
#     if success:
#         return True, None
#     else:
#         return False, {
#             f"{function.func.__name__}({a},{function.func.__name__}({b},{c}))": result1 \
#                 if isinstance(result1, str) else repr(result1),
#             f"{function.func.__name__}({function.func.__name__}({a},{b}),{c})": result2 \
#                 if isinstance(result2, str) else repr(result2)
#         }


# Add properties to a registry
default_registry = PropertyRegistry()
default_registry.register("Commutativity", commutativity_test, 2)


# default_registry.register("Associativity", associativity_test, 3)


def generate_examples(spec_file_path: str, num_examples: int) -> tuple[Fandango, list[DerivationTree]]:
    """Load Fandango grammar file and generate examples using fuzz()."""
    with open(spec_file_path) as spec_file:
        fan: Fandango = Fandango(spec_file)
    # print("📦 Fuzzing examples:")
    examples: list[DerivationTree] = fan.fuzz(desired_solutions=num_examples)
    # for example in examples:
    #     print(str(example))
    return fan, examples


def run_property_inference(config: PropertyInferenceConfig) -> dict[str, dict[str, dict]]:
    """Run property inference based on configuration."""
    results: dict[str, dict[str, dict]] = {}
    for i, fut in enumerate(config.functions_under_test):
        # Dynamically select grammar and parser based on the function
        grammar_spec: str = config.function_to_grammar.get(fut.func.__name__, config.default_grammar)
        parser: InputParser = config.function_to_parser.get(fut.func.__name__, config.default_parser)

        # Generate examples
        fan: Fandango
        examples: list[DerivationTree]
        fan, examples = generate_examples(grammar_spec, config.example_count)

        # Parse examples into input sets
        input_sets: list = []
        for tree in examples:
            # fuzzed_str: str = str(tree)
            # inputs = parser.parse(fan, fuzzed_str)
            inputs = parser.parse(fan, tree)
            if inputs:
                input_sets.append(inputs)

        # Test properties
        tester: PropertyTester = PropertyTester()
        properties, counter_examples, confidence = tester.infer_properties(
            fut, config.properties_to_test, input_sets,
            early_stopping=config.early_stopping)  # Pass early stopping config

        # Store results
        func_key: str = f"{fut.func.__name__} ({i + 1}/{len(config.functions_under_test)})"
        # func_key: str = f"{fut.func.__name__}"
        # func_key: str = (f"{'function ' + fut.func.__name__}" " with "
        #                  f"{fut.arg_converter.__name__ if fut.arg_converter.__name__ != '<lambda>' else 'default'}" " converter and "
        #                  f"{fut.result_comparator.__name__ if fut.result_comparator.__name__ != '<lambda>' else 'default'}" " comparator")
        results[func_key] = {
            "properties": properties,
            "counter_examples": counter_examples,
            "confidence": confidence
        }

    return results


def main():
    # Define extraction strategies
    def extract_two_numbers(tree: DerivationTree) -> tuple[str, str]:
        pair = tree.children[0]  # <start> → <expr>
        a = str(pair.children[0])  # <expr> → <term> ", " <term>
        b = str(pair.children[2])
        return a, b

    # Set up parsers
    binary_parser = InputParser(extract_two_numbers)

    def add(x, y):
        return x + y

    def multiply(x, y):
        return x * y

    def subtract(x, y):
        return x - y

    def abs_compare(x, y):
        return abs(x) == abs(y)

        # Create configuration

    # Create a Fandango instance
    fut_add_bad = FunctionUnderTest(add)
    fut_add_good = FunctionUnderTest(add, arg_converter=int)
    fut_multiply_good = FunctionUnderTest(multiply, arg_converter=int)
    # TODO think about what to do when strings are passed and Error is raised
    # fut_multiply_bad = FunctionUnderTest(multiply)
    fut_subtract_bad = FunctionUnderTest(subtract, arg_converter=int)
    fut_subtract_pass_bad = FunctionUnderTest(subtract, arg_converter=int, result_comparator=abs_compare)

    config = PropertyInferenceConfig(default_registry)
    config.add_function(fut_multiply_good)
    # config.add_function(fut_multiply_bad)
    config.add_function(fut_add_bad)
    config.add_function(fut_add_good)
    config.add_function(fut_subtract_bad, grammar="Grammars/pair2.fan", parser=binary_parser)
    config.add_function(fut_subtract_pass_bad, grammar="Grammars/pair2.fan",
                        parser=binary_parser)

    config.add_property("Commutativity")
    # config.add_property("Associativity")
    config.set_default_grammar("Grammars/pair.fan")
    config.set_default_parser(binary_parser)
    config.example_count = 100
    # Configure early stopping (set to True to stop testing a property after finding a counter-example)
    config.set_early_stopping(False)  # Change to True to enable early stopping

    # Run inference
    results = run_property_inference(config)

    # Report results
    for func_name, result in results.items():
        print(f"\n📊 Inferred Properties for {func_name}:")
        prop: str
        holds: bool
        for prop, holds in result["properties"].items():
            # TODO: rethink confidence calculation for negative results
            confidence:int = result["confidence"].get(prop, 0) * 100
            status = "✅" if holds else "❌"
            decision = f"{status} {prop} (Confidence: {confidence:.1f}%)" if holds else \
                f"{status} {prop} (Confidence: {100 - confidence:.1f}%)"
            print(decision)
            if not holds and prop in result["counter_examples"]:
                print(f"   Counter-example: {result['counter_examples'][prop]}")


if __name__ == "__main__":
    main()
