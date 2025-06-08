from itertools import chain

from core.function_under_test import CombinedFunctionUnderTest
from core.properties.property_test import PropertyTest, TestResult, TestStats


class TypePreservationTest(PropertyTest):
    """Test if function preserves input type"""

    def __init__(self):
        super().__init__(
            name="Type Preservation",
            input_arity=1,
            function_arity=1,
            description="Tests if function preserves the type of input",
            category="Structural"
        )

    def test(self, function: CombinedFunctionUnderTest, inputs, max_counterexamples) -> TestResult:
        fut = function.funcs[0]
        f_name = fut.func.__name__

        all_elements = frozenset(chain.from_iterable(inputs))

        if len(all_elements) < self.input_arity:
            return {
                "holds": False,
                "counterexamples": ["Not enough elements provided\n"],
                "stats": {"total_count": 0, "success_count": 0},
            }
        # Test type preservation for each valid input
        total_tests = 0
        counterexamples = []

        for a in all_elements:
            total_tests += 1
            a = fut.arg_converter(a)
            result = function.call(0, a)

            if type(result) != type(a):
                counterexamples.append(
                    f"Input type: {type(a).__name__}\n\t"
                    f"Output type: {type(result).__name__}\n"
                )

                if len(counterexamples) >= max_counterexamples:
                    break

        # Build result
        test_stats: TestStats = {
            'total_count': total_tests,
            'success_count': total_tests - len(counterexamples)
        }

        if not counterexamples:
            return {
                "holds": True,
                "counterexamples": [f"{f_name} preserves input type\n"],
                "stats": test_stats,
            }
        else:
            return {
                "holds": False,
                "counterexamples": counterexamples,
                "stats": test_stats,
            }

# TODO think about how to integrate try except into the logic
# class SizePreservationTest(PropertyTest):
#     """
#     Test if a unary function f preserves the size/length of its input where:
#         len(f(x)) == len(x)
#     """
#
#     def __init__(self) -> None:
#         super().__init__(
#             name="SizePreservation",
#             input_arity=1,
#             function_arity=1,
#             description="Checks whether function preserves size/length of input",
#             category="Structural"
#         )
#
#     def test(self, function: CombinedFunctionUnderTest, inputs, early_stopping) -> TestResult:
#         fut = function.funcs[0]
#         f_name = fut.func.__name__
#         input_arity = self.input_arity
#
#         # Extract all unique elements from valid input tuples
#         all_elements = set()
#         all_elements.update(element for input_set in inputs if len(input_set) >= input_arity for element in input_set)
#
#         if not all_elements:
#             return {
#                 "holds": False,
#                 "counterexamples": [f"SizePreservation test failed: No valid input sets provided for {f_name}\n"],
#                 "stats": {"total_count": 0, "success_count": 0},
#             }
#
#         # Setup conversion cache
#         conversion_cache = {}
#
#         def cached_convert(raw_val):
#             if raw_val not in conversion_cache:
#                 conversion_cache[raw_val] = fut.arg_converter(raw_val)
#             return conversion_cache[raw_val]
#
#         # Test each element for size preservation
#         total_tests = 0
#         size_preserved = []
#         counterexamples = []
#         skipped_items = []
#
#         for candidate in all_elements:
#             total_tests += 1
#             converted_input = cached_convert(candidate)
#             result = function.call(0, candidate)
#
#             try:
#                 input_len = len(converted_input)
#                 output_len = len(result)
#
#                 if input_len == output_len:
#                     size_preserved.append(f"{f_name}({candidate}): size preserved ({input_len})\n")
#                 else:
#                     counterexamples.append(
#                         f"{f_name}({candidate}): input size {input_len} → output size {output_len}\n"
#                     )
#                     if early_stopping:
#                         break
#
#             except TypeError:
#                 # Skip items where length is not applicable
#                 skipped_items.append(f"{f_name}({candidate}): size test skipped (length not applicable)\n")
#
#         # Build result
#         successful_tests = len(size_preserved)
#
#         # If we have skipped items but no failures, we still consider it a success
#         # since the property holds for all testable inputs
#         has_counterexamples = len(counterexamples) > 0
#
#         test_stats: TestStats = {
#             'total_count': total_tests,
#             'success_count': successful_tests + len(skipped_items) if not has_counterexamples else successful_tests
#         }
#
#         # Combine results for reporting
#         all_results = size_preserved + skipped_items
#
#         if not has_counterexamples and (size_preserved or skipped_items):
#             return {
#                 "holds": True,
#                 "counterexamples": all_results,
#                 "stats": test_stats,
#             }
#         else:
#             return {
#                 "holds": False,
#                 "counterexamples": counterexamples if counterexamples else [
#                     f"No valid inputs for size preservation test on {f_name}\n"],
#                 "stats": test_stats,
#             }