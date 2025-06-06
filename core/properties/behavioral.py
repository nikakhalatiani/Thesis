from core.function_under_test import CombinedFunctionUnderTest
from core.properties.property_test import PropertyTest, TestResult


class DeterminismTest(PropertyTest):
    """Test if a function is deterministic (same input gives same output)"""

    def __init__(self):
        super().__init__(
            name="Determinism",
            input_arity=1,
            function_arity=1,
            description="Tests if function gives same output for same input",
            category="Behavioral"
        )

    def test(self, function: CombinedFunctionUnderTest, inputs, early_stopping) -> TestResult:
        f_name = function.funcs[0].func.__name__
        input_arity = self.input_arity

        # Filter valid inputs based on arity
        valid_inputs = [input_set for input_set in inputs if len(input_set) >= input_arity]

        if not valid_inputs:
            return False, [f"Determinism test failed: No valid input sets provided for {f_name}\n"], {
                'total_count': 0, 'success_count': 0
            }

        # Test determinism for each valid input
        total_tests = 0
        counterexamples = []

        for input_set in valid_inputs:
            a = input_set[0]  # Take first element
            total_tests += 1

            # Call function multiple times with the same input
            results = [function.call(0, a) for _ in range(100)]

            # Check if all results are the same
            first_result = results[0]
            first_different_result = None
            for idx, r in enumerate(results[1:], start=1):
                if not function.compare_results(first_result, r):
                    first_different_result = (idx, r)
                    break

            if first_different_result is not None:
                # If results differ, record the counterexample
                idx_diff, diff_val = first_different_result
                counterexamples.append(
                    f"{f_name}({a}) on run #1: {first_result}\n\t"
                    f"{f_name}({a}) on run #{idx_diff + 1}: {diff_val}\n"
                )

                if early_stopping:
                    break

        # Build result
        test_stats = {
            'total_count': total_tests,
            'success_count': total_tests - len(counterexamples)
        }

        if not counterexamples:
            return True, [f"{f_name}(a) is deterministic for all tested runs\n"], test_stats
        else:
            return False, counterexamples, test_stats
