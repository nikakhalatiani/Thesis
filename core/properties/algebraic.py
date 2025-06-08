from core.function_under_test import CombinedFunctionUnderTest
from core.properties.property_test import TestResult, TestStats, PropertyTest

from itertools import chain, combinations, product


class CommutativityTest(PropertyTest):
    """Test if f(a,b) = f(b,a)"""

    def __init__(self):
        super().__init__(
            name="Commutativity",
            input_arity=2,
            function_arity=2,
            description="Tests if f(a,b) equals f(b,a)",
            category="Algebraic"
        )

    def test(self, function: CombinedFunctionUnderTest, inputs, max_counterexamples) -> TestResult:
        f_name = function.funcs[0].func.__name__

        # Gather all unique elements from valid input sets
        all_elements = frozenset(chain.from_iterable(inputs))

        # all_elements = list(all_elements)
        if len(all_elements) < self.input_arity:
            return {
                "holds": False,
                "counterexamples": ["Not enough elements provided\n"],
                "stats": {"total_count": 0, "success_count": 0},
            }

        total_tests = 0
        counterexamples = []

        for a, b in combinations(all_elements, 2):
            # for i in range(0, len(all_elements) - 1):
            #     a = all_elements[i]
            #     b = all_elements[i + 1]
            r1 = function.call(0, a, b)
            r2 = function.call(0, b, a)
            total_tests += 1

            if not function.compare_results(r1, r2):
                counterexamples.append(
                    f"{f_name}({a}, {b}): {r1}\n\t"
                    f"{f_name}({b}, {a}): {r2}\n"
                )
                if len(counterexamples) >= max_counterexamples:
                    break

        test_stats: TestStats = {
            "total_count": total_tests,
            "success_count": total_tests - len(counterexamples)
        }

        if not counterexamples:
            return {
                "holds": True,
                "counterexamples": [f"{f_name}(a,b) == {f_name}(b,a) for all tested inputs\n"],
                "stats": test_stats,
            }
        else:
            return {
                "holds": False,
                "counterexamples": counterexamples,
                "stats": test_stats,
            }


class AssociativityTest(PropertyTest):
    """Test if f(a, f(b, c)) = f(f(a, b), c)"""

    def __init__(self):
        super().__init__(
            name="Associativity",
            input_arity=3,
            function_arity=2,
            description="Tests if f(a, f(b, c)) equals f(f(a, b), c)",
            category="Algebraic"
        )
        self.num_functions = 2

    def test(self, combined: CombinedFunctionUnderTest, inputs, max_counterexamples) -> TestResult:
        f_name = combined.funcs[0].func.__name__
        g_name = combined.funcs[1].func.__name__

        # Filter valid inputs based on arity
        all_elements = frozenset(chain.from_iterable(inputs))

        if len(all_elements) < self.input_arity:
            return {
                "holds": False,
                "counterexamples": ["Not enough elements provided\n"],
                "stats": {"total_count": 0, "success_count": 0},
            }

        # Test associativity for each valid input
        total_tests = 0
        counterexamples = []

        for a, b, c in combinations(all_elements, 3):
            total_tests += 1

            # Test f(a, g(b, c)) == f(g(a, b), c)
            r1 = combined.call(0, a, combined.call(1, b, c))
            r2 = combined.call(0, combined.call(1, a, b), c)

            if not combined.compare_results(r1, r2):
                counterexamples.append(
                    f"{f_name}({a}, {g_name}({b}, {c})): {r1}\n\t"
                    f"{f_name}({g_name}({a}, {b}), {c}): {r2}\n"
                )

                if len(counterexamples) >= max_counterexamples:
                    break

        # Build result
        test_stats: TestStats = {
            'total_count': total_tests,
            'success_count': total_tests - len(counterexamples)
        }

        if not counterexamples:
            return {
                "holds": True,
                "counterexamples": [
                    f"{f_name}(a, {g_name}(b, c)) == {f_name}({g_name}(a, b), c) for all tested inputs\n"],
                "stats": test_stats,
            }
        else:
            return {
                "holds": False,
                "counterexamples": counterexamples,
                "stats": test_stats,
            }


