from typing import Any, TypedDict
from abc import ABC, abstractmethod

from core.function_under_test import CombinedFunctionUnderTest


class TestStats(TypedDict):
    total_count: int
    success_count: int


class TestResult(TypedDict):
    holds: bool
    counterexamples: list[str]
    stats: TestStats


class PropertyTest(ABC):
    """Abstract base class for all property tests."""

    def __init__(self, name: str, input_arity: int, function_arity: int,
                 description: str = "", category: str = ""):
        self.name = name
        self.input_arity = input_arity
        self.function_arity = function_arity
        self.description = description
        self.category = category
        self.num_functions: int = 1  # default: single-function properties

    @abstractmethod
    def test(self, candidate: CombinedFunctionUnderTest, inputs: list[tuple], early_stopping: bool) -> TestResult:
        """Execute the property test."""
        pass

    def is_applicable(self, candidate: CombinedFunctionUnderTest) -> bool:
        """Check if this property test is applicable to the given function."""
        import inspect
        if self.num_functions != len(candidate.funcs):
            return False
        # Ensure each inner function has the right arity
        return all(len(inspect.signature(fut.func).parameters) == self.function_arity for fut in candidate.funcs)

    def __str__(self) -> str:
        return f"{self.name} (arity: {self.input_arity}/{self.function_arity})"


class PropertyTester:
    def __init__(self, max_examples: int) -> None:
        self._max_examples = max_examples

    # TODO think about this to reverse logic of finding fixed point
    # @staticmethod
    # def fixpoint_test(function: FunctionUnderTest, inputs: tuple) -> tuple[bool, dict[str, str] | str]:
    #     """Test if input is a fixed point: f(x) = x"""
    #     a = inputs[0]
    #     result = function.call(a)
    #
    #     if function.compare_results(result, function.arg_converter(a)):
    #         return True, f"{a} is a fixed point: {function.func.__name__}({a}) = {a}"
    #     else:
    #         return False, {
    #             f"{function.func.__name__}({a})": result,
    #             f"Expected": a,
    #             "Fixed point": "False"
    #         }

    # ============================================================================
    # STRUCTURAL PROPERTIES - Shape and structure preservation
    # ============================================================================

    # TODO think about how to integrate try except into the logic
    # @staticmethod
    # def size_preservation_test(function: FunctionUnderTest, inputs: tuple) -> tuple[bool, dict[str, str] | str]:
    #     """Test if function preserves size/length of input"""
    #     a = inputs[0]
    #     a = function.arg_converter(a)
    #     result = function.call(a)
    #
    #     try:
    #         input_len = len(a)
    #         output_len = len(result)
    #
    #         if input_len == output_len:
    #             return True, f"Function preserves size: {input_len}"
    #         else:
    #             return False, {
    #                 f"Input size": input_len,
    #                 f"Output size": f"{output_len}\n"
    #             }
    #     except TypeError:
    #         return True, "Size preservation test skipped (length not applicable)"

    # TODO interesting usage of try catch needs attention to analyze the behavior (CONVERTER)
    # @staticmethod
    # def closure_test(function: FunctionUnderTest, inputs: tuple) -> tuple[bool, dict[str, str] | str]:
    #     """Test if function result can be used as input (closure property)"""
    #     a = inputs[0]
    #
    #     try:
    #         result = function.call(a)
    #         # Try to use result as input to the same function
    #         second_result = function.call(result)
    #         return True, f"Function exhibits closure: output can be used as input"
    #     except Exception as e:
    #         return False, {
    #             f"First call {function.func.__name__}({a})": f"Success",
    #             f"Second call {function.func.__name__}(result)": f"Failed: {str(e)}",
    #             "Closure": "False"
    #         }

    def test_property(
            self,
            function: CombinedFunctionUnderTest,
            property_test: PropertyTest,
            input_sets: list[Any],
            early_stopping=False,
    ) -> TestResult:
        result = property_test.test(function, input_sets, early_stopping)

        return TestResult(
            holds=result['holds'],
            counterexamples=result['counterexamples'][:self._max_examples],
            stats=result['stats'],
        )
