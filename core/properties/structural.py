from core.function_under_test import CombinedFunctionUnderTest
from core.properties.property_test import PropertyTest, TestResult


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

    def test(self, function: CombinedFunctionUnderTest, inputs, early_stopping) -> TestResult:
        f_name = function.funcs[0].func.__name__
        input_arity = self.input_arity

        # Filter valid inputs based on arity
        valid_inputs = [input_set for input_set in inputs if len(input_set) >= input_arity]

        if not valid_inputs:
            return False, [f"Type preservation test failed: No valid input sets provided for {f_name}\n"], {
                'total_count': 0, 'success_count': 0
            }

        # Test type preservation for each valid input
        total_tests = 0
        counterexamples = []

        for input_set in valid_inputs:
            a = input_set[0]
            total_tests += 1

            result = function.call(0, a)

            if type(result) != type(a):
                counterexamples.append(
                    f"Input type: {type(a).__name__}\n\t"
                    f"Output type: {type(result).__name__}\n"
                )

                if early_stopping:
                    break

        # Build result
        test_stats = {
            'total_count': total_tests,
            'success_count': total_tests - len(counterexamples)
        }

        if not counterexamples:
            return True, [f"{f_name} preserves input type\n"], test_stats
        else:
            return False, counterexamples, test_stats


class MonotonicallyIncreasingTest(PropertyTest):
    """Test if f is monotonically increasing (preserves order relationships)."""

    def __init__(self):
        super().__init__(
            name="MonotonicallyIncreasing",
            input_arity=2,
            function_arity=1,
            description="Tests if a ≤ b implies f(a) ≤ f(b)",
            category="Structural"
        )

    def test(self, function: CombinedFunctionUnderTest, inputs, early_stopping) -> TestResult:
        fut = function.funcs[0]
        f_name = fut.func.__name__
        input_arity = self.input_arity

        # Filter valid inputs based on arity
        valid_inputs = [input_set for input_set in inputs if len(input_set) >= input_arity]

        if not valid_inputs:
            return False, [f"Monotonicity test failed: No valid input sets provided for {f_name}\n"], {
                'total_count': 0, 'success_count': 0
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
        test_stats = {
            'total_count': total_tests,
            'success_count': total_tests - len(counterexamples)
        }

        if not counterexamples:
            return True, [f"a ≤ b ⟹ {f_name}(a) ≤ {f_name}(b)\n"], test_stats
        else:
            return False, counterexamples, test_stats


class MonotonicallyDecreasingTest(PropertyTest):
    """Test if f is monotonically decreasing (reverses order)."""

    def __init__(self):
        super().__init__(
            name="MonotonicallyDecreasing",
            input_arity=2,
            function_arity=1,
            description="Tests if a ≤  b implies f(a) ≥ f(b)",
            category="Structural"
        )

    def test(self, function: CombinedFunctionUnderTest, inputs, early_stopping) -> TestResult:
        fut = function.funcs[0]
        f_name = fut.func.__name__
        input_arity = self.input_arity

        # Filter valid inputs based on arity
        valid_inputs = [input_set for input_set in inputs if len(input_set) >= input_arity]

        if not valid_inputs:
            return False, [f"Monotonicity test failed: No valid input sets provided for {f_name}\n"], {
                'total_count': 0, 'success_count': 0
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
        test_stats = {
            'total_count': total_tests,
            'success_count': total_tests - len(counterexamples)
        }

        if not counterexamples:
            return True, [f"a ≤ b ⟹ {f_name}(a) ≥ {f_name}(b)\n"], test_stats
        else:
            return False, counterexamples, test_stats
