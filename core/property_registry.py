from core.function_under_test import CombinedFunctionUnderTest
from core.properties.property_test import PropertyTest


class PropertyRegistry:
    """Registry for managing property tests, organized by categories."""

    def __init__(self):
        self._tests: dict[str, PropertyTest] = {}
        self._categories: dict[str, list[PropertyTest]] = {}

    def register(self, test: PropertyTest) -> 'PropertyRegistry':
        """Register a property test."""
        if test.name in self._tests:
            raise ValueError(f"Property test '{test.name}' already registered")

        self._tests[test.name] = test

        # Organize by category
        category = test.category or "Uncategorized"
        if category not in self._categories:
            # Register a new category if it doesn't exist
            self._categories[category] = []
        self._categories[category].append(test)

        return self

    def get_by_name(self, name: str) -> PropertyTest:
        """Get a specific property test by name."""
        if name not in self._tests:
            raise KeyError(f"Property test '{name}' not found")
        return self._tests[name]

    def get_by_category(self, category: str) -> list[PropertyTest]:
        """Get all property tests in a category."""
        return self._categories.get(category, [])

    def get_applicable_tests(self, candidate: CombinedFunctionUnderTest) -> list[PropertyTest]:
        """Get all tests applicable to the given function."""
        return [test for test in self._tests.values() if test.is_applicable(candidate)]

    def list_categories(self) -> list[str]:
        """List all available categories."""
        return list(self._categories.keys())

    def get_all(self) -> dict[str, PropertyTest]:
        """Get all registered tests."""
        return self._tests.copy()