# TODO ask if f(g(x)) = f(x) is a valid property test or f(g(x)) = g(x) or f(g(x)) = g(f(x)) is a valid property test
class IdempotenceTest(PropertyTest):
    """Test if f(f(x)) = f(x)"""

    def __init__(self) -> None:
        super().__init__(
            name="Idempotence",
            input_arity=1,
            function_arity=1,
            description="Tests if f(f(x)) equals f(x)",
            category="Algebraic"
        )

    def test(self, function: CombinedFunctionUnderTest, inputs, max_counterexamples) -> TestResult:
        f_name = function.funcs[0].func.__name__

        all_elements = frozenset(chain.from_iterable(inputs))

        if len(all_elements) < self.input_arity:
            return {
                "holds": False,
                "counterexamples": ["Not enough elements provided\n"],
                "stats": {"total_count": 0, "success_count": 0},
            }

        total_tests = 0
        counterexamples = []

        for a in all_elements:
            r1 = function.call(0, a)
            r2 = function.call(0, r1)

            total_tests += 1

            if not function.compare_results(r1, r2):
                counterexamples.append(
                    f"{f_name}({a}): {r1}\n\t"
                    f"{f_name}({f_name}({a})): {r2}\n"
                )
                if len(counterexamples) >= max_counterexamples:
                    break

        # Build result
        test_stats: TestStats = {
            'total_count': total_tests,
            'success_count': total_tests - len(counterexamples)
        }

        if not counterexamples:
            return {
                "holds": True,
                "counterexamples": [f"{f_name}({f_name}(a)) == {f_name}(a) for all tested inputs\n"],
                "stats": test_stats,
            }
        else:
            return {
                "holds": False,
                "counterexamples": counterexamples,
                "stats": test_stats,
            }


class DistributivityTest(PropertyTest):
    """Test if f(a, g(b, c)) == g(f(a, b), f(a, c))"""

    def __init__(self) -> None:
        super().__init__(
            name="Distributivity",
            input_arity=3,
            function_arity=2,
            description="f(a, g(b,c)) == g(f(a,b), f(a,c))",
            category="Algebraic"
        )
        self.num_functions = 2

    def test(self, combined: CombinedFunctionUnderTest, inputs, max_counterexamples) -> TestResult:
        f_name = combined.funcs[0].func.__name__
        g_name = combined.funcs[1].func.__name__

        # Filter valid inputs based on arity
        all_elements = frozenset(chain.from_iterable(inputs))

        if len(all_elements) < self.input_arity:
            return {
                "holds": False,
                "counterexamples": ["Not enough elements provided\n"],
                "stats": {"total_count": 0, "success_count": 0},
            }

        # Test distributivity for each valid input
        total_tests = 0
        counterexamples = []

        for a, b, c in combinations(all_elements, 3):
            total_tests += 1

            # Test f(a, g(b, c)) == g(f(a, b), f(a, c))
            # compute f(a, g(b,c))
            inner = combined.call(1, b, c)
            r1 = combined.call(0, a, inner)

            # compute g(f(a,b), f(a,c))
            left_inner = combined.call(0, a, b)
            right_inner = combined.call(0, a, c)
            r2 = combined.call(1, left_inner, right_inner)

            if not combined.compare_results(r1, r2):
                counterexamples.append(
                    f"{f_name}({a}, {g_name}({b}, {c})): {r1}\n\t"
                    f"{g_name}({f_name}({a}, {b}) ,{f_name}({a}, {c})): {r2}\n"
                )

                if len(counterexamples) >= max_counterexamples:
                    break

        # Build result
        test_stats: TestStats = {
            'total_count': total_tests,
            'success_count': total_tests - len(counterexamples)
        }

        if not counterexamples:
            return {
                "holds": True,
                "counterexamples": [
                    f"{f_name}(a, {g_name}(b, c)) == {g_name}({f_name}(a, b), {f_name}(a, c)) for all tested inputs\n"],
                "stats": test_stats,
            }
        else:
            return {
                "holds": False,
                "counterexamples": counterexamples,
                "stats": test_stats,
            }


