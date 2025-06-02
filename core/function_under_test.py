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
            print(error_message)
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

    def __str__(self):
        return f"FunctionUnderTest(func={self.func.__name__}, arg_converter={self.arg_converter.__name__}, result_comparator={self.result_comparator.__name__})"


class CombinedFunctionUnderTest:
    """
    Wrapper for  multiple FunctionUnderTest instances so that multi-function
    PropertyTests (e.g. Distributivity) can invoke each function by index.
    """

    def __init__(self, funcs: tuple[FunctionUnderTest, ...]) -> None:
        self.funcs = funcs

    def names(self) -> str:
        def get_name(helper: Callable) -> str:
            name = helper.__name__
            if name.startswith('_') or name == '<lambda>':
                return 'default'
            return name

        parts = []
        for fut in self.funcs:
            func_name = get_name(fut.func)
            arg_converter_name = get_name(fut.arg_converter)
            result_comparator_name = get_name(fut.result_comparator)
            parts.append(
                f"function {func_name} "
                f"with {arg_converter_name} converter "
                f"and {result_comparator_name} comparator"
            )
        return ", ".join(parts)

    def call(self, idx: int, *args: Any) -> Any:
        return self.funcs[idx].call(*args)

    #TODO needs better implementation as applying one comparator not good enought
    def compare_results(self, result1: Any, result2: Any) -> bool:
        # Default to using the first function's comparator
        return self.funcs[0].compare_results(result1, result2)


    def __str__(self):
        return f"CombinedFunctionUnderTest(funcs={self.names()})"

    #
    # def compare_results(self, idx1: int, res1, idx2: int, res2) -> bool:
    #     """Compare results of two functions via their own comparators."""
    #     f1 = self.funcs[idx1]
    #     f2 = self.funcs[idx2]
    #     # If idx1 == idx2, compare within same comparator;
    #     # otherwise we can choose one or default to exact.
    #     return f1.result_comparator(res1, res2) and f2.result_comparator(res1, res2) if idx1 != idx2 else f1.result_comparator(res1, res2)
