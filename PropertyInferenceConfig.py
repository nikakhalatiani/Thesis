from FunctionUnderTest import FunctionUnderTest
from PropertyDefinition import PropertyDefinition

def commutativity_test2(function, inputs):
    a, b = inputs
    result1 = function.call(a, b)
    result2 = function.call(b, a)
    return function.compare_results(result1, result2)


# Add properties to a registry
property_registry = {
    "commutativity": PropertyDefinition("commutativity", commutativity_test2, 2)    # Add more properties
}

class PropertyDefinition:
    def __init__(self, name, test_function, arity=2):
        self.name = name
        self.test_function = test_function
        self.arity = arity  # Number of arguments the property test needs



class PropertyInferenceConfig:
    def __init__(self):
        self.functions_under_test = []
        self.properties_to_test = []
        self.grammar_specs = []
        self.input_parsers = []
        self.example_count = 100

    def add_function(self, func, arg_converter=None, result_comparator=None):
        fut = FunctionUnderTest(func, arg_converter, result_comparator)
        self.functions_under_test.append(fut)
        return self


    def add_property(self, property_name):
        if property_name in property_registry:
            self.properties_to_test.append(property_registry[property_name])
        return self

    def set_grammar(self, spec_path):
        self.grammar_specs.append(spec_path)
        return self

    def set_parser(self, parser):
        self.input_parsers.append(parser)
        return self