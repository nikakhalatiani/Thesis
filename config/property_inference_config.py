from core.function_under_test import FunctionUnderTest, CombinedFunctionUnderTest
from core.properties import PropertyRegistry
from core.properties.property_test import PropertyTest
from input.input_parser import InputParser
from config.grammar_config import GrammarConfig


class PropertyInferenceConfig:
    """
    Configuration class for property inference.

    Attributes:
        registry: The registry containing property definitions.
        functions_under_test: List of functions to test.
        properties_to_test: List of properties to test.
        default_grammar: Default grammar for input generation.
        default_parser: Default parser for input parsing.
        function_to_grammar: Mapping of function names to grammar.
        function_to_parser: Mapping of function names to parsers.
        combination_to_grammar: Mapping of function combinations to grammar.
        combination_to_parser: Mapping of function combinations to parsers.
        example_count Number of examples to generate for testing.
        early_stopping: Whether to stop testing a property after finding a counter-example.
    """

    def __init__(self, registry: PropertyRegistry, example_count: int = 100) -> None:
        self.registry: PropertyRegistry = registry
        self.functions_under_test: list[FunctionUnderTest] = []
        self.properties_to_test: list[PropertyTest] = []
        self.default_grammar: GrammarConfig | None = None
        self.default_parser: InputParser | None = None
        self.function_to_grammar: dict[str, GrammarConfig] = {}
        self.function_to_parser: dict[str, InputParser] = {}
        self.combination_to_grammar: dict[tuple[str, ...], GrammarConfig] = {}
        self.combination_to_parser: dict[tuple[str, ...], InputParser] = {}
        self.example_count: int = example_count
        self.early_stopping: bool = False
        self.max_counterexamples: int = 1

    def add_function(
            self,
            fut: FunctionUnderTest,
            grammar: GrammarConfig | None = None,
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

    def add_combination(
            self,
            com_fut: CombinedFunctionUnderTest,
            grammar: GrammarConfig | None = None,
            parser: InputParser | None = None,
    ) -> 'PropertyInferenceConfig':
        key = tuple(fut.func.__name__ for fut in com_fut.funcs)

        if grammar:
            self.combination_to_grammar[key] = grammar

        if parser:
            self.combination_to_parser[key] = parser

        return self

    def add_property_by_name(self, property_name: str) -> 'PropertyInferenceConfig':
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
            property_test = self.registry.get_by_name(property_name)
            if property_test not in self.properties_to_test:
                self.properties_to_test.append(property_test)
        except KeyError:
            raise ValueError(f"Property '{property_name}' not found in registry. Please register it first.")
        return self

    def add_property_by_category(self, category: str) -> 'PropertyInferenceConfig':
        """Add all properties from a specific category."""
        category_tests = self.registry.get_by_category(category)
        for test in category_tests:
            if test not in self.properties_to_test:
                self.properties_to_test.append(test)
        return self

    def set_default_grammar(self, spec_path: str,
                            extra_constraints: list[str] | None = None) -> 'PropertyInferenceConfig':
        """
        Set the default grammar file path.

        Args:
            spec_path: The path to the grammar file.
            extra_constraints: Optional list of extra constraints to add to the grammar.

        Returns:
            The updated configuration instance.
        """
        self.default_grammar = GrammarConfig(spec_path, extra_constraints)
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
        Enable or disable early stopping.

        Args:
            early_stopping: Whether to enable early stopping.

        Returns:
            The updated configuration instance.
        """
        self.early_stopping = early_stopping
        return self

    def set_max_counterexamples(self, n: int) -> "PropertyInferenceConfig":
        """How many failing examples to store for each property."""
        self.max_counterexamples = n
        return self
