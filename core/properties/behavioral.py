from core.function_under_test import CombinedFunctionUnderTest
from core.properties.property_test import PropertyTest, TestResult, TestStats

from itertools import chain


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
                "counterexamples": [f"{f_name}(a) is deterministic for all tested inputs\n"],
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

        conversion_cache = {}

        def cached_convert(raw_val):
            if raw_val not in conversion_cache:
                conversion_cache[raw_val] = fut.arg_converter(raw_val)
            return conversion_cache[raw_val]

        try:
            # Convert and sort raw inputs
            converted_elements = [(cached_convert(raw), raw) for raw in all_elements]
            converted_elements.sort(key=lambda x: x[0])
        except (TypeError, ValueError) as e:
            return {
                "holds": False,
                "counterexamples": [f"Cannot sort elements for monotonicity test: {str(e)}\n"],
                "stats": {"total_count": 0, "success_count": 0},
            }

        total_tests = 0
        counterexamples = []

        for i in range(len(converted_elements) - 1):
            total_tests += 1
            small_val, small_raw = converted_elements[i]
            large_val, large_raw = converted_elements[i + 1]
            small_result = function.call(0, small_val)
            large_result = function.call(0, large_val)

            try:
                if small_result > large_result:
                    counterexamples.append(
                        f"{small_raw} ≤ {small_raw}\n\t"
                        f"{f_name}({small_raw}) = {small_result} > {f_name}({small_raw}) = {large_result}\n"
                    )


            except (TypeError, ValueError, AttributeError):
                counterexamples.append("Test skipped (cannot compare outputs)\n")

            if len(counterexamples) >= max_counterexamples:
                break

        test_stats: TestStats = {
            "total_count": total_tests,
            "success_count": total_tests - len(counterexamples),
        }

        if not counterexamples:
            return {
                "holds": True,
                "counterexamples": [f"a ≤ b ⟹ {f_name}(a) ≤ {f_name}(b) for all tested inputs\n"],
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

        conversion_cache = {}

        def cached_convert(raw_val):
            if raw_val not in conversion_cache:
                conversion_cache[raw_val] = fut.arg_converter(raw_val)
            return conversion_cache[raw_val]

        try:
            converted_elements = [(cached_convert(raw), raw) for raw in all_elements]
            converted_elements.sort(key=lambda x: x[0])
        except (TypeError, ValueError) as e:
            return {
                "holds": False,
                "counterexamples": [f"Cannot sort elements for monotonicity test: {str(e)}\n"],
                "stats": {"total_count": 0, "success_count": 0},
            }

        # Single traversal through sorted pairs
        total_tests = 0
        counterexamples = []

        for i in range(len(converted_elements) - 1):
            total_tests += 1
            small_val, small_raw = converted_elements[i]
            large_val, large_raw = converted_elements[i + 1]
            # Call function on ordered inputs
            r_small = function.call(0, small_val)
            r_large = function.call(0, large_val)
            try:
                # For monotonic decreasing: if small ≤ large, then f(small) ≥ f(large)
                if r_small < r_large:
                    counterexamples.append(
                        f"{small_raw} ≤ {large_raw}\n\t"
                        f"{f_name}({small_raw}) = {r_small} < {f_name}({large_raw}) = {r_large}\n"
                    )

            except (TypeError, ValueError, AttributeError):
                counterexamples.append("Test skipped (cannot compare outputs)\n")

            # Break outer loop if max counterexamples reached
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
                "counterexamples": [f"a ≤ b ⟹ {f_name}(a) ≥ {f_name}(b) for all tested inputs\n"],
                "stats": test_stats,
            }
        else:
            return {
                "holds": False,
                "counterexamples": counterexamples,
                "stats": test_stats,
            }
