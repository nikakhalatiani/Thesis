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

        if function.compare_results(r2, a):
            return True, f"{function.func.__name__}({function.func.__name__}(a)) == a"
        else:
            return False, {
                f"{function.func.__name__}({function.func.__name__}({a}))": f"{r2}\n"
            }
