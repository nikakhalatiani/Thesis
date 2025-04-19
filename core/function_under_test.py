from collections.abc import Callable
from typing import Any


class FunctionUnderTest:
    """
    A function under test, along with optional argument conversion and result comparison logic.

    Attributes:
        func: The function to be tested.
        arg_converter: A function to convert arguments before passing them to `func`.
                                          Defaults to an identity function if not provided.
        result_comparator: A function to compare results of `func`.
                                             Defaults to equality comparison if not provided.
    """

    def __init__(self, func: Callable, arg_converter: Callable | None = None,
                 result_comparator: Callable | None = None) -> None:
        self.func: Callable = func
        self.arg_converter: Callable = arg_converter or (lambda x: x)
        self.result_comparator: Callable[[Any, Any], bool] = result_comparator or (lambda x, y: x == y)

    def call(self, *args: Any) -> Any:
        """
          Calls the function under test with the provided arguments after applying the argument converter.

          Args:
              *args: The arguments to pass to the function under test.

          Returns:
              The result of calling the function under test with the converted arguments.

          Notes:
              - The `arg_converter` is applied to each argument before passing them to the function.
              - If no `arg_converter` is provided during initialization, the arguments are passed as-is.
        """
        converted_args = [self.arg_converter(arg) for arg in args]
        return self.func(*converted_args)

    def compare_results(self, result1: Any, result2: Any) -> bool:
        """
          Compares two results using the result comparator.

          Args:
              result1: The first result to compare.
              result2: The second result to compare.

          Returns:
              True if the results are equal **according to the comparator**, False otherwise.
        """
        return self.result_comparator(result1, result2)
