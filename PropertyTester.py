class PropertyTester:
    def __init__(self, function_under_test):
        self.func = function_under_test
        self.properties = {
            "commutativity": False,
            "associativity": False,
            "idempotence": False,
            "has_identity": False,
            "has_inverses": False,
            # Add more properties as needed
        }
        self.identity_element = None
        self.counter_examples = {}

    def test_commutativity(self, inputs):
        """Test if f(a, b) == f(b, a) for all inputs."""
        a, b = inputs
        result1 = self.func(a, b)
        result2 = self.func(b, a)
        if result1 != result2:
            self.properties["commutativity"] = False
            self.counter_examples["commutativity"] = (a, b, result1, result2)
            return False
        return True

    # Similar methods for other properties

    def infer_properties(self, input_sets):
        """Run all property tests on all input sets."""
        # Initialize all properties as potentially true
        for prop in self.properties:
            self.properties[prop] = True

        # Test each property with each input set
        for inputs in input_sets:
            self.test_commutativity(inputs)
            # Call other property test methods

        return self.properties, self.counter_examples