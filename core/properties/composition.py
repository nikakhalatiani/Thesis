from core.function_under_test import CombinedFunctionUnderTest
from core.properties.property_test import TestResult, PropertyTest


class InvolutionTest(PropertyTest):
    """Test if f(f(x)) = x (function is its own inverse)"""

    def __init__(self):
        super().__init__(
            name="Involution",
            input_arity=1,
            function_arity=1,
            description="Tests if f(f(x)) equals x",
            category="Composition"
        )

    def test(self, function: CombinedFunctionUnderTest, inputs: tuple) -> TestResult:
        fut = function.funcs[0]
        f_name = fut.func.__name__

        # Convert input and apply twice
        a = fut.arg_converter(inputs[0])
        r1 = function.call(0, a)
        r2 = function.call(0, r1)

        if function.compare_results(r2, a):
            return True, f"{f_name}({f_name}(a)) == a"
        else:
            return False, (
                f"{f_name}({f_name}({a})): {r2}\n"
            )


class MonotonicallyIncreasingTest(PropertyTest):
    """Test if f is monotonically increasing (preserves order relationships)."""

    def __init__(self):
        super().__init__(
            name="MonotonicallyIncreasing",
            input_arity=2,
            function_arity=1,
            description="Tests if a ≤ b implies f(a) ≤ f(b)",
            category="Order"
        )

    def test(self, function: CombinedFunctionUnderTest, inputs: tuple) -> TestResult:
        fut = function.funcs[0]
        f_name = fut.func.__name__

        # Check monotonicity
        try:
            # Convert inputs
            a_raw, b_raw = inputs[:2]
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

            if r_small <= r_large:
                return True, f"a ≤ b ⟹ {f_name}(a) ≤ {f_name}(b)"
            else:
                return False, (
                    f"{raw_small} ≤ {raw_large}\n\t"
                    f"{f_name}({raw_small}) > {f_name}({raw_large})\n\t"
                    f"{r_small} > {r_large}\n"
                )
        except (TypeError, ValueError, AttributeError):
            return False, f"Monotonicity test skipped (cannot compare outputs/inputs of {f_name})"


class MonotonicallyDecreasingTest(PropertyTest):
    """Test if f is monotonically decreasing (reverses order)."""

    def __init__(self):
        super().__init__(
            name="MonotonicallyDecreasing",
            input_arity=2,
            function_arity=1,
            description="Tests if a ≥ b implies f(a) ≥ f(b)",
            category="Order"
        )

    def test(self, function: CombinedFunctionUnderTest, inputs: tuple) -> TestResult:
        fut = function.funcs[0]
        f_name = fut.func.__name__

        try:
            # Convert inputs
            a_raw, b_raw = inputs[:2]
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

            if r_small >= r_large:
                return True, f"a ≤ b ⟹ {f_name}(a) ≥ {f_name}(b)"

            else:
                return False, (
                    f"{raw_small} ≤ {raw_large}\n\t"
                    f"{f_name}({raw_small}) < {f_name}({raw_large})\n\t"
                    f"{r_small} < {r_large}\n"
                )
        except (TypeError, ValueError, AttributeError):
            return False, f"Monotonicity test skipped (cannot compare outputs/inputs of {f_name})"