class IdentityElementTest(PropertyTest):
    """
    Test if a binary function f has an identity element e such that:
        f(a, e) == a  and  f(e, a) == a
    """

    def __init__(self) -> None:
        super().__init__(
            name="IdentityElement",
            input_arity=2,
            function_arity=2,
            description="Checks whether candidate acts as an identity element for f",
            category="Algebraic"
        )

    def test(self, function: CombinedFunctionUnderTest, inputs, max_counter_examples) -> TestResult:
        fut = function.funcs[0]
        f_name = fut.func.__name__

        # Extract all unique elements from valid input tuples
        all_elements = frozenset(chain.from_iterable(inputs))

        if len(all_elements) < self.input_arity:
            return {
                "holds": False,
                "counterexamples": ["Not enough elements provided\n"],
                "stats": {"total_count": 0, "success_count": 0},
            }

        # Setup conversion cache
        conversion_cache = {}

        def cached_convert(raw_val):
            if raw_val not in conversion_cache:
                conversion_cache[raw_val] = fut.arg_converter(raw_val)
            return conversion_cache[raw_val]

        identity_candidates = set(all_elements)
        counterexamples = []
        total_tests = 0

        for element, candidate in product(all_elements, all_elements):
            if candidate not in identity_candidates:
                continue  # Skip already eliminated candidates

            total_tests += 1

            # Test both f(element, candidate) and f(candidate, element)
            r1 = function.call(0, element, candidate)
            r2 = function.call(0, candidate, element)
            expected = cached_convert(element)

            if not (function.compare_results(r1, expected) and function.compare_results(r2, expected)):
                identity_candidates.discard(candidate)
                counterexamples.append(
                    f"{f_name}({element}, {candidate}): {r1}\n\t"
                    f"{f_name}({candidate}, {element}): {r2}\n\t"
                    f"Expected both to equal: {element}\n"
                )

        # Convert surviving candidates to result format
        surviving_candidates = [f"{candidate} is an identity element\n"
                                for candidate in identity_candidates]

        # Build result
        test_stats: TestStats = {
            'total_count': total_tests,
            'success_count': total_tests if surviving_candidates else 0
        }

        if surviving_candidates:
            return {
                "holds": True,
                "counterexamples": surviving_candidates,
                "stats": test_stats,
            }
        else:
            return {
                "holds": False,
                "counterexamples": counterexamples,
                "stats": test_stats,
            }


class AbsorbingElementTest(PropertyTest):
    """
    Test if a binary function f has an absorbing element z such that:
        f(a, z) == z  and  f(z, a) == z
    """

    def __init__(self) -> None:
        super().__init__(
            name="AbsorbingElement",
            input_arity=2,
            function_arity=2,
            description="Checks whether candidate acts as an absorbing element for f",
            category="Algebraic"
        )

    def test(self, function: CombinedFunctionUnderTest, inputs, max_counterexamples) -> TestResult:
        fut = function.funcs[0]
        f_name = fut.func.__name__

        # Extract all unique elements from valid input tuples
        all_elements = frozenset(chain.from_iterable(inputs))

        if len(all_elements) < self.input_arity:
            return {
                "holds": False,
                "counterexamples": ["Not enough elements provided\n"],
                "stats": {"total_count": 0, "success_count": 0},
            }

        # Setup conversion cache
        conversion_cache = {}

        def cached_convert(raw_val):
            if raw_val not in conversion_cache:
                conversion_cache[raw_val] = fut.arg_converter(raw_val)
            return conversion_cache[raw_val]

        absorbing_candidates = set(all_elements)
        counterexamples = []
        total_tests = 0

        for element, candidate in product(all_elements, all_elements):
            if candidate not in absorbing_candidates:
                continue  # Candidate already disqualified

            total_tests += 1

            # Absorbing: f(a, z) == z and f(z, a) == z
            expected = cached_convert(candidate)
            r1 = function.call(0, element, candidate)
            r2 = function.call(0, candidate, element)

            if not (function.compare_results(r1, expected) and function.compare_results(r2, expected)):
                absorbing_candidates.discard(candidate)
                counterexamples.append(
                    f"{f_name}({element}, {candidate}): {r1}\n\t"
                    f"{f_name}({candidate}, {element}): {r2}\n\t"
                    f"Expected both to equal: {candidate}\n"
                )

        # Convert surviving candidates to result format
        surviving_candidates = [f"{candidate} is an absorbing element\n"
                                for candidate in absorbing_candidates]

        # Build result
        test_stats: TestStats = {
            'total_count': total_tests,
            'success_count': total_tests if surviving_candidates else 0
        }

        if surviving_candidates:
            return {
                "holds": True,
                "counterexamples": surviving_candidates,
                "stats": test_stats,
            }
        else:
            return {
                "holds": False,
                "counterexamples": counterexamples,
                "stats": test_stats,
            }


