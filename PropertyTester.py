from FunctionUnderTest import FunctionUnderTest
from PropertyDefinition import PropertyDefinition

from typing import Any


class PropertyTester:
    """
    A class to test and infer properties of functions under test.

    Attributes:
        properties: Stores the inferred properties and their boolean results.
        counter_examples: Stores counter-examples for properties that fail.
        confidence_levels: Stores confidence levels for each property.
    """

    def __init__(self) -> None:
        self.properties: dict[str, bool] = {}
        self.counter_examples: dict[str, dict[str, str] | None] = {}
        self.confidence_levels: dict[str, float] = {}

    @staticmethod
    def test_property(property_def: PropertyDefinition, function: FunctionUnderTest, input_set: Any) -> tuple[
        bool, dict[str, str] | None]:
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
        result: tuple[bool, dict[str, str] | None] = property_def.test_function(function, input_set)
        return result

    def infer_properties(self, function: FunctionUnderTest, property_defs: list[PropertyDefinition],
                         input_sets: list[Any], early_stopping: bool = False) -> tuple[
        dict[str, bool], dict[str, dict[str, str] | None], dict[str, float]]:
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
        properties: dict[str, bool] = {prop.name: True for prop in property_defs}
        counter_examples: dict[str, dict[str, str] | None] = {}
        confidence: dict[str, int] = {prop.name: 0 for prop in property_defs}
        total_tests: dict[str, int] = {prop.name: 0 for prop in property_defs}

        # Test each property with appropriate input sets
        for prop in property_defs:
            found_counter_example: bool = False
            for inputs in input_sets:
                # Skip testing if we already found a counter-example and early stopping is enabled
                if early_stopping and found_counter_example:
                    break
                if len(inputs) >= prop.arity:  # Check if we have enough inputs for testing the property
                    total_tests[prop.name] += 1
                    inputs_for_test = inputs[:prop.arity]

                    # Get test result and counter-example data if it fails
                    success: bool
                    counter_example_data: dict[str, str] | None
                    success, counter_example_data = self.test_property(prop, function, inputs_for_test)

                    if success:
                        confidence[prop.name] += 1
                    else:
                        properties[prop.name] = False
                        found_counter_example = True
                        # Store the first counter-example we find
                        if prop.name not in counter_examples:
                            counter_examples[prop.name] = counter_example_data
                            assert isinstance(counter_examples[prop.name], dict), "Failed to store counter-example data"

        # Calculate confidence levels
        for prop in property_defs:
            if total_tests[prop.name] > 0:
                self.confidence_levels[prop.name] = confidence[prop.name] / total_tests[prop.name]

        return properties, counter_examples, self.confidence_levels
