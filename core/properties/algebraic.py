from core.function_under_test import CombinedFunctionUnderTest
from core.property_tester import TestResult, TestStats, PropertyTest


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

    def test(self, function: CombinedFunctionUnderTest, inputs, early_stopping) -> TestResult:
        f_name = function.funcs[0].func.__name__
        input_arity = self.input_arity

        valid_inputs = [input_set for input_set in inputs if len(input_set) >= input_arity]

        if not valid_inputs:
            return {
                "holds": False,
                "counterexamples": [f"Commutativity test failed: No valid input sets provided for {f_name}\n"],
                "stats": {"total_count": 0, "success_count": 0},
            }

        total_tests = 0
        counterexamples = []

        for input_set in valid_inputs:
            a, b = input_set[:2]
            r1 = function.call(0, a, b)
            r2 = function.call(0, b, a)

            total_tests += 1

            if not function.compare_results(r1, r2):
                counterexamples.append(
                    f"{f_name}({a},{b}): {r1}\n\t"
                    f"{f_name}({b},{a}): {r2}\n"
                )
                if early_stopping:
                    break

        # Build result
        test_stats: TestStats = {
            'total_count': total_tests,
            'success_count': total_tests - len(counterexamples)
        }

        if not counterexamples:
            return {
                "holds": True,
                "counterexamples": [f"{f_name}(a,b) == {f_name}(b,a)\n"],
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

    def test(self, combined: CombinedFunctionUnderTest, inputs, early_stopping) -> TestResult:
        f_name = combined.funcs[0].func.__name__
        g_name = combined.funcs[1].func.__name__
        input_arity = self.input_arity

        # Filter valid inputs based on arity
        valid_inputs = [input_set for input_set in inputs if len(input_set) >= input_arity]

        if not valid_inputs:
            return {
                "holds": False,
                "counterexamples": [f"Associativity test failed: No valid input sets provided for {f_name}\n"],
                "stats": {"total_count": 0, "success_count": 0},
            }

        # Test associativity for each valid input
        total_tests = 0
        counterexamples = []

        for input_set in valid_inputs:
            a, b, c = input_set[:3]
            total_tests += 1

            # Test f(a, g(b, c)) == f(g(a, b), c)
            r1 = combined.call(0, a, combined.call(1, b, c))
            r2 = combined.call(0, combined.call(1, a, b), c)

            if not combined.compare_results(r1, r2):
                counterexamples.append(
                    f"{f_name}({a}, {g_name}({b}, {c})): {r1}\n\t"
                    f"{f_name}({g_name}({a}, {b}), {c}): {r2}\n"
                )

                if early_stopping:
                    break

        # Build result
        test_stats: TestStats = {
            'total_count': total_tests,
            'success_count': total_tests - len(counterexamples)
        }

        if not counterexamples:
            return {
                "holds": True,
                "counterexamples": [f"{f_name}(a, {g_name}(b, c)) == {f_name}({g_name}(a, b), c)\n"],
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

    def test(self, function: CombinedFunctionUnderTest, inputs, early_stopping) -> TestResult:
        f_name = function.funcs[0].func.__name__
        valid_inputs = [input_set for input_set in inputs if len(input_set) >= 1]

        if not valid_inputs:
            return {
                "holds": False,
                "counterexamples": [f"Idempotence test failed: No valid input sets provided for {f_name}\n"],
                "stats": {"total_count": 0, "success_count": 0},
            }

        total_tests = 0
        counterexamples = []

        for input_set in valid_inputs:
            a = input_set[0]
            r1 = function.call(0, a)
            r2 = function.call(0, r1)

            total_tests += 1

            if not function.compare_results(r1, r2):
                counterexamples.append(
                    f"{f_name}({a}): {r1}\n\t"
                    f"{f_name}({f_name}({a})): {r2}\n"
                )
                if early_stopping:
                    break

        # Build result
        test_stats: TestStats = {
            'total_count': total_tests,
            'success_count': total_tests - len(counterexamples)
        }

        if not counterexamples:
            return {
                "holds": True,
                "counterexamples": [f"{f_name}({f_name}(a)) == {f_name}(a)"],
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

    def test(self, combined: CombinedFunctionUnderTest, inputs, early_stopping) -> TestResult:
        f_name = combined.funcs[0].func.__name__
        g_name = combined.funcs[1].func.__name__
        input_arity = self.input_arity

        # Filter valid inputs based on arity
        valid_inputs = [input_set for input_set in inputs if len(input_set) >= input_arity]

        if not valid_inputs:
            return {
                "holds": False,
                "counterexamples": [f"Distributivity test failed: No valid input sets provided for {f_name}\n"],
                "stats": {"total_count": 0, "success_count": 0},
            }

        # Test distributivity for each valid input
        total_tests = 0
        counterexamples = []

        for input_set in valid_inputs:
            a, b, c = input_set[:3]  # Take first three elements
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
                    f"{f_name}({a},{g_name}({b},{c})): {r1}\n\t"
                    f"{g_name}({f_name}({a},{b}),{f_name}({a},{c})): {r2}\n"
                )

                if early_stopping:
                    break

        # Build result
        test_stats: TestStats = {
            'total_count': total_tests,
            'success_count': total_tests - len(counterexamples)
        }

        if not counterexamples:
            return {
                "holds": True,
                "counterexamples": [f"{f_name}(a,{g_name}(b,c)) == {g_name}({f_name}(a,b),{f_name}(a,c))\n"],
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

    def test(self, function: CombinedFunctionUnderTest, inputs, early_stopping) -> TestResult:
        fut = function.funcs[0]
        f_name = fut.func.__name__
        input_arity = self.input_arity

        # Extract all unique elements from valid input tuples
        all_elements = set()
        all_elements.update(element for input_set in inputs if len(input_set) >= input_arity for element in input_set)

        if not all_elements:
            return {
                "holds": False,
                "counterexamples": [f"IdentityElement test failed: No valid input sets provided for {f_name}\n"],
                "stats": {"total_count": 0, "success_count": 0},
            }

        # Setup conversion cache
        conversion_cache = {}

        def cached_convert(raw_val):
            if raw_val not in conversion_cache:
                conversion_cache[raw_val] = fut.arg_converter(raw_val)
            return conversion_cache[raw_val]

        # Test each element as potential identity
        total_tests = 0
        surviving_candidates = []
        counterexamples = []

        for candidate in all_elements:
            is_identity = True

            for element in all_elements:
                total_tests += 1

                # Test both f(element, candidate) and f(candidate, element)
                r1 = function.call(0, element, candidate)
                r2 = function.call(0, candidate, element)
                expected = cached_convert(element)

                if not (function.compare_results(r1, expected) and function.compare_results(r2, expected)):
                    is_identity = False
                    counterexamples.append(
                        f"{f_name}({element}, {candidate}): {r1}\n\t"
                        f"{f_name}({candidate}, {element}): {r2}\n\t"
                        f"Expected both to equal: {element}\n"
                    )
                    break

            if is_identity:
                surviving_candidates.append(f"{candidate} is an identity element for {f_name}\n")

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

    def test(self, function: CombinedFunctionUnderTest, inputs, early_stopping) -> TestResult:
        fut = function.funcs[0]
        f_name = fut.func.__name__
        input_arity = self.input_arity

        # Extract all unique elements from valid input tuples
        all_elements = set()
        all_elements.update(element for input_set in inputs if len(input_set) >= input_arity for element in input_set)

        if not all_elements:
            return {
                "holds": False,
                "counterexamples": [f"AbsorbingElement test failed: No valid input sets provided for {f_name}\n"],
                "stats": {"total_count": 0, "success_count": 0},
            }
        # Setup conversion cache
        conversion_cache = {}

        def cached_convert(raw_val):
            if raw_val not in conversion_cache:
                conversion_cache[raw_val] = fut.arg_converter(raw_val)
            return conversion_cache[raw_val]

        # Test each element as potential absorbing element
        total_tests = 0
        surviving_candidates = []
        counterexamples = []

        for candidate in all_elements:
            is_absorbing = True

            for element in all_elements:
                total_tests += 1

                # Test both f(element, candidate) and f(candidate, element)
                r1 = function.call(0, element, candidate)
                r2 = function.call(0, candidate, element)
                expected = cached_convert(candidate)

                if not (function.compare_results(r1, expected) and function.compare_results(r2, expected)):
                    is_absorbing = False
                    counterexamples.append(
                        f"{f_name}({element}, {candidate}): {r1}\n\t"
                        f"{f_name}({candidate}, {element}): {r2}\n\t"
                        f"Expected both to equal: {candidate}\n"
                    )
                    break

            if is_absorbing:
                surviving_candidates.append(f"{candidate} is an absorbing element for {f_name}\n")

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

    def test(self, function: CombinedFunctionUnderTest, inputs, early_stopping) -> TestResult:
        fut = function.funcs[0]
        f_name = fut.func.__name__
        input_arity = self.input_arity

        # Extract all unique elements from valid input tuples
        all_elements = set()
        all_elements.update(element for input_set in inputs if len(input_set) >= input_arity for element in input_set)

        if not all_elements:
            return {
                "holds": False,
                "counterexamples": [f"FixedPoint test failed: No valid input sets provided for {f_name}\n"],
                "stats": {"total_count": 0, "success_count": 0},
            }

        # Setup conversion cache
        conversion_cache = {}

        def cached_convert(raw_val):
            if raw_val not in conversion_cache:
                conversion_cache[raw_val] = fut.arg_converter(raw_val)
            return conversion_cache[raw_val]

        # Test each element as potential fixed point
        total_tests = 0
        fixed_points = []
        counterexamples = []

        for candidate in all_elements:
            total_tests += 1
            result = function.call(0, candidate)
            result2 = function.call(0, candidate) # Call twice to ensure consistency
            expected = cached_convert(candidate)

            if function.compare_results(result, expected) and function.compare_results(result2, expected):
                fixed_points.append(f"{f_name}({candidate}) = {candidate}\n")
            else:
                counterexamples.append(f"{f_name}({candidate}): {result} ≠ {candidate}\n")

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
