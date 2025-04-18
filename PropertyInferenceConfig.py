from FunctionUnderTest import FunctionUnderTest
from PropertyDefinition import PropertyDefinition


def commutativity_test(function, inputs):
    a, b = inputs
    result1 = function.call(a, b)
    result2 = function.call(b, a)
    success = function.compare_results(result1, result2)

    if success:
        return True, None
    else:
        return False, {
                f"{function.func.__name__}({a},{b})": result1,
                f"{function.func.__name__}({b},{a})": result2
        }

def associativity_test(function, inputs):
    a, b, c = inputs
    result1 = function.call(a, function.call(b, c))
    result2 = function.call(function.call(a, b), c)
    return function.compare_results(result1, result2)

# Add properties to a registry
property_registry = {
    "Commutativity": PropertyDefinition("Commutativity", commutativity_test, 2),
    "Associativity": PropertyDefinition("Associativity", associativity_test, 3),
}


class PropertyInferenceConfig:
    def __init__(self):
        self.functions_under_test = []
        self.properties_to_test = []
        self.grammar_specs = []
        self.input_parsers = []
        self.example_count = 100
        self.early_stopping = False  # Default: test all inputs


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

    def set_early_stopping(self, early_stopping=True):
        """Configure whether to stop testing a property after finding a counter-example."""
        self.early_stopping = early_stopping
        return self