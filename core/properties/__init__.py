from .algebraic import *
from .composition import *
from .information import DeterminismTest
from .structural import TypePreservationTest
from .property_test import PropertyRegistry


def create_standard_registry() -> PropertyRegistry:
    """Create a registry with all available property tests."""
    registry = PropertyRegistry()

    # Algebraic properties
    registry.register(CommutativityTest())
    registry.register(AssociativityTest())
    registry.register(IdempotenceTest())
    registry.register(DistributivityTest())

    # Behavioral properties
    registry.register(DeterminismTest())

    # Structural properties
    registry.register(TypePreservationTest())

    # Composition properties
    registry.register(InvolutionTest())

    return registry


def create_minimal_registry() -> PropertyRegistry:
    """Create a registry with basic properties."""
    registry = PropertyRegistry()
    registry.register(CommutativityTest())
    registry.register(AssociativityTest())
    registry.register(IdempotenceTest())
    registry.register(DistributivityTest())
    # registry.register(RightIdempotenceTest())
    # registry.register(LeftIdempotenceTest())
    # registry.register(FullIdempotenceTest())

    # registry.register(InvolutionTest())
    # registry.register(MonotonicallyDecreasingTest())
    # registry.register(MonotonicallyIncreasingTest())

    return registry
