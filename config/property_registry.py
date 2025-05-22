from config.property_definition import PropertyDefinition
from core.function_under_test import FunctionUnderTest

from collections.abc import Callable
from typing import Any


class PropertyRegistry:
    """
    A registry for managing property definitions.
    """

    def __init__(self) -> None:
        self._properties: dict[str, PropertyDefinition] = {}

    def register(self, name: str,
                 test_function: Callable[[FunctionUnderTest, Any], tuple[bool, dict[str, str] | str]],
                 input_arity: int,
                 function_arity: int) -> 'PropertyRegistry':
        """
        Register a new property with the registry.

        Args:
            name: The name of the property
            test_function: The function implementing the property test
            input_arity: The number of inputs required for testing
            function_arity: The number of arguments the function must accept

        Returns:
            The updated registry instance
        """
        assert name not in self._properties, "Property already registered"
        assert input_arity >= 0, "Arity must be non-negative"
        self._properties[name] = PropertyDefinition(name, test_function, input_arity, function_arity)

        return self

    def get(self, name: str) -> PropertyDefinition:
        """
        Retrieve a property definition by name.

        Args:
            name: The name of the property to retrieve

        Returns:
            The PropertyDefinition object

        Raises:
            KeyError: If the property is not registered
        """
        if name not in self._properties:
            raise KeyError(f"Property '{name}' not found in registry")
        return self._properties[name]

    @property
    def get_all(self) -> dict[str, PropertyDefinition]:
        """
        Get all registered properties.

        Returns:
            Dictionary mapping property names to their definitions
        """
        return self._properties.copy()

    def list_names(self) -> list[str]:
        """
        List all registered property names.

        Returns:
            List of property names
        """
        return list(self._properties.keys())
