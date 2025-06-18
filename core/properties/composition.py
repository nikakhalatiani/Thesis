from core.function_under_test import CombinedFunctionUnderTest
from core.properties.property_test import PropertyTest, TestResult, TestStats

import inspect
from itertools import chain, combinations


class _CompositionTest(PropertyTest):
    """Private base for f∘g composition tests."""

    def __init__(self, name: str, description: str,
                 function_arity: int, result_index: int) -> None:
        super().__init__(
            name=name,
            input_arity=function_arity,
            function_arity=function_arity,
            description=description,
            category="Composition"
        )
        self.num_functions = 2
        if not (0 <= result_index < function_arity):
            raise ValueError("result_index must be within function arity range")
        self.result_index = result_index

    def compute_results(self, combined: CombinedFunctionUnderTest, *raw_args):
        """Return a tuple (r1, r2, conv_1, conv_2)."""
        raise NotImplementedError

    def format_counterexample(self, raw_args, r1, r2,
                              f_name: str, g_name: str,
                              conv_f, conv_g) -> str:
        """Format a counterexample message for a failed test."""
        raise NotImplementedError

    def success_message(self, f_name: str, g_name: str) -> str:
        """Default “all good” message; override in subclasses."""
        return f"{self.name} holds for all tested inputs."

    def test(self, combined: CombinedFunctionUnderTest,
             inputs, max_counterexamples: int) -> TestResult:

        fut_f, fut_g = combined.funcs
        f_name, g_name = fut_f.func.__name__, fut_g.func.__name__

        valid_inputs = [input_set[:self.input_arity] for input_set in inputs if len(input_set) >= self.input_arity]

        if not valid_inputs:
            return {
                "holds": False,
                "counterexamples": ["No valid inputs found\n"],
                "stats": {"total_count": 0, "success_count": 0},
            }

        total_tests = 0
        counterexamples = []

        for args in valid_inputs:
            total_tests += 1
            r1, r2, conv_1, conv_2 = self.compute_results(combined, *args)

            if not combined.compare_results(r1, r2):
                counterexamples.append(
                    self.format_counterexample(args, r1, r2,
                                               f_name, g_name,
                                               conv_1, conv_2)
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
                "counterexamples": [self.success_message(f_name, g_name)],
                "stats": test_stats,
            }
        else:
            return {
                "holds": False,
                "counterexamples": counterexamples,
                "stats": test_stats,
            }


class LeftCompositionTest(_CompositionTest):
    """Test f∘g = g: f(g(x1,...,xn)) == g(x1,...,xn)"""

    def __init__(self, function_arity=1, result_index=0):
        super().__init__(
            name="LeftComposition",
            description=(
                "Checks f(..., g(x1..xn), ...) == g(x1..xn) "
                f"by inserting g’s output at position {result_index}"
            ),
            function_arity=function_arity,
            result_index=result_index
        )

    def compute_results(
            self,
            combined: CombinedFunctionUnderTest,
            *raw_args
    ):
        fut_f, fut_g = combined.funcs
        # compute g(x...)
        conv_g = combined.convert_args(1, *raw_args, arg_converter=fut_g.arg_converter)
        r_g = combined.call(1, *conv_g)

        # insert r_g into f at the identity position
        f_args = list(raw_args)
        f_args[self.result_index] = r_g
        conv_fg = combined.convert_args(0, *f_args, arg_converter=fut_f.arg_converter)
        r_fg = combined.call(0, *conv_fg)

        return r_fg, r_g, conv_fg, conv_g

    def format_counterexample(
            self,
            raw_args,
            r1,
            r2,
            f_name: str,
            g_name: str,
            conv_f,
            conv_g,
    ) -> str:
        fg_args = list(conv_f)
        fg_args[self.result_index] = f"{g_name}{tuple(conv_g)}"

        return (
            f"{f_name}({', '.join(map(str, fg_args))}): {r1}\n\t"
            f"{g_name}{tuple(conv_g)}: {r2}\n"
        )

    def success_message(self, f_name, g_name):
        return (
            f"Composition check passed: calling {f_name} after {g_name} on the same arguments "
            f"always yields exactly what {g_name} would produce."
        )


class RightCompositionTest(_CompositionTest):
    """Test f∘g = f: f(g(x1,...,xn)) == f(x1,...,xn)"""

    def __init__(self, function_arity=1, result_index=0):
        super().__init__(
            name="RightComposition",
            description=(
                "Checks f(..., g(x1..xn), ...) == f(x1..xn) "
                f"by replacing argument {result_index} with g’s output"
            ),
            function_arity=function_arity,
            result_index=result_index
        )

    def compute_results(
            self,
            combined: CombinedFunctionUnderTest,
            *raw_args
    ):
        fut_f, fut_g = combined.funcs
        # original f(x...)
        conv_f = combined.convert_args(0, *raw_args, arg_converter=fut_f.arg_converter)
        r_f = combined.call(0, *conv_f)

        # compute g(x...)
        conv_g = combined.convert_args(1, *raw_args, arg_converter=fut_g.arg_converter)
        r_g = combined.call(1, *conv_g)

        # insert r_g into f at result position
        f_args = list(raw_args)
        f_args[self.result_index] = r_g
        conv_fg = combined.convert_args(0, *f_args, arg_converter=fut_f.arg_converter)
        r_fg = combined.call(0, *conv_fg)

        return r_fg, r_f, conv_f, conv_g

    def success_message(self, f_name, g_name):
        return (
            f"Composition check passed: calling {f_name} after {g_name} on the same arguments "
            f"always yields exactly what {f_name} would produce"
        )

    def format_counterexample(
            self,
            raw_args,
            r1,
            r2,
            f_name: str,
            g_name: str,
            conv_f,
            conv_g,
    ) -> str:
        fg_args = list(conv_f)
        fg_args[self.result_index] = f"{g_name}{tuple(conv_g)}"

        return (
            f"{f_name}({', '.join(map(str, fg_args))}): {r1}\n\t"
            f"{f_name}{tuple(conv_f)}: {r2}\n"
        )


