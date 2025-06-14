from .algebraic import *
from .composition import *
from .behavioral import *
from .structural import *
from core.property_registry import PropertyRegistry


def create_standard_registry() -> PropertyRegistry:
    """Create a registry with all available property tests."""
    registry = PropertyRegistry()

    registry.register(CommutativityTest())
    registry.register(AssociativityTest())
    registry.register(IdempotenceTest())
    registry.register(DistributivityTest())
    registry.register(IdentityElementTest())
    registry.register(AbsorbingElementTest())
    registry.register(FixedPointTest())
    registry.register(InjectivityTest())

    registry.register(InvolutionTest())
    registry.register(ScalarHomomorphismTest())
    registry.register(HomomorphismTest())

    registry.register(DeterminismTest())
    registry.register(MonotonicallyIncreasingTest())
    registry.register(MonotonicallyDecreasingTest())

    registry.register(TypePreservationTest())

    return registry


def create_minimal_registry() -> PropertyRegistry:
    """Create a registry with basic properties."""
    registry = PropertyRegistry()
    # registry.register(IdempotenceTest()) # new instance
    registry.register(IdempotenceTest(function_arity=2, result_index=0)) # new instance
    return registry