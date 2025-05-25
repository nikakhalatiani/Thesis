from collections.abc import Callable
from typing import Any


class FunctionCallError:
    """
    Custom error class for representing function call failures.

    Attributes:
        message: Error message describing the failure
    """

    def __init__(self, message: str):
        self.message = message

    def __repr__(self):
        return self.message

    def __str__(self):
        return self.message


class FunctionUnderTest:
    """
    A function under test, along with optional argument conversion and result comparison logic.

    Attributes:
        func: The function to be tested.
        arg_converter: A function to convert arguments before passing them to `func`.
                       Defaults to a smart converter if not provided.
        result_comparator: A function to compare results of `func`.
                        Defaults to equality comparison if not provided.
    """

    def __init__(self, func: Callable, arg_converter: Callable | None = None,
                 result_comparator: Callable | None = None) -> None:
        self.func: Callable = func
        self.arg_converter: Callable = arg_converter or self._smart_converter
        self.result_comparator: Callable[[Any, Any], bool] = result_comparator or (lambda x, y: x == y)

    @staticmethod
    def _smart_converter(value: str) -> Any:
        """
        Attempts to intelligently convert string inputs to appropriate types based on operation needs.

        This helps prevent type errors when the fuzzer generates string inputs but the function
        expects numeric types.

        Args:
            value: The value to convert from the fuzzer

        Returns:
            The converted value in an appropriate type
        """
        if isinstance(value, (int, float)):
            return value

        if isinstance(value, str):
            try:
                return int(value)
            except ValueError:
                try:
                    return float(value)
                except ValueError:
                    # If all conversions fail, return the original value
                    return value

        return value

    def call(self, *args: Any) -> Any:
        """
          Calls the function under test with the provided arguments after applying the argument converter.

          Args:
              *args: The arguments to pass to the function under test.

        Returns:
            The result of calling the function under test with the converted arguments.
            If conversion or function call fails, returns a FunctionCallError.
        """
        try:
            converted_args = [self.arg_converter(arg) for arg in args]
            result = self.func(*converted_args)
            return result
        except Exception as e:
            error_message = f"Error calling {self.func.__name__} with args {args}: {str(e)}"
            print(error_message)  # Log the error for debugging
            return FunctionCallError(f"Error: {str(e)}")

    def compare_results(self, result1: Any, result2: Any) -> bool:
        """
          Compares two results using the result comparator.

          Args:
              result1: The first result to compare.
              result2: The second result to compare.

        Returns:
            True if the results are equal according to the comparator, False otherwise.
            If either result is a FunctionCallError, returns False.
        """
        if isinstance(result1, FunctionCallError) or isinstance(result2, FunctionCallError):
            # Any error means the comparison fails
            return False

        return self.result_comparator(result1, result2)