class InvolutionTest(_CompositionTest):
    """Test f∘g = id on position result_index: f(g(x1..xn), …) == x_k."""

    def __init__(self, function_arity=1, result_index=0):
        super().__init__(
            name="Involution",
            description=(
                "Checks f(..., g(x1..xn), ...) == x_k (involution on position "
                f"{result_index + 1})"
            ),
            function_arity=function_arity,
            result_index=result_index
        )

    def compute_results(
            self,
            combined: CombinedFunctionUnderTest,
            *raw_args
    ):
        fut_f, fut_g = combined.funcs

        # 1) compute g(x…)
        conv_g = combined.convert_args(1, *raw_args, arg_converter=fut_g.arg_converter)
        r_g = combined.call(1, *conv_g)

        # 2) insert g-result back into position `result_index` and call f
        f_args = list(raw_args)
        f_args[self.result_index] = r_g
        conv_fg = combined.convert_args(0, *f_args, arg_converter=fut_f.arg_converter)
        r_fg = combined.call(0, *conv_fg)

        # expected is the original argument at result_index
        expected = combined.convert_args(0, *raw_args, arg_converter=fut_f.arg_converter)[self.result_index]
        return r_fg, expected, conv_fg, conv_g

    def format_counterexample(
            self,
            raw_args,
            r1,
            r2,
            f_name: str,
            g_name: str,
            conv_fg,
            conv_g,
    ) -> str:
        # build the f(g(...)) arg list
        fg_args = list(conv_fg)
        fg_args[self.result_index] = f"{g_name}{tuple(conv_g)}"

        return (
            f"{f_name}({', '.join(map(str, fg_args))}): {r1}\n\t"
            f"Expected: {r2}\n"
        )

    def success_message(self, f_name, g_name):
        return (
            f"Involution check passed: applying {f_name} after {g_name} "
            f"always returns the original argument at position {self.result_index + 1}."
        )


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
            description="Checks f(g(k,a)) == g(k, f(a)) for two functions f, g",
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

    def test(self, combined: CombinedFunctionUnderTest, inputs, max_counterexamples) -> TestResult:
        # Unpack f and g
        f_ut, g_ut = combined.funcs
        f_name = f_ut.func.__name__
        g_name = g_ut.func.__name__

        all_elements = frozenset(chain.from_iterable(inputs))

        if len(all_elements) < self.input_arity:
            return {
                "holds": False,
                "counterexamples": ["Not enough elements provided\n"],
                "stats": {"total_count": 0, "success_count": 0},
            }

        # Test scalar homomorphism for each valid input
        total_tests = 0
        counterexamples = []

        for k, a in combinations(all_elements, 2):
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
                    f"{f_name}({g_name}({k}, {a})): {r1}\n\t"
                    f"{g_name}({k}, {f_name}({a})): {r2}\n"
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
                "counterexamples": [f"{f_name}({g_name}(k, a)) == {g_name}(k, {f_name}(a)) for all tested inputs\n"],
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
            category="Composition"
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

    def test(self, combined: CombinedFunctionUnderTest, inputs, max_counterexamples) -> TestResult:
        # Unpack f and g
        f_ut, g_ut = combined.funcs
        f_name = f_ut.func.__name__
        g_name = g_ut.func.__name__

        all_elements = frozenset(chain.from_iterable(inputs))

        if len(all_elements) < self.input_arity:
            return {
                "holds": False,
                "counterexamples": ["Not enough elements provided\n"],
                "stats": {"total_count": 0, "success_count": 0},
            }
        # Test homomorphism for each valid input
        total_tests = 0
        counterexamples = []

        for a, b in combinations(all_elements, 2):
            total_tests += 1

            # Test f(g(a, b)) == g(f(a), f(b))
            # Compute f(g(a, b))
            gab = combined.call(1, a, b)  # g(a, b)
            r1 = combined.call(0, gab)  # f(g(a, b))

            # Compute g(f(a), f(b))
            fa = combined.call(0, a)  # f(a)
            fb = combined.call(0, b)  # f(b)
            r2 = combined.call(1, fa, fb)  # g(f(a), f(b))

            if not combined.compare_results(r1, r2):
                counterexamples.append(
                    f"{f_name}({g_name}({a}, {b})): {r1}\n\t"
                    f"{g_name}({f_name}({a}), {f_name}({b})): {r2}\n"
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
                    f"{f_name}({g_name}(a, b)) == {g_name}({f_name}(a), {f_name}(b)) for all tested inputs\n"],
                "stats": test_stats,
            }
        else:
            return {
                "holds": False,
                "counterexamples": counterexamples,
                "stats": test_stats,
            }
