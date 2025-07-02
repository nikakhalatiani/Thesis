from util.function_under_test import CombinedFunctionUnderTest
from core.properties.property_test import PropertyTest, TestResult, TestStats, ExecutionTrace


class InjectivityTest(PropertyTest):
    """Test whether a function is injective (one-to-one) for the given arity and projection strategy.
    An injective function maps distinct inputs to distinct outputs."""

    def __init__(self, function_arity: int = 1, projection_func=None):
        """Create a new injectivity test.

        Parameters:
        function_arity:
            The number of arguments the function accepts. Defaults to 1.
        projection_func:
            Optional function to extract comparable values from function results.
            Useful for functions that return complex objects where only part
            should be compared for injectivity.
        """
        super().__init__(
            name="Injectivity",
            input_arity=function_arity,
            function_arity=function_arity,
            description=f"Checks injectivity for {function_arity}-ary function",
            category="Behavioral",
        )
        self.projection_func = projection_func or (lambda x: x)

    def test(self, function: CombinedFunctionUnderTest, inputs, max_counterexamples) -> TestResult:
        fut = function.funcs[0]
        f_name = fut.func.__name__

        valid_inputs = {
            tuple(input_set[: self.function_arity])
            for input_set in inputs
            if len(input_set) >= self.function_arity
        }

        if not valid_inputs:
            return {
                "holds": False,
                "counterexamples": ["No valid inputs found\n"],
                "successes": [],
                "stats": {"total_count": 0, "success_count": 0},
                "execution_traces": [],
            }

        counterexamples = []
        total_tests = 0
        result_map = []  # List of (projected_result, args, result) tuples
        execution_traces: list[ExecutionTrace] = []

        for args in valid_inputs:
            total_tests += 1

            # Convert args using the function's argument converter
            conv_args = function.convert_args(0, *args, arg_converter=fut.arg_converter)
            # Call the function with converted args
            result = function.call(0, *conv_args)

            projected_result = self.projection_func(result)

            # Check if we've seen an equivalent projected result before using custom comparison
            is_unique = True
            matching_entry = None

            for prev_projected_result, prev_args, prev_result in result_map:
                if function.compare_results(projected_result, prev_projected_result):
                    is_unique = False
                    matching_entry = (prev_projected_result, prev_args, prev_result)
                    break

            if not is_unique:
                _, prev_args, prev_result = matching_entry
                counterexamples.append(
                    f"{f_name}{tuple(conv_args)} = {result}\n\t"
                    f"{f_name}{tuple(prev_args)} = {prev_result}\n"
                )

                if len(counterexamples) >= max_counterexamples:
                    break
            else:
                result_map.append((projected_result, conv_args, result))

            execution_traces.append(
                {
                    "input": tuple(args),
                    "comparison_result": is_unique,
                    "property_name": self.name,
                }
            )

        test_stats: TestStats = {
            "total_count": total_tests,
            "success_count": total_tests - len(counterexamples),
        }

        return {
            "holds": not counterexamples,
            "counterexamples": counterexamples,
            "successes": [f"{f_name} is injective on the tested inputs\n"],
            "stats": test_stats,
            "execution_traces": execution_traces,
        }


class FixedPointTest(PropertyTest):
    """Test whether a function has fixed points, i.e., inputs for which f(x) = x (or a specified argument index).
    Useful for identifying idempotent or stable states."""

    def __init__(self, function_arity: int = 1, result_index: int = 0):
        """Create a new fixed point test.

        Parameters:
        function_arity:
            The number of arguments the function accepts. Defaults to 1.
        result_index:
            Which argument position to compare with the result for fixed point.
            For f(x) = x, this would be 0. For f(state, value) where we check
            if the state is unchanged, this would be 0.
        """
        super().__init__(
            name="FixedPoint",
            input_arity=function_arity,
            function_arity=function_arity,
            description=f"Checks for fixed points comparing result with argument {result_index}",
            category="Behavioral",
        )
        self.result_index = result_index

    def test(
            self, function: CombinedFunctionUnderTest, inputs, max_counterexamples
    ) -> TestResult:
        fut = function.funcs[0]
        f_name = fut.func.__name__

        # Extract all unique elements from valid input tuples
        valid_inputs = [
            input_set[: self.function_arity]
            for input_set in inputs
            if len(input_set) >= self.function_arity
        ]

        if not valid_inputs:
            return {
                "holds": False,
                "counterexamples": ["No valid inputs found\n"],
                "successes": [],
                "stats": {"total_count": 0, "success_count": 0},
                "execution_traces": [],
            }

        total_tests = 0
        fixed_points = []
        counterexamples = []
        execution_traces: list[ExecutionTrace] = []

        for valid_input in valid_inputs:
            total_tests += 1

            if self.result_index < len(valid_input):
                args = list(valid_input)
                # Convert args using the function's argument converter
                conv_args = function.convert_args(
                    0, *args, arg_converter=fut.arg_converter
                )
                # Call the function with converted args
                expected = conv_args[self.result_index]
                # Call the function
                result1 = function.call(0, *conv_args)
                # Double-check if result really matches expected
                result2 = function.call(0, *conv_args)

                comparison1 = function.compare_results(result1, expected)
                comparison2 = function.compare_results(result2, expected)
                comparison = comparison1 and comparison2
                execution_traces.append(
                    {
                        "input": tuple(args),
                        "comparison_result": comparison,
                        "property_name": self.name,
                    }
                )

                if comparison:
                    fixed_points.append(
                        f"{f_name}{tuple(conv_args)}: {result1} == {conv_args[self.result_index]}\n"
                    )
                else:
                    counterexamples.append(
                        f"{f_name}{tuple(conv_args)}: {result1} ≠ {conv_args[self.result_index]}\n"
                    )

        test_stats: TestStats = {
            "total_count": total_tests,
            # 'success_count': total_tests if fixed_points else 0
            "success_count": len(fixed_points),
        }

        return {
            "holds": bool(fixed_points),
            "counterexamples": counterexamples,
            "successes": fixed_points,
            "stats": test_stats,
            "execution_traces": execution_traces,
        }


