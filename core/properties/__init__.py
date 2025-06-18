from .algebraic import *
from .composition import *
from .behavioral import *
from .structural import *
from core.property_registry import PropertyRegistry


def create_standard_registry() -> PropertyRegistry:
    """Create a registry with all available property tests."""
    registry = PropertyRegistry()

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

    # registry.register(CommutativityTest()) # new instance
    # registry.register(CommutativityTest(2, (1,0))) # new instance
    # registry.register(CommutativityTest(3))  # new instance
    # registry.register(AssociativityTest())  # new instance
    # registry.register(LeftDistributivityTest())
    # registry.register(RightDistributivityTest())
    # registry.register(DistributivityTest())
    # registry.register(LeftIdentityElementTest())
    # registry.register(RightIdentityElementTest())
    # registry.register(LeftAbsorbingElementTest())
    # registry.register(RightAbsorbingElementTest())
    # registry.register(AbsorbingElementTest())
    # registry.register(GeneralAbsorbingElementTest(2,[0,1]))
    # registry.register(IdentityElementTest())
    # registry.register(GeneralIdentityElementTest()) # same as IdentityElementTest
    # registry.register(FixedPointTest())
    # registry.register(FixedPointTest(2,1))
    # registry.register(FixedPointTest(2))
    # registry.register(InjectivityTest())
    # registry.register(InjectivityTest(2))

    # registry.register(LeftCompositionTest())
    # registry.register(RightCompositionTest())
    # registry.register(LeftCompositionTest(2,0))
    # registry.register(RightCompositionTest(2,0))
    # registry.register(InvolutionTest())
    # registry.register(InvolutionTest(2,))
    return registry
