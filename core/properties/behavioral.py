from core.function_under_test import CombinedFunctionUnderTest
from core.property_tester import PropertyTest, TestResult, TestStats


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
            return {
                "holds": False,
                "counterexamples": [f"Determinism test failed: No valid input sets provided for {f_name}\n"],
                "stats": {"total_count": 0, "success_count": 0},
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
        test_stats: TestStats = {
            'total_count': total_tests,
            'success_count': total_tests - len(counterexamples)
        }

        if not counterexamples:
            return {
                "holds": True,
                "counterexamples": [f"{f_name}(a) is deterministic for all tested runs\n"],
                "stats": test_stats,
            }
        else:
            return {
                "holds": False,
                "counterexamples": counterexamples,
                "stats": test_stats,
            }



class MonotonicallyIncreasingTest(PropertyTest):
    """Test if f is monotonically increasing (preserves order relationships)."""

    def __init__(self):
        super().__init__(
            name="MonotonicallyIncreasing",
            input_arity=2,
            function_arity=1,
            description="Tests if a ≤ b implies f(a) ≤ f(b)",
            category="Behavioral"
        )

    def test(self, function: CombinedFunctionUnderTest, inputs, early_stopping) -> TestResult:
        fut = function.funcs[0]
        f_name = fut.func.__name__
        input_arity = self.input_arity

        # Filter valid inputs based on arity
        valid_inputs = [input_set for input_set in inputs if len(input_set) >= input_arity]

        if not valid_inputs:
            return {
                "holds": False,
                "counterexamples": [f"Monotonicity test failed: No valid input sets provided for {f_name}\n"],
                "stats": {"total_count": 0, "success_count": 0},
            }

        # Test monotonicity for each valid input
        total_tests = 0
        counterexamples = []

        for input_set in valid_inputs:
            a_raw, b_raw = input_set[:2]  # Take first two elements
            total_tests += 1

            # Check monotonicity
            try:
                # Convert inputs
                a = fut.arg_converter(a_raw)
                b = fut.arg_converter(b_raw)

                # Determine order
                if a <= b:
                    small, large = a, b
                    raw_small, raw_large = a_raw, b_raw
                else:
                    small, large = b, a
                    raw_small, raw_large = b_raw, a_raw

                # Call function on ordered inputs
                r_small = function.call(0, small)
                r_large = function.call(0, large)

                if r_small > r_large:
                    # TODO maybe add max_counterexamples to limit output size here instead of post processing
                    counterexamples.append(
                        f"{raw_small} ≤ {raw_large}\n\t"
                        f"{f_name}({raw_small}) > {f_name}({raw_large})\n\t"
                        f"{r_small} > {r_large}\n"
                    )

                    if early_stopping:
                        break

            except (TypeError, ValueError, AttributeError):
                counterexamples.append(f"Monotonicity test skipped (cannot compare outputs/inputs of {f_name}\n)")

                if early_stopping:
                    break

        # Build result
        test_stats: TestStats = {
            'total_count': total_tests,
            'success_count': total_tests - len(counterexamples)
        }

        if not counterexamples:
            return {
                "holds": True,
                "counterexamples": [f"a ≤ b ⟹ {f_name}(a) ≤ {f_name}(b)\n"],
                "stats": test_stats,
            }
        else:
            return {
                "holds": False,
                "counterexamples": counterexamples,
                "stats": test_stats,
            }


class MonotonicallyDecreasingTest(PropertyTest):
    """Test if f is monotonically decreasing (reverses order)."""

    def __init__(self):
        super().__init__(
            name="MonotonicallyDecreasing",
            input_arity=2,
            function_arity=1,
            description="Tests if a ≤  b implies f(a) ≥ f(b)",
            category="Behavioral"
        )

    def test(self, function: CombinedFunctionUnderTest, inputs, early_stopping) -> TestResult:
        fut = function.funcs[0]
        f_name = fut.func.__name__
        input_arity = self.input_arity

        # Filter valid inputs based on arity
        valid_inputs = [input_set for input_set in inputs if len(input_set) >= input_arity]

        if not valid_inputs:
            return {
                "holds": False,
                "counterexamples": [f"Monotonicity test failed: No valid input sets provided for {f_name}\n"],
                "stats": {"total_count": 0, "success_count": 0},
            }

        # Test monotonicity for each valid input
        total_tests = 0
        counterexamples = []

        for input_set in valid_inputs:
            a_raw, b_raw = input_set[:2]  # Take first two elements
            total_tests += 1

            try:
                # Convert inputs
                a = fut.arg_converter(a_raw)
                b = fut.arg_converter(b_raw)

                # Determine order
                if a >= b:
                    large, small = a, b
                    raw_large, raw_small = a_raw, b_raw
                else:
                    large, small = b, a
                    raw_large, raw_small = b_raw, a_raw

                # Call function on ordered inputs
                r_small = function.call(0, small)
                r_large = function.call(0, large)

                if r_small < r_large:
                    counterexamples.append(
                        f"{raw_small} ≤ {raw_large}\n\t"
                        f"{f_name}({raw_small}) < {f_name}({raw_large})\n\t"
                        f"{r_small} < {r_large}\n"
                    )

                    if early_stopping:
                        break

            except (TypeError, ValueError, AttributeError):
                counterexamples.append(f"Monotonicity test skipped (cannot compare outputs/inputs of {f_name}\n)")

                if early_stopping:
                    break

        # Build result
        test_stats: TestStats = {
            'total_count': total_tests,
            'success_count': total_tests - len(counterexamples)
        }

        if not counterexamples:
            return {
                "holds": True,
                "counterexamples": [f"a ≤ b ⟹ {f_name}(a) ≥ {f_name}(b)\n"],
                "stats": test_stats,
            }
        else:
            return {
                "holds": False,
                "counterexamples": counterexamples,
                "stats": test_stats,
            }