class DeterminismTest(PropertyTest):
    """Test whether a function is deterministic, i.e., the same input always produces the same output.
    Useful for detecting randomness or side effects."""

    def __init__(self, function_arity: int = 1):
        """Create a new determinism test.

        Parameters:
        function_arity:
            The number of arguments the function accepts. Defaults to 1.
        """
        super().__init__(
            name="Determinism",
            input_arity=function_arity,
            function_arity=function_arity,
            description=f"Tests if {function_arity}-ary function gives same output for same input",
            category="Behavioral",
        )

    def test(
            self, function: CombinedFunctionUnderTest, inputs, max_counterexamples
    ) -> TestResult:
        fut = function.funcs[0]
        f_name = fut.func.__name__
        input_arity = self.input_arity

        valid_inputs = {
            tuple(input_set[:input_arity])
            for input_set in inputs
            if len(input_set) >= input_arity
        }

        if not valid_inputs:
            return {
                "holds": False,
                "counterexamples": ["No valid inputs found\n"],
                "successes": [],
                "stats": {"total_count": 0, "success_count": 0},
                "execution_traces": [],
            }

        # Test determinism for each valid input
        total_tests = 0
        counterexamples = []
        execution_traces: list[ExecutionTrace] = []

        for args in valid_inputs:
            total_tests += 1

            # Convert args using the function's argument converter
            conv_args = function.convert_args(0, *args, arg_converter=fut.arg_converter)

            # Call function multiple times with the same input
            results = [function.call(0, *conv_args) for _ in range(max_counterexamples)]

            # Check if all results are the same
            first_result = results[0]
            first_different_result = None
            for idx, r in enumerate(results[1:], start=1):
                if not function.compare_results(first_result, r):
                    first_different_result = (idx, r)
                    break

            deterministic = first_different_result is None
            execution_traces.append(
                {
                    "input": tuple(args),
                    "comparison_result": deterministic,
                    "property_name": self.name,
                }
            )

            if not deterministic:
                # If results differ, record the counterexample
                idx_diff, diff_val = first_different_result
                counterexamples.append(
                    f"{f_name}{tuple(conv_args)} on run #1: {first_result}\n\t"
                    f"{f_name}{tuple(conv_args)} on run #{idx_diff + 1}: {diff_val}\n"
                )

                if len(counterexamples) >= max_counterexamples:
                    break

        # Build result
        test_stats: TestStats = {
            "total_count": total_tests,
            "success_count": total_tests - len(counterexamples),
        }

        return {
            "holds": not counterexamples,
            "counterexamples": counterexamples,
            "successes": [
                f"{f_name} is deterministic for all tested inputs\n"
            ],
            "stats": test_stats,
            "execution_traces": execution_traces,
        }

