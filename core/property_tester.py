from typing import Any, TypedDict

from core.function_under_test import CombinedFunctionUnderTest
from core.properties.property_test import PropertyTest


class PropertyOutcome(TypedDict):
    """
    Holds the result of testing a PropertyTest against a CombinedFunctionUnderTest.
    """
    holds: bool
    counterexamples: list[str]
    confidence: float
    total_tests: int


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
            early_stopping=False
    ) -> PropertyOutcome:

        success, result_data, test_stats = property_test.test(function, input_sets, early_stopping)

        total_count = test_stats['total_count']
        success_count = test_stats['success_count']
        confidence = (success_count / total_count) if total_count > 0 else 0.0

        if success:
            return PropertyOutcome(
                holds=True,
                counterexamples=result_data,
                confidence=confidence,
                total_tests=total_count,
            )
        else:
            return PropertyOutcome(
                holds=False,
                counterexamples=result_data[:self._max_examples],
                confidence=confidence,
                total_tests=total_count,
            )
