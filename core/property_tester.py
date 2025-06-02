from typing import Any

from core.properties import PropertyRegistry
from core.function_under_test import FunctionUnderTest, CombinedFunctionUnderTest
from core.properties.property_test import PropertyTest


class PropertyTester:
    """
    A class to test and infer properties of functions under test.

    Attributes:
        properties: Stores the inferred properties and their boolean results.
        examples: Stores counter-examples for properties that fail.
        confidence_levels: Stores confidence levels for each property.
    """

    def __init__(self, registry: PropertyRegistry, max_examples: int) -> None:
        #TODO think if we need this attributes
        self.properties: dict[str, bool] = {}
        self.examples: dict[str, dict[str, str] | str] = {}
        self.confidence_levels: dict[str, float] = {}
        self._registry = registry
        self._max_examples = max_examples

    # TODO think about this to make more abstract instead of * this can be done using CombinedFunctionUnderTest
    # @staticmethod
    # def scaling_invariance_test(function: FunctionUnderTest, inputs: tuple) -> tuple[bool, dict[str, str] | str]:
    #     """Test if function is invariant under scaling"""
    #     a, scale = inputs
    #     try:
    #         r1 = function.call(function.arg_converter(a) * function.arg_converter(scale))
    #         r2 = function.call(a) * function.arg_converter(scale)
    #
    #         if function.compare_results(r1, r2):
    #             return True, f"{function.func.__name__}(k*a) == k*{function.func.__name__}(a)"
    #         else:
    #             return False, {
    #                 f"{function.func.__name__}({scale}*{a})": r1,
    #                 f"{scale}*{function.func.__name__}({a})": f"{r2}"
    #             }
    #     except (TypeError, AttributeError):
    #         return True, "Scaling invariance test skipped (scaling not supported)"

    # TODO think about changing this to more abstract thing instead of +
    # @staticmethod
    # def homomorphism_test(function: FunctionUnderTest, inputs: tuple) -> tuple[bool, dict[str, str] | str]:
    #     """Test if function preserves some operation structure"""
    #     a, b = inputs
    #     try:
    #         # Test if f(a + b) has some relationship to f(a) and f(b)
    #         combined_input = a + b
    #         r1 = function.call(combined_input)
    #         r2 = function.call(a)
    #         r3 = function.call(b)
    #         combined_output = r2 + r3
    #
    #         if function.compare_results(r1, combined_output):
    #             return True, f"{function.func.__name__}(a+b) == {function.func.__name__}(a) + {function.func.__name__}(b)"
    #         else:
    #             return False, {
    #                 f"{function.func.__name__}({a}+{b})": r1,
    #                 f"{function.func.__name__}({a}) + {function.func.__name__}({b})": f"{combined_output}"
    #             }
    #     except (TypeError, AttributeError):
    #         return True, "Homomorphism test skipped (operation not supported)"

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
            function: FunctionUnderTest | CombinedFunctionUnderTest,
            property_test: PropertyTest,
            input_sets: list[Any],
            early_stopping: bool = False
    ) -> tuple[
        dict[str, bool],
        dict[str, list[dict[str, str] | str]],
        dict[str, float],
        dict[str, int]
    ]:
        """
        Test a property for a specific function or function combination.

        Args:
            function: The function or function combination being tested.
            property_test: A property test instance to execute.
            input_sets: A list of input sets to test the properties with.
            early_stopping: Whether to stop testing a property after finding a counter-example.

        Returns:
            A tuple containing:
                - A dictionary of properties and their boolean results.
                - A dictionary of counter-examples for properties that fail.
                - A dictionary of confidence levels for each property.
                - A dictionary of total tests run for each property.
        """

        name = property_test.name
        # Initialize maps with exactly one entry
        properties: dict[str, bool] = {name: True}
        counterexamples: dict[str, list[dict[str, str] | str]] = {name: []}
        confidence: dict[str, int] = {name: 0}
        total_tests: dict[str, int] = {name: 0}

        found_counter_example: bool = False

        for inputs in input_sets:
            # Skip testing if we already found a counter-example and early stopping is enabled
            if early_stopping and found_counter_example:
                break

            if len(inputs) < property_test.input_arity:
                continue

            total_tests[name] += 1
            success, example_data = property_test.test(function, inputs[:property_test.input_arity])

            if success:
                confidence[name] += 1
                # On the first success, record the “example_data” string if no counter yet
                if not found_counter_example:
                    counterexamples[name] = [example_data]
            else:
                # Found a failing case
                properties[name] = False

                if counterexamples[name] and not found_counter_example:
                    counterexamples[name] = [example_data]
                else:
                    if len(counterexamples[name]) < self._max_examples:
                        counterexamples[name].append(example_data)

                found_counter_example = True

        # Compute final confidence fraction
        if total_tests[name] > 0:
            self.confidence_levels[name] = confidence[name] / total_tests[name]
        else:
            self.confidence_levels[name] = 0.0

        return properties, counterexamples, self.confidence_levels, total_tests
