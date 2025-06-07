from .algebraic import *
from .composition import *
from .behavioral import DeterminismTest
from .structural import *
from core.property_registry import PropertyRegistry


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
    registry.register(MonotonicallyIncreasingTest())
    registry.register(MonotonicallyDecreasingTest())

    return registry


def create_minimal_registry() -> PropertyRegistry:
    """Create a registry with basic properties."""
    registry = PropertyRegistry()
    # registry.register(CommutativityTest())
    # registry.register(AssociativityTest())
    # registry.register(IdempotenceTest())
    registry.register(DistributivityTest())
    # registry.register(IdentityElementTest())
    # registry.register(AbsorbingElementTest())
    # registry.register(FixedPointTest())
    #
    # registry.register(InvolutionTest())
    # registry.register(ScalarHomomorphismTest())
    # registry.register(HomomorphismTest())
    #
    # registry.register(DeterminismTest())
    #
    # registry.register(TypePreservationTest())
    # registry.register(MonotonicallyIncreasingTest())
    # registry.register(MonotonicallyDecreasingTest())

    return registry
