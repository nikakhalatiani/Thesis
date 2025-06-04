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


    # ============================================================================
    # BOUNDARY PROPERTIES - Behavior at limits and boundaries
    # ============================================================================

    # TODO think about this to inverse logic of finding identity element
    # @staticmethod
    # def identity_element_test(function: FunctionUnderTest, inputs: tuple) -> tuple[bool, dict[str, str] | str]:
    #     """Test if there exists an identity element"""
    #     a, candidate_identity = inputs
    #     r1 = function.call(a, candidate_identity)
    #     r2 = function.call(candidate_identity, a)
    #
    #     if function.compare_results(r1, function.arg_converter(a)) and function.compare_results(r2, function.arg_converter(a)):
    #         return True, f"{candidate_identity} is an identity element"
    #     else:
    #         return False, {
    #             f"{function.func.__name__}({a}, {candidate_identity})": r1,
    #             f"{function.func.__name__}({candidate_identity}, {a})": r2,
    #             f"Expected both to equal": f"{a}"
    #         }

    # TODO think about this to inverse logic as above
    # @staticmethod
    # def absorbing_element_test(function: FunctionUnderTest, inputs: tuple) -> tuple[bool, dict[str, str] | str]:
    #     """Test if there exists an absorbing/zero element"""
    #     a, candidate_absorber = inputs
    #     r1 = function.call(a, candidate_absorber)
    #     r2 = function.call(candidate_absorber, a)
    #
    #     if function.compare_results(r1, function.arg_converter(candidate_absorber)) and function.compare_results(r2, function.arg_converter(candidate_absorber)):
    #         return False, {
    #             f"{function.func.__name__}({a}, {candidate_absorber})": r1,
    #             f"{function.func.__name__}({candidate_absorber}, {a})": r2,
    #             f"Expected both to equal": f"{candidate_absorber}"
    #         }
    #
    #     else:
    #         return True, f"No absorbing element found"

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
            early_stopping: bool = False
    ) -> PropertyOutcome:

        holds = True
        counterexamples: list[str] = []
        success_count = 0
        total_count = 0

        for inputs in input_sets:
            if early_stopping and not holds:
                break
            if len(inputs) < property_test.input_arity:
                continue

            total_count += 1
            success, example_data = property_test.test(function, inputs[:property_test.input_arity])

            if success:
                success_count += 1
                if holds:
                    counterexamples = [example_data]
            else:
                if holds:
                    counterexamples = [example_data]
                    # first time we see a failure
                    holds = False
                else:
                    if len(counterexamples) < self._max_examples:
                        # example_data is normally a str or a dict; convert to string
                        counterexamples.append(str(example_data))


        # Compute confidence = success_count / total_count
        confidence = (success_count / total_count) if total_count > 0 else 0.0

        return PropertyOutcome(
            holds=holds,
            counterexamples=counterexamples,
            confidence=confidence,
            total_tests=total_count,
        )
