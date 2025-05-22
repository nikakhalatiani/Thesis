from collections.abc import Callable
from typing import Any

from core.function_under_test import FunctionUnderTest


class PropertyDefinition:
    """
    Property definition for testing functions.

    Attributes:
        name: The name of the property.
        test_function:
            The function used to test the property. It takes a `FunctionUnderTest` instance
            and inputs, and returns a tuple containing a boolean indicating success and
            an optional dictionary of counterexamples.
        input_arity: The number of inputs required for testing
        function_arity: The number of arguments the function must accept to be applicable
    """

    def __init__(self, name: str, test_function: Callable[[FunctionUnderTest, Any], tuple[bool, dict[str, str] | str]],
                 input_arity: int, function_arity: int) -> None:
        self.name = name
        self.test_function = test_function
        self.input_arity = input_arity
        self.function_arity = function_arity