class FixedPointTest(PropertyTest):
    """
    Test if a unary function f has fixed points where:
        f(x) == x
    """

    def __init__(self) -> None:
        super().__init__(
            name="FixedPoint",
            input_arity=1,
            function_arity=1,
            description="Checks whether inputs act as fixed points for f",
            category="Algebraic"
        )

    def test(self, function: CombinedFunctionUnderTest, inputs, max_counter_examples) -> TestResult:
        fut = function.funcs[0]
        f_name = fut.func.__name__

        # Extract all unique elements from valid input tuples
        all_elements = frozenset(chain.from_iterable(inputs))

        if len(all_elements) < self.input_arity:
            return {
                "holds": False,
                "counterexamples": ["Not enough elements provided\n"],
                "stats": {"total_count": 0, "success_count": 0},
            }

        # Setup conversion cache
        conversion_cache = {}

        def cached_convert(raw_val):
            if raw_val not in conversion_cache:
                conversion_cache[raw_val] = fut.arg_converter(raw_val)
            return conversion_cache[raw_val]

        total_tests = 0
        fixed_points = []
        counterexamples = []

        for candidate in all_elements:
            total_tests += 1

            expected = cached_convert(candidate)
            result1 = function.call(0, candidate)
            result2 = function.call(0, candidate)  # Call twice to ensure consistency

            if function.compare_results(result1, expected) and function.compare_results(result2, expected):
                fixed_points.append(f"{candidate} is a fixed point\n")
            else:
                counterexamples.append(f"{f_name}({candidate}): {result1} ≠ {candidate}\n")

        # Build result
        test_stats: TestStats = {
            'total_count': total_tests,
            # 'success_count': total_tests if fixed_points else 0
            'success_count': len(fixed_points)
        }

        if fixed_points:
            return {
                "holds": True,
                "counterexamples": fixed_points,
                "stats": test_stats,
            }
        else:
            return {
                "holds": False,
                "counterexamples": counterexamples,
                "stats": test_stats,
            }


# TODO interesting usage of try catch needs attention (CONVERTER)
# class ClosureTest(PropertyTest):
#     """
#     Test if a unary function f exhibits closure property where:
#         f(f(x)) is well-defined (output can be used as input)
#     """
#
#     def __init__(self) -> None:
#         super().__init__(
#             name="Closure",
#             input_arity=1,
#             function_arity=1,
#             description="Checks whether function output can be used as input (closure property)",
#             category="Algebraic"
#         )
#
#     def test(self, function: CombinedFunctionUnderTest, inputs, max_counterexamples) -> TestResult:
#         fut = function.funcs[0]
#         f_name = fut.func.__name__
#
#         # Extract all unique elements from valid input tuples
#         all_elements = frozenset(chain.from_iterable(inputs))
#
#         if len(all_elements) < self.input_arity:
#             return {
#                 "holds": False,
#                 "counterexamples": ["Not enough elements provided\n"],
#                 "stats": {"total_count": 0, "success_count": 0},
#             }
#
#         # Test each element for closure property
#         total_tests = 0
#         closure_satisfied = []
#         counterexamples = []
#
#         for candidate in all_elements:
#             total_tests += 1
#
#             try:
#                 # First call: f(x)
#                 first_result = function.call(0, candidate)
#
#                 # Second call: f(f(x)) - this tests closure
#                 _ = function.call(0, first_result)
#
#                 closure_satisfied.append(
#                     f"{f_name}({candidate}) → {f_name}({f_name}({candidate})): closure satisfied\n"
#                 )
#
#             except Exception as e:
#                 counterexamples.append(
#                     f"{f_name}({candidate}): First call succeeded, "
#                     f"but {f_name}(result) failed: {str(e)}\n"
#                 )
#                 if len(counterexamples) >= max_counterexamples:
#                     break
#
#         # Build result
#         test_stats: TestStats = {
#             'total_count': total_tests,
#             'success_count': len(closure_satisfied)
#         }
#
#         if closure_satisfied and not counterexamples:
#             return {
#                 "holds": True,
#                 "counterexamples": closure_satisfied,
#                 "stats": test_stats,
#             }
#         else:
#             return {
#                 "holds": False,
#                 "counterexamples": counterexamples if counterexamples else [
#                     f"No valid inputs for closure test on {f_name}\n"],
#                 "stats": test_stats,
#             }
#
#
# class CompositionTest(PropertyTest):
#     """
#     Test if two unary functions f and g can be composed where:
#         f(g(x)) is well-defined (output of g can be used as input to f)
#     """
#
#     def __init__(self) -> None:
#         super().__init__(
#             name="Composition",
#             input_arity=1,
#             function_arity=1,
#             description="Checks whether g's output can be used as input to f (f∘g composability)",
#             category="Algebraic"
#         )
#         self.num_functions = 2
#
#     def test(self, function: CombinedFunctionUnderTest, inputs, max_counterexamples) -> TestResult:
#         f_name = function.funcs[0].func.__name__  # First function
#         g_name = function.funcs[1].func.__name__  # Second function
#
#         # Extract all unique elements from valid input tuples
#         all_elements = frozenset(chain.from_iterable(inputs))
#
#         if len(all_elements) < self.input_arity:
#             return {
#                 "holds": False,
#                 "counterexamples": ["Not enough elements provided\n"],
#                 "stats": {"total_count": 0, "success_count": 0},
#             }
#
#         # Test each element for composition property
#         total_tests = 0
#         composition_satisfied = []
#         counterexamples = []
#
#         for candidate in all_elements:
#             total_tests += 1
#
#             try:
#                 # First call: g(x)
#                 candidate_converted = function.funcs[1].arg_converter(candidate)
#                 g_result = function.call(1, candidate_converted)
#
#                 # Second call: f(g(x)) - this tests if f can accept g's output
#                 _ = function.call(0, g_result)
#
#                 composition_satisfied.append(
#                     f"{f_name}({g_name}({candidate})): composition successful\n"
#                 )
#
#             except Exception as e:
#                 counterexamples.append(
#                     f"{g_name}({candidate}) succeeded, "
#                     f"but {f_name}({g_name}({candidate})) failed: {str(e)}\n"
#                 )
#                 if len(counterexamples) >= max_counterexamples:
#                     break
#
#         test_stats: TestStats = {
#             'total_count': total_tests,
#             'success_count': len(composition_satisfied)
#         }
#
#         if composition_satisfied and not counterexamples:
#             return {
#                 "holds": True,
#                 "counterexamples": composition_satisfied,
#                 "stats": test_stats,
#             }
#         else:
#             return {
#                 "holds": False,
#                 "counterexamples": counterexamples if counterexamples else [
#                     f"No valid inputs for composition test on {f_name}∘{g_name}\n"],
#                 "stats": test_stats,
#             }


