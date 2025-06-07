from core.function_under_test import CombinedFunctionUnderTest
from core.property_tester import PropertyTest, TestResult, TestStats

import inspect


# TODO ask if f(g(x)) == x is a valid test, or if it should be f(f(x)) == x
class InvolutionTest(PropertyTest):
    """Test if f(f(x)) = x (function is its own inverse)"""

    def __init__(self):
        super().__init__(
            name="Involution",
            input_arity=1,
            function_arity=1,
            description="Tests if f(f(x)) equals x",
            category="Composition"
        )

    def test(self, function: CombinedFunctionUnderTest, inputs, early_stopping) -> TestResult:
        fut = function.funcs[0]
        f_name = fut.func.__name__
        input_arity = self.input_arity

        # Filter valid inputs based on arity
        valid_inputs = [input_set for input_set in inputs if len(input_set) >= input_arity]

        if not valid_inputs:
            return {
                "holds": False,
                "counterexamples": [f"Involution test failed: No valid input sets provided for {f_name}\n"],
                "stats": {"total_count": 0, "success_count": 0},
            }

        # Test involution for each valid input
        total_tests = 0
        counterexamples = []

        for input_set in valid_inputs:
            raw_input = input_set[0]  # Take first element
            total_tests += 1

            # Test f(f(x)) == x
            a = fut.arg_converter(raw_input)
            r1 = function.call(0, a)
            r2 = function.call(0, r1)

            if not function.compare_results(r2, a):
                counterexamples.append(
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
                "counterexamples": [f"{f_name}({f_name}(a)) == a\n"],
                "stats": test_stats,
            }
        else:
            return {
                "holds": False,
                "counterexamples": counterexamples,
                "stats": test_stats,
            }


class ScalarHomomorphismTest(PropertyTest):
    """
    Test if for two functions f (unary) and g (binary):
        f(g(k, a)) == g(k, f(a))
    """

    def __init__(self) -> None:
        super().__init__(
            name="ScalarHomomorphism",
            input_arity=2,
            function_arity=0,  # overridden in is_applicable
            description="Checks f(g(k,a)) == g(k, f(a)) for two functions f,g",
            category="Composition"
        )
        self.num_functions = 2

    def is_applicable(self, candidate: CombinedFunctionUnderTest) -> bool:
        """
        Applicable exactly when candidate is CombinedFunctionUnderTest of length 2,
        where:
          - funcs[0] takes 1 argument (f: A -> B)
          - funcs[1] takes 2 arguments (g: K x A -> B)
        """
        if self.num_functions != len(candidate.funcs):
            return False

        f_ut, g_ut = candidate.funcs
        sig_f = inspect.signature(f_ut.func)
        sig_g = inspect.signature(g_ut.func)

        return (len(sig_f.parameters) == 1) and (len(sig_g.parameters) == 2)

    def test(self, combined: CombinedFunctionUnderTest, inputs, early_stopping) -> TestResult:
        # Unpack f and g
        f_ut, g_ut = combined.funcs
        f_name = f_ut.func.__name__
        g_name = g_ut.func.__name__
        input_arity = self.input_arity

        # Filter valid inputs based on arity
        valid_inputs = [input_set for input_set in inputs if len(input_set) >= input_arity]

        if not valid_inputs:
            return {
                "holds": False,
                "counterexamples": [f"ScalarHomomorphism test failed: No valid input sets provided for {f_name}\n"],
                "stats": {"total_count": 0, "success_count": 0},
            }

        # Test scalar homomorphism for each valid input
        total_tests = 0
        counterexamples = []

        for input_set in valid_inputs:
            a, k = input_set[:2]
            total_tests += 1

            # Test f(g(k, a)) == g(k, f(a))
            # Compute f(g(k, a))
            ga = combined.call(1, k, a)  # g(k, a)
            r1 = combined.call(0, ga)  # f(g(k, a))

            # Compute g(k, f(a))
            fa = combined.call(0, a)  # f(a)
            r2 = combined.call(1, k, fa)  # g(k, f(a))

            if not combined.compare_results(r1, r2):
                counterexamples.append(
                    f"{f_name}({g_name}({k},{a})): {r1}\n\t"
                    f"{g_name}({k},{f_name}({a})): {r2}\n"
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
                "counterexamples": [f"{f_name}({g_name}(k,a)) == {g_name}(k,{f_name}(a))\n"],
                "stats": test_stats,
            }
        else:
            return {
                "holds": False,
                "counterexamples": counterexamples,
                "stats": test_stats,
            }


class HomomorphismTest(PropertyTest):
    """
    Test if for two functions f (unary) and g (binary):
        f(g(a, b)) == g(f(a), f(b))
    """

    def __init__(self) -> None:
        super().__init__(
            name="Homomorphism",
            input_arity=2,
            function_arity=0,  # overridden in is_applicable
            description="Checks f(g(a,b)) == g(f(a), f(b)) for two functions f, g",
            category="Behavioral"
        )
        self.num_functions = 2

    def is_applicable(self, candidate: CombinedFunctionUnderTest) -> bool:
        """
        Applicable exactly when candidate is CombinedFunctionUnderTest of length 2,
        where:
          - funcs[0] takes 1 argument (f: A → B)
          - funcs[1] takes 2 arguments (g: A × A → A or B)
        """
        if self.num_functions != len(candidate.funcs):
            return False

        f_ut, g_ut = candidate.funcs
        sig_f = inspect.signature(f_ut.func)
        sig_g = inspect.signature(g_ut.func)

        return (len(sig_f.parameters) == 1) and (len(sig_g.parameters) == 2)

    def test(self, combined: CombinedFunctionUnderTest, inputs: list[tuple], early_stopping=False) -> TestResult:
        # Unpack f and g
        f_ut, g_ut = combined.funcs
        f_name = f_ut.func.__name__
        g_name = g_ut.func.__name__
        input_arity = self.input_arity

        # Filter valid inputs based on arity
        valid_inputs = [input_set for input_set in inputs if len(input_set) >= input_arity]

        if not valid_inputs:
            return {
                "holds": False,
                "counterexamples": [f"Homomorphism test failed: No valid input sets provided for {f_name}\n"],
                "stats": {"total_count": 0, "success_count": 0},
            }
        # Test homomorphism for each valid input
        total_tests = 0
        counterexamples = []

        for input_set in valid_inputs:
            a_raw, b_raw = input_set[:2]  # Take first two elements
            total_tests += 1

            # Test f(g(a, b)) == g(f(a), f(b))
            # Compute f(g(a, b))
            gab = combined.call(1, a_raw, b_raw)  # g(a, b)
            r1 = combined.call(0, gab)  # f(g(a, b))

            # Compute g(f(a), f(b))
            fa = combined.call(0, a_raw)  # f(a)
            fb = combined.call(0, b_raw)  # f(b)
            r2 = combined.call(1, fa, fb)  # g(f(a), f(b))

            if not combined.compare_results(r1, r2):
                counterexamples.append(
                    f"{f_name}({g_name}({a_raw},{b_raw})): {r1}\n\t"
                    f"{g_name}({f_name}({a_raw}),{f_name}({b_raw})): {r2}\n"
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
                "counterexamples": [f"{f_name}({g_name}(a,b)) == {g_name}({f_name}(a),{f_name}(b))\n"],
                "stats": test_stats,
            }
        else:
            return {
                "holds": False,
                "counterexamples": counterexamples,
                "stats": test_stats,
            }
