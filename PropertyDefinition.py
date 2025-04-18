class PropertyDefinition:
    def __init__(self, name, test_function, arity=2):
        self.name = name
        self.test_function = test_function
        self.arity = arity  # Number of arguments the property test needs
