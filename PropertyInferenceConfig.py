from FunctionUnderTest import FunctionUnderTest
from PropertyDefinition import PropertyDefinition
from InputParser import InputParser
from PropertyRegistry import PropertyRegistry


class PropertyInferenceConfig:
    """
    Configuration class for property inference.

    Attributes:
        registry: The registry containing property definitions.
        functions_under_test: List of functions to test.
        properties_to_test: List of properties to test.
        default_grammar: Default grammar file path for input generation.
        default_parser: Default parser for input parsing.
        function_to_grammar: Mapping of function names to grammar file paths.
        function_to_parser: Mapping of function names to parsers.
        example_count Number of examples to generate for testing.
        early_stopping: Whether to stop testing a property after finding a counter-example.
    """

    def __init__(self, registry: PropertyRegistry, example_count: int = 100) -> None:
        self.registry: PropertyRegistry = registry
        self.functions_under_test: list[FunctionUnderTest] = []
        self.properties_to_test: list[PropertyDefinition] = []
        self.default_grammar: str | None = None
        self.default_parser: InputParser | None = None
        self.function_to_grammar: dict[str, str] = {}
        self.function_to_parser: dict[str, InputParser] = {}
        self.example_count: int = example_count
        self.early_stopping: bool = False

    def add_function(
            self,
            fut: FunctionUnderTest,
            grammar: str | None = None,
            parser: InputParser | None = None,
    ) -> 'PropertyInferenceConfig':
        """
        Add a function to the list of functions under test.

        Args:
            fut: The function to test.
            grammar: Optional grammar file path for the function.
            parser: Optional parser for the function.

        Returns:
            The updated configuration instance.
        """
        self.functions_under_test.append(fut)
        if grammar:
            self.function_to_grammar[fut.func.__name__] = grammar
        if parser:
            self.function_to_parser[fut.func.__name__] = parser
        return self

    def add_property(self, property_name: str) -> 'PropertyInferenceConfig':
        """
        Add a property to the list of properties to test.

        Args:
            property_name: The name of the property to test.

        Returns:
            The updated configuration instance.

        Raises:
            ValueError: If the property is not found in the registry.
        """
        try:
            property_def: PropertyDefinition = self.registry.get(property_name)
            self.properties_to_test.append(property_def)
        except KeyError:
            raise ValueError(f"Property '{property_name}' not found in registry. Please register it first.")
        return self

    def set_default_grammar(self, spec_path: str) -> 'PropertyInferenceConfig':
        """
        Set the default grammar file path.

        Args:
            spec_path: The path to the grammar file.

        Returns:
            The updated configuration instance.
        """
        self.default_grammar = spec_path
        return self

    def set_default_parser(self, parser: InputParser) -> 'PropertyInferenceConfig':
        """
        Set the default parser.

        Args:
            parser: The parser to use.

        Returns:
            The updated configuration instance.
        """
        self.default_parser = parser
        return self

    def set_early_stopping(self, early_stopping: bool = True) -> 'PropertyInferenceConfig':
        """
        Enable or disable early stopping .

        Args:
            early_stopping: Whether to enable early stopping.

        Returns:
            The updated configuration instance.
        """
        self.early_stopping = early_stopping
        return self