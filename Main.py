from fandango import Fandango, FandangoParseError

from PropertyTester import PropertyTester


def generate_examples(spec_file_path: str, num_examples: int):
    """Load spec and generate examples using fuzz()."""
    with open(spec_file_path) as spec_file:
        fan = Fandango(spec_file)


    print("📦 Fuzzing examples:")
    examples = fan.fuzz(desired_solutions=num_examples, population_size=num_examples)
    for example in examples:
        print(str(example))
    return fan, examples

def parse_example(fan, fuzzed_string: str):
    """Parse a fuzzed string and return a tuple of (a, b, b_rev, a_rev)."""
    try:
        for tree in fan.parse(fuzzed_string):
            pair = tree.children[0]  # <start> → <expr> → <term> + <term>
            a = str(pair.children[0])
            b = str(pair.children[2])
            return a, b
    except FandangoParseError as e:
        print(f"❌ Parsing failed at position {e.position} in '{fuzzed_string}'")
    return None

def main():
    spec_path = 'add_pair.fan'
    number_of_examples = 200
    fan, examples = generate_examples(spec_path, number_of_examples)

    # Function under test FUT1
    def add(x, y):
        return x + y

    # Function under test FUT2
    def add_pair(x, y):
        return int(x) + int(y)

    property_tester = PropertyTester(add_pair)

    # Collect test inputs
    input_sets = []
    for i, tree in enumerate(examples, start=1):
        fuzzed_str = str(tree)
        inputs = parse_example(fan, fuzzed_str)
        if inputs:
            a, b = inputs
            input_sets.append((a, b))

    # Infer properties
    properties, counter_examples = property_tester.infer_properties(input_sets)

    # Report results
    print("\n📊 Inferred Properties:")
    for prop, result in properties.items():
        status = "✅" if result else "❌"
        print(f"{status} {prop}")
        if not result and prop in counter_examples:
            print(f"   Counter-example: {counter_examples[prop]}")


if __name__ == "__main__":
    main()