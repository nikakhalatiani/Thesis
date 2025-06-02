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

    def test(self, function: CombinedFunctionUnderTest, inputs: tuple) -> TestResult:
        fut = function.funcs[0]
        f_name = fut.func.__name__

        a = inputs[0]
        result = function.call(0, a)

        if type(result) == type(a):
            return True, f"{f_name} preserves input type: {type(a).__name__}"
        else:
            return False, (
                f"Input type: {type(a).__name__}\n\t "
                f"Output type: {type(result).__name__}\n"
            )