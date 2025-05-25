from core.function_under_test import FunctionUnderTest
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

    def test(self, function: FunctionUnderTest, inputs: tuple) -> TestResult:
        a = inputs[0]
        a = function.arg_converter(a)
        result = function.call(a)

        if type(result) == type(a):
            return True, f"Function preserves input type: {type(a).__name__}"
        else:
            return False, {
                f"Input type": type(a).__name__,
                f"Output type": f"{type(result).__name__}\n",
            }