class InjectivityTest(PropertyTest):
    """
    Test if a unary function is injective (one-to-one) on the provided inputs:
        ∀ a ≠ b: f(a) ≠ f(b)
    """

    def __init__(self) -> None:
        super().__init__(
            name="Injectivity",
            input_arity=1,
            function_arity=1,
            description="Checks whether f produces distinct outputs for distinct inputs (injective)",
            category="Algebraic"
        )

    def test(self, function: CombinedFunctionUnderTest, inputs, max_counterexamples) -> TestResult:
        fut = function.funcs[0]
        f_name = fut.func.__name__

        # Extract all unique elements from valid input tuples
        all_elements = frozenset(chain.from_iterable(inputs))
        if len(all_elements) < self.input_arity:
            return {
                "holds": False,
                "counterexamples": ["Not enough elements provided\n"],
                "stats": {"total_count": 0, "success_count": 0},
            }

        # Test all pairs of distinct elements for injectivity
        counterexamples = []
        total_tests = 0
        success_count = 0
        result_map = {}  # Maps function results to the input that produced them

        for element in all_elements:
            total_tests += 1

            # Get function result for this element
            result = function.call(0, element)

            # Check if we've seen this result before
            if result in result_map:
                # Found a collision - injectivity violated
                previous_element = result_map[result]
                counterexamples.append(
                    f"{f_name}({element}) = {result}\n\t"
                    f"{f_name}({previous_element}) = {result}\n"
                )

                # Early exit if we've hit max counterexamples
                if len(counterexamples) >= max_counterexamples:
                    break
            else:
                # New result - store it in the map
                result_map[result] = element
                success_count += 1

        # Build result
        test_stats: TestStats = {
            'total_count': total_tests,
            'success_count': success_count
        }

        if counterexamples:
            return {
                "holds": False,
                "counterexamples": counterexamples,
                "stats": test_stats,
            }
        else:
            return {
                "holds": True,
                "counterexamples": [f"{f_name} is injective on the tested inputs\n"],
                "stats": test_stats,
            }
