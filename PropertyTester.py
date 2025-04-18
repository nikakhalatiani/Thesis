class PropertyTester:
    def __init__(self):
        self.properties = {}
        self.counter_examples = {}
        self.confidence_levels = {}

    @staticmethod
    def test_property(property_def, function, input_set):
        """Test a specific property for a function and input set."""
        result = property_def.test_function(function, input_set)
        return result

    def infer_properties(self, function, property_defs, input_sets, early_stopping=False):
        """Infer properties for a specific function."""
        # Initialize properties
        properties = {prop.name: True for prop in property_defs}
        counter_examples = {}
        confidence = {prop.name: 0 for prop in property_defs}
        total_tests = {prop.name: 0 for prop in property_defs}

        # Test each property with appropriate input sets
        for prop in property_defs:
            found_counter_example = False

            for inputs in input_sets:
                # Skip testing if we already found a counter-example and early stopping is enabled
                if early_stopping and found_counter_example:
                    break

                if len(inputs) >= prop.arity:  # Check if we have enough inputs
                    total_tests[prop.name] += 1
                    inputs_for_test = inputs[:prop.arity]

                    # Get test result and counter-example data if it fails
                    success, counter_example_data = self.test_property(prop, function, inputs_for_test)

                    if success:
                        confidence[prop.name] += 1
                    else:
                        properties[prop.name] = False
                        found_counter_example = True
                        # Store the first counter-example we find
                        if prop.name not in counter_examples:
                            counter_examples[prop.name] = counter_example_data

        # Calculate confidence levels
        for prop in property_defs:
            if total_tests[prop.name] > 0:
                self.confidence_levels[prop.name] = confidence[prop.name] / total_tests[prop.name]

        return properties, counter_examples, self.confidence_levels