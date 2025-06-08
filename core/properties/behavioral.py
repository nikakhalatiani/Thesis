from core.function_under_test import CombinedFunctionUnderTest
from core.properties.property_test import PropertyTest, TestResult, TestStats

from itertools import chain, combinations


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

    def test(self, function: CombinedFunctionUnderTest, inputs, max_counterexamples) -> TestResult:
        f_name = function.funcs[0].func.__name__

        all_elements = frozenset(chain.from_iterable(inputs))

        if len(all_elements) < self.input_arity:
            return {
                "holds": False,
                "counterexamples": ["Not enough elements provided\n"],
                "stats": {"total_count": 0, "success_count": 0},
            }

        # Test determinism for each valid input
        total_tests = 0
        counterexamples = []

        for a in all_elements:
            total_tests += 1

            # Call function multiple times with the same input
            results = [function.call(0, a) for _ in range(max_counterexamples)]

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

        # Test monotonicity for each valid input
        total_tests = 0
        counterexamples = []

        for a_raw, b_raw in combinations(all_elements, 2):
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
                    counterexamples.append(
                        f"{raw_small} ≤ {raw_large}\n\t"
                        f"{f_name}({raw_small}) > {f_name}({raw_large})\n\t"
                        f"{r_small} > {r_large}\n"
                    )

                    if len(counterexamples) >= max_counterexamples:
                        break

            except (TypeError, ValueError, AttributeError):
                counterexamples.append("Test skipped (cannot compare outputs/inputs)\n")

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
            description="Tests if a ≤ b implies f(a) ≥ f(b)",
            category="Behavioral"
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

        # Test monotonicity for each valid input
        total_tests = 0
        counterexamples = []

        for a_raw, b_raw in combinations(all_elements, 2):
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

                    if len(counterexamples) >= max_counterexamples:
                        break

            except (TypeError, ValueError, AttributeError):
                counterexamples.append("Test skipped (cannot compare outputs/inputs)\n")


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
