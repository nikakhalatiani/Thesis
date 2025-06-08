from typing import TypedDict
from abc import ABC, abstractmethod

from core.function_under_test import CombinedFunctionUnderTest


class TestStats(TypedDict):
    total_count: int
    success_count: int


class TestResult(TypedDict):
    holds: bool
    counterexamples: list[str]
    stats: TestStats


class PropertyTest(ABC):
    """Abstract base class for all property tests."""

    def __init__(self, name: str, input_arity: int, function_arity: int,
                 description: str = "", category: str = ""):
        self.name = name
        self.input_arity = input_arity
        self.function_arity = function_arity
        self.description = description
        self.category = category
        self.num_functions: int = 1  # default: single-function properties

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
        return f"{self.name} (arity: {self.input_arity}/{self.function_arity})"