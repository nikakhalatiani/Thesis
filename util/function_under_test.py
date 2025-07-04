from collections.abc import Callable
from typing import Any
from enum import Enum


class FunctionConvertError:
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
        arg_converter: List of converters applied positionally. Defaults to a smart
            converter if not provided.
        result_comparator: A function to compare results of ``func``.
            Defaults to equality comparison if not provided.
    """

    def __init__(self, func: Callable,
                 arg_converter: list[Callable] | None = None,
                 result_comparator: Callable | None = None) -> None:
        self.func: Callable = func
        self.arg_converter: list[Callable] = arg_converter or [FunctionUnderTest._smart_converter]
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
                    # If all conversions fail, return the string value
                    return value

        return value

    def convert_args(self, *args: Any, arg_converter) -> tuple[Any, ...]:
        """
        Converts the provided arguments using the argument converter.

        Args:
            *args: The arguments to convert.
            arg_converter: List of argument converters to apply positionally.

        Returns:
            A tuple of converted arguments.
            If conversion fails, returns a tuple containing FunctionConvertError objects.        """
        try:
            if arg_converter:
                # If there are converters, use the last one as the default
                default = arg_converter[-1]
            else:
                default = self._smart_converter

            converted_args = []
            for i, arg in enumerate(args):
                # Use the i-th converter if available, otherwise use the default
                if i < len(arg_converter):
                    converted_args.append(arg_converter[i](arg))
                else:
                    converted_args.append(default(arg))

            return tuple(converted_args)
        except Exception as e:
            error_message = f"Error converting args {args}: {str(e)}"
            print(error_message)
            return tuple(FunctionConvertError(f"Error: {str(e)}") for _ in args)

    def call2(self, *args: Any) -> Any:
        """
          Calls the function under test with the provided arguments after applying the argument converter.

          Args:
              *args: The arguments to pass to the function under test.

        Returns:
            The result of calling the function under test with the converted arguments.
            If conversion or function call fails, returns a FunctionConvertError.
        """
        try:
            converted_args = self.convert_args(*args, arg_converter=self.arg_converter)

            # Check if any conversion failed
            if any(isinstance(arg, FunctionConvertError) for arg in converted_args):
                return converted_args[0]  # Return the first error

            result = self.func(*converted_args)
            return result
        except Exception as e:
            error_message = f"Error calling {self.func.__name__} with args {args}: {str(e)}"
            print(error_message)
            return FunctionConvertError(f"Error: {str(e)}")

    def call(self, *args: Any) -> Any:
        """
        Calls the function under test with the provided arguments directly, without applying the argument converter.

        Args:
            *args: The arguments to pass to the function under test.

        Returns:
            The result of calling the function under test with the original arguments.
            If the function call fails, returns a FunctionConvertError.
        """
        try:
            # Check if any conversion failed
            if any(isinstance(arg, FunctionConvertError) for arg in args):
                return args[0]  # Return the first error

            result = self.func(*args)
            return result
        except Exception as e:
            error_message = f"Error calling {self.func.__name__} with args {args}: {str(e)}"
            print(error_message)
            return FunctionConvertError(f"Error: {str(e)}")

    def compare_results(self, result1: Any, result2: Any) -> bool:
        """
          Compares two results using the result comparator.

          Args:
              result1: The first result to compare.
              result2: The second result to compare.

        Returns:
            True if the results are equal according to the comparator, False otherwise.
            If either result is a FunctionConvertError, returns False.
        """
        if isinstance(result1, FunctionConvertError) or isinstance(result2, FunctionConvertError):
            # Any error means the comparison fails
            return False

        return self.result_comparator(result1, result2)

    def __str__(self):
        return (
            f"FunctionUnderTest(func={self.func.__name__}, "
            f"arg_converter={'[' + ', '.join(c.__name__ for c in self.arg_converter) + ']'}, "
            f"result_comparator={self.result_comparator.__name__})"
        )


class ComparisonStrategy(Enum):
    """Strategy for comparing results across multiple functions."""
    CONSENSUS = "consensus"
    FIRST_COMPATIBLE = "first"
    MOST_RESTRICTIVE = "restrictive"


class CombinedFunctionUnderTest:
    """
    Wrapper for multiple FunctionUnderTest instances so that multi-function
    PropertyTests (e.g. Distributivity) can invoke each function by index.
    """

    def __init__(self, funcs: tuple[FunctionUnderTest, ...],
                 comparison_strategy: ComparisonStrategy = ComparisonStrategy.CONSENSUS) -> None:
        self.funcs = funcs
        self.comparison_strategy = comparison_strategy

    def names(self) -> str:
        def get_name(helper: Callable | list[Callable]) -> str:
            if isinstance(helper, list):
                names = ', '.join(h.__name__ for h in helper if h.__name__ not in ["_smart_converter", '<lambda>'])
                if not names:
                    return 'default'
                return f"[{names}]"
            name = helper.__name__
            if name == "[_smart_converter]" or name == '<lambda>':
                return 'default'
            return name

        shared_configs: dict[tuple[str, str], list[str]] = {}

        for fut in self.funcs:
            func_name = get_name(fut.func)
            arg_converter_name = get_name(fut.arg_converter)
            result_comparator_name = get_name(fut.result_comparator)

            shared_key: tuple[str, str] = (arg_converter_name, result_comparator_name)
            shared_configs.setdefault(shared_key, []).append(func_name)

        descriptions: list[str] = []

        for (arg_converter, result_comparator), func_names in shared_configs.items():
            # Create description based on number of functions
            if len(set(func_names)) == 1:
                desc = f"function {func_names[0]}"
            else:
                desc = f"functions {', '.join(func_names)}"

            # Add configuration details (only if not default)
            config_parts: list[str] = []
            if arg_converter != 'default':
                config_parts.append(f"{arg_converter} converter")
            if result_comparator != 'default':
                config_parts.append(f"{result_comparator} comparator")

            if config_parts:
                desc += f" with {' and '.join(config_parts)}"

            descriptions.append(desc)

        return ", ".join(descriptions)

    def convert_args(self, idx: int, *args: Any, arg_converter) -> tuple[Any, ...]:
        """
        Converts the provided arguments using the argument converter of the specified function.

        Args:
            idx: The index of the function whose converter to use.
            *args: The arguments to convert.
            arg_converter: The argument converter to use for conversion.

        Returns:
            A tuple of converted arguments.
        """
        return self.funcs[idx].convert_args(*args, arg_converter=arg_converter)

    def call(self, idx: int, *args: Any) -> Any:
        return self.funcs[idx].call(*args)

    def compare_results(self, result1: Any, result2: Any) -> bool:
        """
        Compare results using the configured strategy.

        Args:
            result1: First result to compare
            result2: Second result to compare

        Returns:
            True if results are considered equal according to the strategy
        """
        if not self.funcs:
            return result1 == result2

        if self.comparison_strategy == ComparisonStrategy.CONSENSUS:
            return self._consensus_compare(result1, result2)
        elif self.comparison_strategy == ComparisonStrategy.FIRST_COMPATIBLE:
            return self._first_compatible_compare(result1, result2)
        elif self.comparison_strategy == ComparisonStrategy.MOST_RESTRICTIVE:
            return self._restrictive_compare(result1, result2)
        else:
            return self._consensus_compare(result1, result2)

    def _consensus_compare(self, result1: Any, result2: Any) -> bool:
        """All compatible comparators must agree."""
        compatible_results = []
        for func in self.funcs:
            try:
                comparison_result = func.compare_results(result1, result2)
                compatible_results.append(comparison_result)
            except Exception as e:
                # Log the error and skip this comparator
                print(f"Error comparing results with {func.func.__name__}: {str(e)}")
                continue

        if not compatible_results:
            # No compatible comparators found, fall back to basic equality
            return result1 == result2

        # All compatible comparators must agree
        return all(compatible_results)

    def _first_compatible_compare(self, result1: Any, result2: Any) -> bool:
        """Use the first comparator that can handle the result types."""
        for func in self.funcs:
            try:
                return func.compare_results(result1, result2)
            except Exception as e:
                # Log the error and try the next comparator
                print(f"Error comparing results with {func.func.__name__}: {str(e)}")
                continue

        # No compatible comparator found
        return result1 == result2

    def _restrictive_compare(self, result1: Any, result2: Any) -> bool:
        """Return True only if ALL comparators (that can handle the types) return True."""
        has_any_compatible = False

        for func in self.funcs:
            try:
                result = func.compare_results(result1, result2)
                has_any_compatible = True
                if not result:
                    return False
            except Exception as e:
                # Log the error and skip this comparator
                print(f"Error comparing results with {func.func.__name__}: {str(e)}")
                continue

        # If no compatible comparators, fall back to basic equality
        return result1 == result2 if not has_any_compatible else True

    def __str__(self):
        return f"CombinedFunctionUnderTest(funcs={self.names()}, strategy={self.comparison_strategy.value})"
