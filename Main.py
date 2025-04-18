from fandango import Fandango
from PropertyTester import PropertyTester
from InputParser import InputParser
from PropertyInferenceConfig import PropertyInferenceConfig

def generate_examples(spec_file_path: str, num_examples: int):
    """Load spec and generate examples using fuzz()."""
    with open(spec_file_path) as spec_file:
        fan = Fandango(spec_file)
    print("📦 Fuzzing examples:")
    examples = fan.fuzz(desired_solutions=num_examples, population_size=num_examples)
    for example in examples:
        print(str(example))
    return fan, examples


def run_property_inference(config):
    """Run property inference based on configuration."""
    results = {}

    for i, func in enumerate(config.functions_under_test):
        # Set up appropriate grammar and parser
        grammar_spec = config.grammar_specs[min(i, len(config.grammar_specs) - 1)]
        parser = config.input_parsers[min(i, len(config.input_parsers) - 1)]

        # Generate examples
        fan, examples = generate_examples(grammar_spec, config.example_count)

        # Parse examples into input sets
        input_sets = []
        for tree in examples:
            fuzzed_str = str(tree)
            inputs = parser.parse(fan, fuzzed_str)
            if inputs:
                input_sets.append(inputs)

        # Test properties
        tester = PropertyTester()
        properties, counter_examples, confidence = tester.infer_properties(
            func, config.properties_to_test, input_sets)

        # Store results
        func_name = func.func.__name__
        results[func_name] = {
            "properties": properties,
            "counter_examples": counter_examples,
            "confidence": confidence
        }

    return results


def main():
    # Define extraction strategies
    def extract_two_numbers(tree):
        pair = tree.children[0]  # <start> → <expr>
        a = str(pair.children[0])  # <expr> → <term> " + " <term>
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

    def subtract2(x, y):
        return x - y

    def abs_compare(x, y):
        return abs(x) == abs(y)

        # Create configuration

    config = PropertyInferenceConfig()
    config.add_function(multiply, arg_converter=int)
    config.add_function(add)
    config.add_function(subtract, arg_converter=int)
    config.add_function(subtract2, arg_converter=int, result_comparator=abs_compare)

    config.add_property("commutativity")
    config.set_grammar("Grammars/pair.fan")
    config.set_parser(binary_parser)
    config.example_count = 5

    # Run inference
    results = run_property_inference(config)

    # Report results
    for func_name, result in results.items():
        print(f"\n📊 Inferred Properties for {func_name}:")
        for prop, holds in result["properties"].items():
            # TODO: rethink confidence calculation for negative results
            confidence = result["confidence"].get(prop, 0) * 100
            status = "✅" if holds else "❌"
            decision = f"{status} {prop} (Confidence: {confidence:.1f}%)" if holds else f"{status} {prop} (Confidence: {100-confidence:.1f}%)"
            print(decision)
            if not holds and prop in result["counter_examples"]:
                print(f"   Counter-example: {result['counter_examples'][prop]}")



if __name__ == "__main__":
    main()