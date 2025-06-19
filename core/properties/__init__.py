from .algebraic import *
from .composition import *
from .behavioral import *
from .structural import *
from core.property_registry import PropertyRegistry


def create_symmetry_registry() -> PropertyRegistry:
    """Registry for testing argument order and position relationships."""
    registry = PropertyRegistry()

    # Basic commutativity for binary functions
    registry.register(CommutativityTest())  # f(a,b) == f(b,a)
    registry.register(CommutativityTest(2, (1, 0)))  # explicit (1,0) swap

    # Commutativity for higher arity functions
    registry.register(CommutativityTest(3))  # f(a,b,c) == f(b,a,c) - swaps first two
    registry.register(CommutativityTest(3, (0, 2)))  # f(a,b,c) == f(c,b,a) - swaps first and last
    registry.register(CommutativityTest(3, (1, 2)))  # f(a,b,c) == f(a,c,b) - swaps last two
    registry.register(CommutativityTest(4, (0, 3)))  # 4-ary function, swap first and last

    return registry


def create_algebraic_structure_registry() -> PropertyRegistry:
    """Registry for fundamental algebraic laws and structural properties."""
    registry = PropertyRegistry()

    # Associativity - fundamental for groups, monoids
    registry.register(AssociativityTest())

    # Distributivity - fundamental for rings, fields
    registry.register(LeftDistributivityTest())
    registry.register(RightDistributivityTest())
    registry.register(DistributivityTest())  # both left and right

    return registry


def create_special_elements_registry() -> PropertyRegistry:
    """Registry for testing identity and absorbing elements."""
    registry = PropertyRegistry()

    # Identity elements - neutral elements in operations
    registry.register(LeftIdentityElementTest())  # f(e, a) == a
    registry.register(RightIdentityElementTest())  # f(a, e) == a
    registry.register(IdentityElementTest())  # two-sided identity
    registry.register(GeneralIdentityElementTest())  # same as IdentityElementTest for arity 2

    # Identity for higher arity functions
    registry.register(LeftIdentityElementTest(3, 0, 1))  # f(e, a, b) == a
    registry.register(LeftIdentityElementTest(3, 0, 2))  # f(e, a, b) == b
    registry.register(RightIdentityElementTest(3, 2, 0))  # f(a, b, e) == a
    registry.register(GeneralIdentityElementTest(3))  # tests all positions

    # Absorbing elements - dominating elements
    registry.register(LeftAbsorbingElementTest())  # f(z, a) == z
    registry.register(RightAbsorbingElementTest())  # f(a, z) == z
    registry.register(AbsorbingElementTest())  # two-sided absorbing
    registry.register(GeneralAbsorbingElementTest(2, [0, 1]))  # same as AbsorbingElementTest

    # Absorbing for higher arity
    registry.register(GeneralAbsorbingElementTest(3, [0]))  # only test position 0
    registry.register(GeneralAbsorbingElementTest(3, [0, 1, 2]))  # test all positions

    return registry


def create_function_analysis_registry() -> PropertyRegistry:
    """Registry for analyzing general function behavior and properties."""
    registry = PropertyRegistry()

    # Injectivity - one-to-one mapping
    registry.register(InjectivityTest())  # unary functions
    registry.register(InjectivityTest(2))  # binary functions
    registry.register(InjectivityTest(3))  # ternary functions

    # Fixed points - f(x) == x behavior
    registry.register(FixedPointTest())  # f(x) == x
    registry.register(FixedPointTest(2, 0))  # f(x, y) == x (compare result with first arg)
    registry.register(FixedPointTest(2, 1))  # f(x, y) == y (compare result with second arg)
    registry.register(FixedPointTest(3, 0))  # f(x, y, z) == x
    registry.register(FixedPointTest(3, 1))  # f(x, y, z) == y
    registry.register(FixedPointTest(3, 2))  # f(x, y, z) == z

    return registry


