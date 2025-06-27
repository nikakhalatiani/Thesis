from typing import TypedDict
from abc import ABC, ABCMeta, abstractmethod

from core.function_under_test import CombinedFunctionUnderTest


class TestStats(TypedDict):
    total_count: int
    success_count: int


class TestResult(TypedDict):
    holds: bool
    counterexamples: list[str]
    successes: list[str]
    stats: TestStats


class MultitonMeta(ABCMeta):
    """
    Metaclass that implements the Multiton pattern.
    Creates one instance per unique combination of class and constructor arguments.
    Inherits from ABCMeta to work with abstract base classes.
    """
    _instances = {}

    def __call__(cls, *args, **kwargs):
        # Create a key from class and all constructor arguments
        # Convert mutable types to immutable for hashing
        def make_hashable(item):
            if isinstance(item, dict):
                return tuple(sorted(item.items()))
            elif isinstance(item, list):
                return tuple(item)
            elif isinstance(item, set):
                return frozenset(item)
            return item

        hashable_args = tuple(make_hashable(arg) for arg in args)
        hashable_kwargs = tuple(sorted((k, make_hashable(v)) for k, v in kwargs.items()))

        key = (cls, hashable_args, hashable_kwargs)

        if key not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[key] = instance

        return cls._instances[key]

    @classmethod
    def clear_instances(cls):
        """Clear all cached instances - useful for testing"""
        cls._instances.clear()


class PropertyTest(ABC, metaclass=MultitonMeta):
    """Abstract base class for all property tests with Multiton pattern."""

    def __init__(self, name: str, input_arity: int, function_arity: int,
                 description: str = "", category: str = ""):
        self.name = name
        self.input_arity = input_arity
        self.function_arity = function_arity
        self.description = description
        self.category = category
        self.num_functions = 1
        self.swap_indices = None
        self.result_index = None
        self.distribute_over_index = None
        self.identity_positions = None

    @abstractmethod
    def test(self, candidate: CombinedFunctionUnderTest, inputs: list[tuple], max_counterexamples) -> TestResult:
        """Execute the property test."""
        pass

    def is_applicable(self, candidate: CombinedFunctionUnderTest) -> bool:
        """Check if this property test is applicable to the given function."""
        import inspect
        if self.num_functions != len(candidate.funcs):
            return False
        # Ensure each inner function has the right arity
        return all(len(inspect.signature(fut.func).parameters) == self.function_arity for fut in candidate.funcs)

    def __str__(self) -> str:
        """String representation of the property test."""
        parts = [f"{self.name} (arity: {self.input_arity}/{self.function_arity})"]

        optional_attributes = {
            "swap": self.swap_indices,
            "result_index": self.result_index,
            "distribute_over_index": self.distribute_over_index,
            "identity_positions": self.identity_positions,
        }

        for key, value in optional_attributes.items():
            if value is not None:
                parts.append(f"{key}: {value}")

        return ", ".join(parts)
