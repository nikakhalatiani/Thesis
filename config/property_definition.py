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
        arity: The number of arguments required by the property test.
    """

    def __init__(self, name: str, test_function: Callable[[FunctionUnderTest, Any], tuple[bool, dict[str, str] | str]],
                 arity: int) -> None:
        self.name: str = name
        self.test_function: Callable[[FunctionUnderTest, Any], tuple[bool, dict[str, str] | str]] = test_function
        self.arity: int = arity
