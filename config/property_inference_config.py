from core.function_under_test import FunctionUnderTest, ComparisonStrategy
from core.properties import PropertyRegistry
from input.input_parser import InputParser
from config.grammar_config import GrammarConfig
from core.properties.property_test import PropertyTest


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
        example_count: Number of examples to generate for testing.
        use_input_cache: Whether to reuse generated inputs across properties.
    """

    def __init__(self, registry: PropertyRegistry) -> None:
        self.registry: PropertyRegistry = registry
        self.functions_under_test: list[FunctionUnderTest] = []
        self.properties_to_test: list[PropertyTest] = []
        self.default_grammar: GrammarConfig | None = None
        self.default_parser: InputParser | None = None
        self.function_to_grammar: dict[str, GrammarConfig] = {}
        self.function_to_parser: dict[str, InputParser] = {}
        self.example_count: int = 100
        self.max_counterexamples: int = 100
        self.comparison_strategy = ComparisonStrategy.CONSENSUS
        self.use_input_cache = True
        self.max_feedback_attempts: int = 3
        self.feedback_enabled = False

    def add_function(
            self,
            fut: FunctionUnderTest,
            grammar: GrammarConfig | None = None,
            parser: InputParser | None = None,
    ) -> "PropertyInferenceConfig":
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

    def add_property_by_name(self, property_name: str) -> "PropertyInferenceConfig":
        """
        Add a property to the list of properties to test.
        A single property name can map to multiple test variants in the
        registry. All variants will be added.

        Args:
            property_name: The name of the property to test.

        Returns:
            The updated configuration instance.

        Raises:
            ValueError: If the property is not found in the registry.
        """
        try:
            property_tests = self.registry.get_by_name(property_name)
            for property_test in property_tests:
                if property_test not in self.properties_to_test:
                    self.properties_to_test.append(property_test)
        except KeyError:
            raise ValueError(f"Property '{property_name}' not found in registry. Please register it first.")
        return self

    def add_property_by_category(self, category: str) -> "PropertyInferenceConfig":
        """Add all properties from a specific category."""
        category_tests = self.registry.get_by_category(category)
        for test in category_tests:
            if test not in self.properties_to_test:
                self.properties_to_test.append(test)
        return self

    def set_default_grammar(self, spec_path: str,
                            extra_constraints: list[str] | None = None) -> "PropertyInferenceConfig":
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

    def set_default_parser(self, parser: InputParser) -> "PropertyInferenceConfig":
        """
        Set the default parser.

        Args:
            parser: The parser to use.

        Returns:
            The updated configuration instance.
        """
        self.default_parser = parser
        return self

    def set_max_counterexamples(self, n: int) -> "PropertyInferenceConfig":
        """How many failing examples to store for each property."""
        self.max_counterexamples = n
        return self

    def set_max_feedback_attempts(self, n: int) -> "PropertyInferenceConfig":
        """Set maximum attempts in feedback loop."""
        if n < 1:
            raise ValueError("Maximum feedback attempts must be at least 1.")
        self.max_feedback_attempts = n
        return self

    def set_feedback_enabled(self, enabled: bool) -> "PropertyInferenceConfig":
        """Control whether the adaptive feedback loop is used."""
        self.feedback_enabled = enabled
        return self

    def set_comparison_strategy(self, strategy: ComparisonStrategy) -> "PropertyInferenceConfig":
        """Set the comparison strategy for combined functions."""
        self.comparison_strategy = strategy
        return self

    def set_use_input_cache(self, enabled: bool) -> "PropertyInferenceConfig":
        """Enable or disable caching of generated input sets."""
        self.use_input_cache = enabled
        return self

    def set_example_count(self, count: int) -> "PropertyInferenceConfig":
        """Set the number of examples to generate for testing."""
        self.example_count = count
        return self
