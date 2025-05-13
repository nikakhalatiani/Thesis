from core.function_under_test import FunctionUnderTest
from config.property_definition import PropertyDefinition
from config.property_registry import PropertyRegistry

from typing import Any

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

    @staticmethod
    def test_property(property_def: PropertyDefinition, function: FunctionUnderTest, input_set: Any) -> tuple[
        bool, dict[str, str] | str]:
        """
        Test a specific property for a function and input set.

        Args:
            property_def: The property definition to test.
            function: The function being tested.
            input_set: The set of inputs to test the property with.

        Returns:
            A tuple containing a boolean indicating success and
            a dictionary of counter-example data if the test fails.
        """
        result = property_def.test_function(function, input_set)
        return result

    @staticmethod
    def commutativity_test(function: FunctionUnderTest, inputs: tuple) -> tuple[bool, dict[str, str] | str]:
        a, b = inputs
        r1, r2 = function.call(a, b), function.call(b, a)
        if function.compare_results(r1, r2):
            return True, f"{function.func.__name__}(a,b) == {function.func.__name__}(b,a)"
        else:
            return False, {
                f"{function.func.__name__}({a},{b})": r1,
                f"{function.func.__name__}({b},{a})": f"{r2}\n"
            }

    @staticmethod
    def associativity_test(function: FunctionUnderTest, inputs: tuple) -> tuple[bool, dict[str, str] | str]:
        a, b, c = inputs
        r1, r2 = function.call(a, function.call(b, c)), function.call(function.call(a, b), c)

        if function.compare_results(r1, r2):
            return True, (f"{function.func.__name__}(a,{function.func.__name__}(b,c)) "
                          f"== {function.func.__name__}({function.func.__name__}(a,b),c)")
        else:
            return False, {
                f"{function.func.__name__}({a},{function.func.__name__}({b},{c}))": r1,
                f"{function.func.__name__}({function.func.__name__}({a},{b}),{c})": f"{r2}\n"
            }

    @staticmethod
    def left_idempotence_test(function: FunctionUnderTest, inputs: tuple) -> tuple[bool, dict[str, str] | str]:
        a, b = inputs
        r1 = function.call(a, b)
        r2 = function.call(a, r1)
        if function.compare_results(r1, r2):
            return True, f"{function.func.__name__}(a,b) == {function.func.__name__}(a,{function.func.__name__}(a,b))"
        else:
            return False, {
                f"{function.func.__name__}({a},{b})": r1,
                f"{function.func.__name__}({a},{function.func.__name__}({a},{b}))": f"{r2}\n",
            }

    @staticmethod
    def right_idempotence_test(function: FunctionUnderTest, inputs: tuple) -> tuple[bool, dict[str, str] | str]:
        a, b = inputs
        r1 = function.call(a, b)
        r2 = function.call(r1, a)
        if function.compare_results(r1, r2):
            return True, f"{function.func.__name__}(a,b) == {function.func.__name__}({function.func.__name__}(a,b),a)"
        else:
            return False, {
                f"{function.func.__name__}({a},{b})": r1,
                f"{function.func.__name__}({function.func.__name__}({a},{b}),{b})": f"{r2}\n",
            }

    @staticmethod
    def full_idempotence_test(function: FunctionUnderTest, inputs: tuple) -> tuple[bool, dict[str, str] | str]:
        a, b = inputs
        r1 = function.call(a, b)
        r2 = function.call(r1, r1)
        if function.compare_results(r1, r2):
            return True, f"{function.func.__name__}(a,b) == {function.func.__name__}({function.func.__name__}(a,b),{function.func.__name__}(a,b))"
        else:
            return False, {
                f"{function.func.__name__}({a},{b})": r1,
                f"{function.func.__name__}({function.func.__name__}({a},{b}),{function.func.__name__}({a},{b}))": f"{r2}\n",
            }

    @staticmethod
    def idempotence_test(function: FunctionUnderTest, inputs: tuple) -> tuple[bool, dict[str, str] | str]:
        a = inputs[0]
        r1 = function.call(a)
        r2 = function.call(r1)
        if function.compare_results(r1, r2):
            return True, f"{function.func.__name__}(a) == {function.func.__name__}({function.func.__name__}(a))"
        else:
            return False, {
                f"{function.func.__name__}({a})": r1,
                f"{function.func.__name__}({function.func.__name__}({a}))": f"{r2}\n",
            }

    def infer_properties(self, function: FunctionUnderTest, property_defs: list[PropertyDefinition],
                         input_sets: list[Any], early_stopping: bool = False) -> tuple[
        dict[str, bool], dict[str, list[dict[str, str] | str]], dict[str, float], dict[str, int]]:
        """
        Infer properties for a specific function.

        Args:
            function: The function being tested.
            property_defs: A list of property definitions to test.
            input_sets: A list of input sets to test the properties with.
            early_stopping: Whether to stop testing a property after finding a counter-example.

        Returns:
            A tuple containing:
                - A dictionary of properties and their boolean results.
                - A dictionary of counter-examples for properties that fail.
                - A dictionary of confidence levels for each property.
        """
        if not property_defs:
            property_defs = list(self._registry.get_all.values())

        properties: dict[str, bool] = {prop.name: True for prop in property_defs}
        counter_examples: dict[str, list[dict[str, str] | str]] = {prop.name: [] for prop in property_defs}
        confidence: dict[str, int] = {prop.name: 0 for prop in property_defs}
        total_tests: dict[str, int] = {prop.name: 0 for prop in property_defs}

        # Test each property with appropriate input sets
        for prop in property_defs:
            found_counter_example: bool = False
            for inputs in input_sets:
                # Skip testing if we already found a counter-example and early stopping is enabled
                if early_stopping and found_counter_example:
                    break
                if len(inputs) < prop.arity:  # Check if we have enough inputs for testing the property
                    continue
                total_tests[prop.name] += 1

                # Get test result and counter-example data if it fails
                success, example_data = self.test_property(prop, function, inputs[:prop.arity])

                if success:
                    confidence[prop.name] += 1
                    if not found_counter_example:
                        assert isinstance(example_data, str), (
                            f"Expected success example to be str, got {type(example_data)}"
                        )
                        counter_examples[prop.name] = [example_data]
                else:
                    properties[prop.name] = False
                    found_counter_example = True
                    assert isinstance(example_data, dict), (
                        f"Expected failure example to be dict, got {type(example_data)}"
                    )
                    lst = counter_examples[prop.name]
                    # if we already have a dict‐based list, append up to the max
                    if lst and isinstance(lst[0], dict):
                        if len(lst) < self._max_examples:
                            lst.append(example_data)
                    else:
                        # either we had an empty list, or a success‐string,
                        # so overwrite with a new failure‐list
                        counter_examples[prop.name] = [example_data]

        # Calculate confidence levels
        for prop in property_defs:
            if total_tests[prop.name] > 0:
                self.confidence_levels[prop.name] = confidence[prop.name] / total_tests[prop.name]

        return properties, counter_examples, self.confidence_levels, total_tests
