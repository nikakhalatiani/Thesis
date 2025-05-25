from typing import Any

from core.properties import PropertyRegistry
from core.function_under_test import FunctionUnderTest
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
        self.properties: dict[str, bool] = {}
        self.examples: dict[str, dict[str, str] | str] = {}
        self.confidence_levels: dict[str, float] = {}
        self._registry = registry
        self._max_examples = max_examples


    # ============================================================================
    # INVARIANCE PROPERTIES - Function behavior under transformations
    # ============================================================================

    # TODO think about this to fix logic of getting inputs that are not monotonic
    # @staticmethod
    # def monotonically_increasing_test(function: FunctionUnderTest, inputs: tuple) -> tuple[bool, dict[str, str] | str]:
    #     """Test if function is monotonically increasing (preserves order relationships)"""
    #     a, b = inputs
    #     try:
    #         if function.arg_converter(a) <= function.arg_converter(b):
    #             r1, r2 = function.call(a), function.call(b)
    #             if r1 <= r2:
    #                 return True, f"a ≤ b ⟹ {function.func.__name__}(a) ≤ {function.func.__name__}(b)"
    #             else:
    #                 return False, {
    #                     f"Input: {a} ≤ {b}": "True",
    #                     f"{function.func.__name__}({a})": r1,
    #                     f"{function.func.__name__}({b})": r2,
    #                     f"Output: {r1} ≤ {r2}": "False"
    #                 }
    #         else:
    #             return True, "Increasing monotonicity test skipped (inputs not monotonically increasing)"
    #     except (TypeError, AttributeError):
    #         return True, "Increasing monotonicity test skipped (inputs not comparable)"
    #
    # @staticmethod
    # def monotonically_decreasing_test(function: FunctionUnderTest, inputs: tuple) -> tuple[bool, dict[str, str] | str]:
    #     """Test if function is monotonically decreasing (preserves order relationships)"""
    #     a, b = inputs
    #     try:
    #         if function.arg_converter(a) >= function.arg_converter(b):
    #             r1, r2 = function.call(a), function.call(b)
    #             if r1 >= r2:
    #                 return True, f"a ≥ b ⟹ {function.func.__name__}(a) ≥ {function.func.__name__}(b)"
    #             else:
    #                 return False, {
    #                     f"Input: {a} ≥ {b}": "True",
    #                     f"{function.func.__name__}({a})": r1,
    #                     f"{function.func.__name__}({b})": r2,
    #                     f"Output: {r1} ≥ {r2}": "False"
    #                 }
    #         else:
    #             return True, "Decreasing monotonicity test skipped (inputs not monotonically decreasing)"
    #     except (TypeError, AttributeError):
    #         return True, "Decreasing monotonicity test skipped (inputs not comparable)"

    # TODO think about this to make more abstract instead of *
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
    # COMPOSITION PROPERTIES - How functions interact with themselves
    # ============================================================================


    # TODO think about this to make more abstract by changing + to a function
    # TODO this requires support for multiple functions under test
    # @staticmethod
    # def distributivity_test(function: FunctionUnderTest, inputs: tuple) -> tuple[bool, dict[str, str] | str]:
    #     """Test if f(a, b+c) = f(a,b) + f(a,c) or similar distributive property"""
    #     a, b, c = inputs
    #     a, b, c = function.arg_converter(a), function.arg_converter(b), function.arg_converter(c)
    #     try:
    #         # Test left distributivity: f(a, b+c) ?= f(a,b) + f(a,c)
    #         combined = b + c
    #         r1 = function.call(a, combined)
    #         r2 = function.call(a, b) + function.call(a, c)
    #
    #         if function.compare_results(r1, r2):
    #             return True, f"{function.func.__name__}(a, b+c) = {function.func.__name__}(a,b) + {function.func.__name__}(a,c)"
    #         else:
    #             return False, {
    #                 f"{function.func.__name__}({a}, {b}+{c})": r1,
    #                 f"{function.func.__name__}({a},{b}) + {function.func.__name__}({a},{c})": r2
    #             }
    #     except (TypeError, AttributeError):
    #         return True, "Distributivity test skipped (operations not supported)"

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



    def infer_properties(self, function: FunctionUnderTest, property_tests: list[PropertyTest],
                         input_sets: list[Any], early_stopping: bool = False) -> tuple[
        dict[str, bool], dict[str, list[dict[str, str] | str]], dict[str, float], dict[str, int]]:
        """
        Infer properties for a specific function.

        Args:
            function: The function being tested.
            property_tests: A list of property test instances to execute.
            input_sets: A list of input sets to test the properties with.
            early_stopping: Whether to stop testing a property after finding a counter-example.

        Returns:
            A tuple containing:
                - A dictionary of properties and their boolean results.
                - A dictionary of counter-examples for properties that fail.
                - A dictionary of confidence levels for each property.
                - A dictionary of total tests run for each property.
        """

        properties: dict[str, bool] = {prop.name: True for prop in property_tests}
        counterexamples: dict[str, list[dict[str, str] | str]] = {prop.name: [] for prop in property_tests}
        confidence: dict[str, int] = {prop.name: 0 for prop in property_tests}
        total_tests: dict[str, int] = {prop.name: 0 for prop in property_tests}

        # Test each applicable property with appropriate input sets
        for prop in property_tests:
            found_counter_example: bool = False
            for inputs in input_sets:
                # Skip testing if we already found a counter-example and early stopping is enabled
                if early_stopping and found_counter_example:
                    break
                if len(inputs) < prop.input_arity:
                    continue
                total_tests[prop.name] += 1

                # Get test result and counter-example data if it fails
                success, example_data = prop.test(function, inputs[:prop.input_arity])

                if success:
                    confidence[prop.name] += 1
                    if not found_counter_example:
                        assert isinstance(example_data, str), (
                            f"Expected success example to be str, got {type(example_data)}"
                        )
                        counterexamples[prop.name] = [example_data]
                else:
                    properties[prop.name] = False
                    found_counter_example = True
                    assert isinstance(example_data, dict), (
                        f"Expected failure example to be dict, got {type(example_data)}"
                    )
                    lst = counterexamples[prop.name]
                    # if we already have a dict‐based list, append up to the max
                    if lst and isinstance(lst[0], dict):
                        if len(lst) < self._max_examples:
                            lst.append(example_data)
                    else:
                        # either we had an empty list, or a success‐string,
                        # so overwrite with a new failure‐list
                        counterexamples[prop.name] = [example_data]

        # Calculate confidence levels
        for prop in property_tests:
            if total_tests[prop.name] > 0:
                self.confidence_levels[prop.name] = confidence[prop.name] / total_tests[prop.name]
            else:
                self.confidence_levels[prop.name] = 0.0

        return properties, counterexamples, self.confidence_levels, total_tests