#
# class MonotonicallyIncreasingTest(PropertyTest):
#     """Test if f is monotonically increasing (preserves order relationships)."""
#
#     def __init__(self):
#         super().__init__(
#             name="MonotonicallyIncreasing",
#             input_arity=2,
#             function_arity=1,
#             description="Tests if a ≤ b implies f(a) ≤ f(b)",
#             category="Behavioral"
#         )
#
#     def test(self, function: CombinedFunctionUnderTest, inputs, max_counterexamples) -> TestResult:
#         fut = function.funcs[0]
#         f_name = fut.func.__name__
#
#         all_elements = frozenset(chain.from_iterable(inputs))
#
#         if len(all_elements) < self.input_arity:
#             return {
#                 "holds": False,
#                 "counterexamples": ["Not enough elements provided\n"],
#                 "stats": {"total_count": 0, "success_count": 0},
#             }
#
#         conversion_cache = {}
#
#         def cached_convert(raw_val):
#             if raw_val not in conversion_cache:
#                 conversion_cache[raw_val] = fut.arg_converter(raw_val)
#             return conversion_cache[raw_val]
#
#         try:
#             # Convert and sort raw inputs
#             converted_elements = [(cached_convert(raw), raw) for raw in all_elements]
#             converted_elements.sort(key=lambda x: x[0])
#         except (TypeError, ValueError) as e:
#             return {
#                 "holds": False,
#                 "counterexamples": [f"Cannot sort elements for monotonicity test: {str(e)}\n"],
#                 "stats": {"total_count": 0, "success_count": 0},
#             }
#
#         total_tests = 0
#         counterexamples = []
#
#         for i in range(len(converted_elements) - 1):
#             total_tests += 1
#             small_val, small_raw = converted_elements[i]
#             large_val, large_raw = converted_elements[i + 1]
#             small_result = function.call(0, small_val)
#             large_result = function.call(0, large_val)
#
#             try:
#                 if small_result > large_result:
#                     counterexamples.append(
#                         f"{small_raw} ≤ {small_raw}\n\t"
#                         f"{f_name}({small_raw}) = {small_result} > {f_name}({small_raw}) = {large_result}\n"
#                     )
#
#
#             except (TypeError, ValueError, AttributeError):
#                 counterexamples.append("Test skipped (cannot compare outputs)\n")
#
#             if len(counterexamples) >= max_counterexamples:
#                 break
#
#         test_stats: TestStats = {
#             "total_count": total_tests,
#             "success_count": total_tests - len(counterexamples),
#         }
#
#         if not counterexamples:
#             return {
#                 "holds": True,
#                 "counterexamples": [f"a ≤ b ⟹ {f_name}(a) ≤ {f_name}(b) for all tested inputs\n"],
#                 "stats": test_stats,
#             }
#         else:
#             return {
#                 "holds": False,
#                 "counterexamples": counterexamples,
#                 "stats": test_stats,
#             }
#
#
# class MonotonicallyDecreasingTest(PropertyTest):
#     """Test if f is monotonically decreasing (reverses order)."""
#
#     def __init__(self):
#         super().__init__(
#             name="MonotonicallyDecreasing",
#             input_arity=2,
#             function_arity=1,
#             description="Tests if a ≤ b implies f(a) ≥ f(b)",
#             category="Behavioral"
#         )
#
#     def test(self, function: CombinedFunctionUnderTest, inputs, max_counterexamples) -> TestResult:
#         fut = function.funcs[0]
#         f_name = fut.func.__name__
#
#         all_elements = frozenset(chain.from_iterable(inputs))
#
#         if len(all_elements) < self.input_arity:
#             return {
#                 "holds": False,
#                 "counterexamples": ["Not enough elements provided\n"],
#                 "stats": {"total_count": 0, "success_count": 0},
#             }
#
#         conversion_cache = {}
#
#         def cached_convert(raw_val):
#             if raw_val not in conversion_cache:
#                 conversion_cache[raw_val] = fut.arg_converter(raw_val)
#             return conversion_cache[raw_val]
#
#         try:
#             converted_elements = [(cached_convert(raw), raw) for raw in all_elements]
#             converted_elements.sort(key=lambda x: x[0])
#         except (TypeError, ValueError) as e:
#             return {
#                 "holds": False,
#                 "counterexamples": [f"Cannot sort elements for monotonicity test: {str(e)}\n"],
#                 "stats": {"total_count": 0, "success_count": 0},
#             }
#
#         # Single traversal through sorted pairs
#         total_tests = 0
#         counterexamples = []
#
#         for i in range(len(converted_elements) - 1):
#             total_tests += 1
#             small_val, small_raw = converted_elements[i]
#             large_val, large_raw = converted_elements[i + 1]
#             # Call function on ordered inputs
#             r_small = function.call(0, small_val)
#             r_large = function.call(0, large_val)
#             try:
#                 # For monotonic decreasing: if small ≤ large, then f(small) ≥ f(large)
#                 if r_small < r_large:
#                     counterexamples.append(
#                         f"{small_raw} ≤ {large_raw}\n\t"
#                         f"{f_name}({small_raw}) = {r_small} < {f_name}({large_raw}) = {r_large}\n"
#                     )
#
#             except (TypeError, ValueError, AttributeError):
#                 counterexamples.append("Test skipped (cannot compare outputs)\n")
#
#             # Break outer loop if max counterexamples reached
#             if len(counterexamples) >= max_counterexamples:
#                 break
#
#         # Build result
#         test_stats: TestStats = {
#             'total_count': total_tests,
#             'success_count': total_tests - len(counterexamples)
#         }
#
#         if not counterexamples:
#             return {
#                 "holds": True,
#                 "counterexamples": [f"a ≤ b ⟹ {f_name}(a) ≥ {f_name}(b) for all tested inputs\n"],
#                 "stats": test_stats,
#             }
#         else:
#             return {
#                 "holds": False,
#                 "counterexamples": counterexamples,
#                 "stats": test_stats,
#             }
