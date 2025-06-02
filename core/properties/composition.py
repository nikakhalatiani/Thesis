from core.function_under_test import FunctionUnderTest
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

    def test(self, function: FunctionUnderTest, inputs: tuple) -> TestResult:
        a = inputs[0]
        a = function.arg_converter(a)
        r1 = function.call(a)
        r2 = function.call(r1)

        f_name = function.func.__name__

        if function.compare_results(r2, a):
            return True, f"{f_name}({f_name}(a)) == a"
        else:
            return False, {
                f"{f_name}({f_name}({a})): ": f"{r2}\n"
            }

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

    def test(self, function: FunctionUnderTest, inputs: tuple) -> TestResult:
        a, b = inputs[:2]
        if function.arg_converter(a) <= function.arg_converter(b):
            small, large = a, b
        else:
            small, large = b, a

        r_small = function.call(small)
        r_large = function.call(large)

        f_name = function.func.__name__

        if r_small <= r_large:
            return True, (
                f"a ≤ b ⟹ {f_name}(a) ≤ {f_name}(b)"
            )
        else:
            return False, {
                f"{small} ≤ {large}": "",
                f"{f_name}({small}) ≥ {f_name}({large})":"",
                f"{r_small} ≥ {r_large}": "\n"
            }


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

    def test(self, function: FunctionUnderTest, inputs: tuple) -> TestResult:
        a, b = inputs[:2]
        if function.arg_converter(a) <= function.arg_converter(b):
            small, large = a, b
        else:
            small, large = b, a

        r_large = function.call(large)
        r_small = function.call(small)

        f_name = function.func.__name__

        if r_large >= r_small:
            return True, (
                f"a ≥ b ⟹ {f_name}(a) ≥ {f_name}(b)"
            )
        else:
            return False, {
                f"{large} ≥ {small}":"",
                f"{f_name}({large}) ≤ {f_name}({small})":"",
                f"{r_large} ≤ {r_small}": "\n"
            }