class PropertyTester:
    def __init__(self):
        self.properties = {}
        self.counter_examples = {}
        self.confidence_levels = {}

    def test_property(self, property_def, function, input_set):
        """Test a specific property for a function and input set."""
        result = property_def.test_function(function, input_set)
        return result

    def infer_properties(self, function, property_defs, input_sets):
        """Infer properties for a specific function."""
        # Initialize properties
        properties = {prop.name: True for prop in property_defs}
        counter_examples = {}
        confidence = {prop.name: 0 for prop in property_defs}
        total_tests = {prop.name: 0 for prop in property_defs}

        # Test each property with appropriate input sets
        for prop in property_defs:
            for inputs in input_sets:
                print(f"Testing property {prop.name} with inputs: {inputs}")
                if len(inputs) >= prop.arity:  # Check if we have enough inputs
                    total_tests[prop.name] += 1
                    if self.test_property(prop, function, inputs[:prop.arity]):
                        confidence[prop.name] += 1
                    else:
                        properties[prop.name] = False
                        if prop.name not in counter_examples:
                            counter_examples[prop.name] = (inputs[:prop.arity],
                                                           function.call(*inputs[:prop.arity]),
                                                           function.call(*reversed(inputs[:prop.arity])))
                # else:
                #     # Not enough inputs for this property
                #     raise(ValueError(f"Not enough inputs for property {prop.name}. Expected {prop.arity}, got {len(inputs)}."))

        # Calculate confidence levels
        for prop in property_defs:
            if total_tests[prop.name] > 0:
                self.confidence_levels[prop.name] = confidence[prop.name] / total_tests[prop.name]

        return properties, counter_examples, self.confidence_levels