def create_composition_registry() -> PropertyRegistry:
    """Registry for testing function composition behaviors."""
    registry = PropertyRegistry()

    # Left composition - f(g(x)) == g(x)
    registry.register(LeftCompositionTest())  # unary case
    registry.register(LeftCompositionTest(2, 0))  # f(g(x,y), _) == g(x,y) at pos 0
    registry.register(LeftCompositionTest(2, 1))  # f(_, g(x,y)) == g(x,y) at pos 1
    registry.register(LeftCompositionTest(3, 0))  # ternary functions
    registry.register(LeftCompositionTest(3, 1))
    registry.register(LeftCompositionTest(3, 2))

    # Right composition - f(g(x)) == f(x)
    registry.register(RightCompositionTest())  # unary case
    registry.register(RightCompositionTest(2, 0))  # f(g(x,y), _) == f(x,y)
    registry.register(RightCompositionTest(2, 1))  # f(_, g(x,y)) == f(x,y)
    registry.register(RightCompositionTest(3, 0))
    registry.register(RightCompositionTest(3, 1))
    registry.register(RightCompositionTest(3, 2))

    # Involution - f(g(x)) == x (functions are inverses)
    registry.register(InvolutionTest())  # unary case
    registry.register(InvolutionTest(2, 0))  # f(g(x,y), _) == x (return to pos 0)
    registry.register(InvolutionTest(2, 1))  # f(_, g(x,y)) == y (return to pos 1)
    registry.register(InvolutionTest(3, 0))
    registry.register(InvolutionTest(3, 1))
    registry.register(InvolutionTest(3, 2))

    return registry


def create_comprehensive_registry() -> PropertyRegistry:
    """Create a comprehensive registry with all property categories."""
    registry = PropertyRegistry()

    # Add all specialized registries
    symmetry_reg = create_symmetry_registry()
    algebraic_reg = create_algebraic_structure_registry()
    elements_reg = create_special_elements_registry()
    analysis_reg = create_function_analysis_registry()
    composition_reg = create_composition_registry()

    # Merge all registries
    for test_reg in [symmetry_reg, algebraic_reg, elements_reg, analysis_reg, composition_reg]:
        for test in test_reg.get_all():
            registry.register(test)

    return registry


def create_basic_registry() -> PropertyRegistry:
    """Create a basic registry with commonly used properties."""
    registry = PropertyRegistry()

    # Most common symmetry test
    registry.register(CommutativityTest())

    # Core algebraic properties
    registry.register(AssociativityTest())
    registry.register(DistributivityTest())

    # Basic special elements
    registry.register(IdentityElementTest())
    registry.register(AbsorbingElementTest())

    # Essential function analysis
    registry.register(InjectivityTest())
    registry.register(FixedPointTest())

    # Key composition properties
    registry.register(InvolutionTest())

    return registry


def create_arithmetic_registry() -> PropertyRegistry:
    """Registry optimized for testing arithmetic operations."""
    registry = PropertyRegistry()

    # Arithmetic is typically commutative
    registry.register(CommutativityTest())

    # Arithmetic is typically associative
    registry.register(AssociativityTest())

    # Test for additive identity (0) and multiplicative identity (1)
    registry.register(IdentityElementTest())

    # Test for absorbing elements (0 in multiplication)
    registry.register(AbsorbingElementTest())

    # Multiplication distributes over addition
    registry.register(DistributivityTest())

    return registry


def create_logical_operations_registry() -> PropertyRegistry:
    """Registry optimized for testing logical/boolean operations."""
    registry = PropertyRegistry()

    # Boolean operations are typically commutative
    registry.register(CommutativityTest())

    # Boolean operations are typically associative
    registry.register(AssociativityTest())

    # Test for logical identities (true for AND, false for OR)
    registry.register(IdentityElementTest())

    # Test for absorbing elements (false for AND, true for OR)
    registry.register(AbsorbingElementTest())

    # AND distributes over OR, OR distributes over AND
    registry.register(DistributivityTest())

    return registry


def create_cryptographic_registry() -> PropertyRegistry:
    """Registry for testing cryptographic and encoding functions."""
    registry = PropertyRegistry()

    # Crypto functions should be injective (no collisions)
    registry.register(InjectivityTest())

    # Test encode/decode as inverse operations
    registry.register(InvolutionTest())

    # For hash functions and encoders
    registry.register(InjectivityTest(2))  # keyed operations

    return registry


def create_data_structure_registry() -> PropertyRegistry:
    """Registry for testing data structure operations."""
    registry = PropertyRegistry()

    # Many data structure operations are commutative (set union, intersection)
    registry.register(CommutativityTest())

    # Operations like union, merge are often associative
    registry.register(AssociativityTest())

    # Test for neutral elements (empty set, empty list)
    registry.register(IdentityElementTest())

    # Some operations have absorbing elements
    registry.register(AbsorbingElementTest())

    # Test uniqueness properties for keys, IDs
    registry.register(InjectivityTest())

    return registry
