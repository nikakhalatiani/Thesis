from core.function_under_test import CombinedFunctionUnderTest
from core.properties.property_test import PropertyTest, TestResult


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

    def test(self, function: CombinedFunctionUnderTest, inputs: tuple) -> TestResult:
        a, b = inputs
        r1 = function.call(0, a, b)  # Call the first function with a, b
        r2 = function.call(0, b, a)

        f_name = function.funcs[0].func.__name__

        if function.compare_results(r1, r2):
            return True, f"{f_name}(a,b) == {f_name}(b,a)"
        else:
            return False, (
                f"{f_name}({a},{b}): {r1}\n\t"
                f"{f_name}({b},{a}): {r2}\n"
            )

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

    def test(self,
             combined: CombinedFunctionUnderTest,
             inputs: tuple) -> TestResult:

        a, b, c = inputs[:3]
        # we’ll test associativity on the 0th function in the combined wrapper:
        #   r1 = f(a, f(b,c));  r2 = f(f(a,b), c)
        r1 = combined.call(0, a, combined.call(1, b, c))
        r2 = combined.call(0, combined.call(1, a, b), c)

        f_name = combined.funcs[0].func.__name__
        g_name = combined.funcs[1].func.__name__

        if combined.compare_results(r1, r2):
            return True, (
                f"{f_name}(a, {g_name}(b, c)) "
                f"== {f_name}({g_name}(a, b), c)"
            )
        else:
            return False, (
                f"{f_name}({a}, {g_name}({b}, {c})): {r1}\n\t"
                f"{f_name}({g_name}({a}, {b}), {c}): {r2}\n"
            )


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

    def test(self, function: CombinedFunctionUnderTest, inputs: tuple) -> TestResult:
        a = inputs[0]
        r1 = function.call(0, a)
        r2 = function.call(0, r1)

        f_name = function.funcs[0].func.__name__

        if function.compare_results(r1, r2):
            return True, f"{f_name}({f_name}(a)) == {f_name}(a)"
        else:
            return False, (
                f"{f_name}({a}): {r1}\n\t"
                f"{f_name}({f_name}({a})): {r2}\n"
            )


# class LeftIdempotenceTest(PropertyTest):
#     """Test if f(a, f(a,b)) = f(a,b) - the left argument dominates when repeated"""
#
#     def __init__(self):
#         super().__init__(
#             name="Left Idempotence",
#             input_arity=2,
#             function_arity=2,
#             description="Tests if f(a, f(a,b)) equals f(a,b) - left argument idempotence",
#             category="Algebraic"
#         )
#
#     def test(self, function: CombinedFunctionUnderTest, inputs: tuple) -> TestResult:
#         a, b = inputs[:2]
#         r1 = function.call(a, b)
#         r2 = function.call(a, r1)
#
#         f_name = function.funcs[0].__name__
#
#         if function.compare_results(r1, r2):
#             return True, f"{f_name}(a,b) == {f_name}(a,{f_name}(a,b))"
#         else:
#             return False, (
#                 f"{f_name}({a},{b}): {r1}\n\t"
#                 f"{f_name}({a},{f_name}({a},{b})): {r2}\n"
#             )
#
#
# class RightIdempotenceTest(PropertyTest):
#     """Test if f(f(a,b), b) = f(a,b) - the right argument dominates when repeated"""
#
#     def __init__(self):
#         super().__init__(
#             name="Right Idempotence",
#             input_arity=2,
#             function_arity=2,
#             description="Tests if f(f(a,b), b) equals f(a,b) - right argument idempotence",
#             category="Algebraic"
#         )
#
#     def test(self, function: CombinedFunctionUnderTest, inputs: tuple) -> TestResult:
#         a, b = inputs[:2]
#         r1 = function.call(a, b)
#         r2 = function.call(r1, b)
#
#         f_name = function.funcs[0].__name__
#
#         if function.compare_results(r1, r2):
#             return True, f"{f_name}(a,b) == {f_name}({f_name}(a,b),b)"
#         else:
#             return False, (
#                 f"{f_name}({a},{b}): {r1}\n\t"
#                 f"{f_name}({f_name}({a},{b}),{b}): {r2}\n"
#             )
#
#
# class FullIdempotenceTest(PropertyTest):
#     """Test if f(f(a,b), f(a,b)) = f(a,b) - complete idempotence"""
#
#     def __init__(self):
#         super().__init__(
#             name="Full Idempotence",
#             input_arity=2,
#             function_arity=2,
#             description="Tests if f(f(a,b), f(a,b)) equals f(a,b) - complete idempotence",
#             category="Algebraic"
#         )
#
#     def test(self, function: CombinedFunctionUnderTest, inputs: tuple) -> TestResult:
#         a, b = inputs[:2]
#         r1 = function.call(a, b)
#         r2 = function.call(r1, r1)
#
#         f_name = function.funcs[0].__name__
#
#         if function.compare_results(r1, r2):
#             return True, f"{f_name}(a,b) == {f_name}({f_name}(a,b),{f_name}(a,b))"
#         else:
#             return False, (
#                 f"{f_name}({a},{b}): {r1}\n\t"
#                 f"{f_name}({f_name}({a},{b}),{f_name}({a},{b})): {r2}\n"
#             )

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

    def test(self, combined: CombinedFunctionUnderTest, inputs: tuple) -> TestResult:
        a, b, c = inputs
        # f is funcs[0], g is funcs[1]

        # compute f(a, g(b,c))
        inner = combined.call(1, b, c)
        r1 = combined.call(0, a, inner)

        # compute g(f(a,b), f(a,c))
        left_inner = combined.call(0, a, b)
        right_inner = combined.call(0, a, c)
        r2 = combined.call(1, left_inner, right_inner)

        # extract the real function names
        f_name = combined.funcs[0].func.__name__
        g_name = combined.funcs[1].func.__name__

        # compare with a default comparator of the first function
        if combined.compare_results(r1, r2):
            return True, f"{f_name}(a,{g_name}(b,c)) == {g_name}({f_name}(a,b),{f_name}(a,c))"
        else:
            return False, (
                f"{f_name}({a},{g_name}({b},{c})): {r1}\n\t"
                f"{g_name}({f_name}({a},{b}),{f_name}({a},{c})): {r2}\n"
            )


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

    def test(self, combined: CombinedFunctionUnderTest, inputs: list[tuple], early_stopping) -> TestResult:
        fut = combined.funcs[0]
        f_name = fut.func.__name__

        # Extract all unique elements from valid input tuples
        all_elements = set()
        for input_set in inputs:
            if len(input_set) >= self.input_arity:
                all_elements.update(input_set)

        if not all_elements:
            return False, [f"IdentityElement test failed: No valid input sets provided for {f_name}"], {
                'total_count': 0, 'success_count': 0
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
                r1 = combined.call(0, element, candidate)
                r2 = combined.call(0, candidate, element)
                expected = cached_convert(element)

                if not (combined.compare_results(r1, expected) and combined.compare_results(r2, expected)):
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
        test_stats = {
            'total_count': total_tests,
            'success_count': total_tests if surviving_candidates else 0
        }

        if surviving_candidates:
            return True, surviving_candidates, test_stats
        else:
            return False, counterexamples, test_stats

