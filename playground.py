# from fandango import Fandango, FandangoParseError
#
#
# def generate_examples(spec_file_path: str, num_examples: int):
#     """Load spec and generate examples using fuzz()."""
#     with open(spec_file_path) as spec_file:
#         fan = Fandango(spec_file)
#
#     print("📦 Fuzzing examples:")
#     examples = fan.fuzz(desired_solutions=num_examples, population_size=num_examples)
#     for example in examples:
#         print(str(example))
#     return fan, examples
#
#
# def parse_example(fan, fuzzed_string: str):
#     """Parse a fuzzed string and return a tuple of (a, b, b_rev, a_rev)."""
#     try:
#         for tree in fan.parse(fuzzed_string):
#             pair = tree.children[0]  # <start> → <pair>
#             a = str(pair.children[0])
#             b = str(pair.children[2])
#             b_rev = str(pair.children[4])
#             a_rev = str(pair.children[6])
#             return a, b, b_rev, a_rev
#     except FandangoParseError as e:
#         print(f"❌ Parsing failed at position {e.position} in '{fuzzed_string}'")
#     return None
#
#
# def run_test(a: str, b: str, b_rev: str, a_rev: str):
#     """Run the function under test and compare results."""
#     def add(x, y):
#         return int(x) + int(y)
#
#     result1 = add(a, b)
#     result2 = add(b_rev, a_rev)
#
#     print(f"🧪 Testing: add({a}, {b}) = {result1}, add({b_rev}, {a_rev}) = {result2}")
#     if result1 == result2:
#         print("✅ Test passed")
#         return True
#     else:
#         print("❌ Test failed")
#         return False
#
#
# def main():
#     spec_path = 'rev.fan'
#     number_of_examples = 5
#
#     fan, examples = generate_examples(spec_path, number_of_examples)
#
#     for i, tree in enumerate(examples, start=1):
#         fuzzed_str = str(tree)
#         print(f"\n🔍 Parsing example {i}: '{fuzzed_str}'")
#
#         inputs = parse_example(fan, fuzzed_str)
#
#         if inputs:
#             a, b, b_rev, a_rev = inputs
#             run_test(a, b, b_rev, a_rev)
#         else:
#             print("⚠️ Could not extract inputs from example.")
#
#
# if __name__ == "__main__":
#     main()
