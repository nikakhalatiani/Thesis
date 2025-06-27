from core.function_under_test import CombinedFunctionUnderTest
from core.properties.property_test import PropertyTest, TestResult, TestStats
from abc import abstractmethod


class _CompositionTest(PropertyTest):
    """Generic base class for tests that check compositional properties between two functions, such as left/right composition and involution."""

    def __init__(
            self, name: str, description: str, function_arity: int, result_index: int
    ):
        super().__init__(
            name=name,
            input_arity=function_arity,
            function_arity=function_arity,
            description=description,
            category="Compositional",
        )

        self.num_functions = 2

        if not (0 <= result_index < function_arity):
            raise ValueError("result_index must be within function arity range")
        self.result_index = result_index

    @abstractmethod
    def compute_results(self, combined: CombinedFunctionUnderTest, *raw_args):
        """Return (output_with_composition, baseline_output, conv_comp, conv_base)."""
        ...

    @abstractmethod
    def format_counterexample(
            self,
            raw_args,
            comp_output,
            base_output,
            f_name: str,
            g_name: str,
            conv_comp,
            conv_base,
    ) -> str:
        """Format a counterexample message."""
        ...

    @abstractmethod
    def success_message(self, f_name: str, g_name: str) -> str:
        """Create a success message when outputs always match."""
        ...

    def test(
            self, combined: CombinedFunctionUnderTest, inputs, max_counterexamples: int
    ) -> TestResult:

        fut_f, fut_g = combined.funcs
        f_name, g_name = fut_f.func.__name__, fut_g.func.__name__
        input_arity = self.input_arity

        valid_inputs = [
            input_set[:input_arity]
            for input_set in inputs
            if len(input_set) >= input_arity
        ]

        if not valid_inputs:
            return {
                "holds": False,
                "counterexamples": ["No valid inputs found\n"],
                "successes": [],
                "stats": {"total_count": 0, "success_count": 0},
            }

        total_tests = 0
        counterexamples = []

        for args in valid_inputs:
            total_tests += 1
            r1, r2, conv_1, conv_2 = self.compute_results(combined, *args)

            if not combined.compare_results(r1, r2):
                counterexamples.append(
                    self.format_counterexample(
                        args, r1, r2, f_name, g_name, conv_1, conv_2
                    )
                )
                if len(counterexamples) >= max_counterexamples:
                    break

        # Build result
        test_stats: TestStats = {
            "total_count": total_tests,
            "success_count": total_tests - len(counterexamples),
        }

        return {
            "holds": not counterexamples,
            "counterexamples": counterexamples,
            "successes": [self.success_message(f_name, g_name)],
            "stats": test_stats,
        }


class LeftCompositionTest(_CompositionTest):
    """Test whether applying f after g yields exactly g's output (left composition/idempotence)."""

    def __init__(self, function_arity=1, result_index=0):
        super().__init__(
            name="LeftComposition",
            description="Checks that applying f after g yields exactly g's output.",
            function_arity=function_arity,
            result_index=result_index,
        )

    def compute_results(self, combined: CombinedFunctionUnderTest, *raw_args):
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
        return f"{f_name}∘{g_name} always equals {g_name} for tested inputs."


class RightCompositionTest(_CompositionTest):
    """Test whether f(g(x)) equals f(x) (right composition property)."""

    def __init__(self, function_arity=1, result_index=0):
        super().__init__(
            name="RightComposition",
            description=(
                "Checks f(..., g(x1..xn), ...) == f(x1..xn) "
                f"by replacing argument {result_index} with g's output"
            ),
            function_arity=function_arity,
            result_index=result_index,
        )

    def compute_results(self, combined: CombinedFunctionUnderTest, *raw_args):
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

    def success_message(self, f_name, g_name):
        return f"{f_name}∘{g_name} always equals {f_name} for tested inputs."


class InvolutionTest(_CompositionTest):
    """Test that f(g(x...)) returns original at position (involution)."""

    def __init__(self, function_arity=1, result_index=0):
        super().__init__(
            name="Involution",
            description="Checks that f after g returns the original argument at index.",
            function_arity=function_arity,
            result_index=result_index,
        )

    def compute_results(self, combined: CombinedFunctionUnderTest, *raw_args):
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
        expected = combined.convert_args(
            0, *raw_args, arg_converter=fut_f.arg_converter
        )[self.result_index]
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

        return f"{f_name}({', '.join(map(str, fg_args))}): {r1}\n\t" f"Expected: {r2}\n"

    def success_message(self, f_name, g_name):
        return f"{f_name}∘{g_name} returns the original argument at position {self.result_index} for all inputs."


class _DistributivityTest(PropertyTest):
    """Generic base class for distributivity tests, checking if one function distributes over another (e.g., f(x, g(y, z)) == g(f(x, y), f(x, z)))."""

    def __init__(self, name: str, description: str):
        super().__init__(
            name=name,
            input_arity=3,
            function_arity=2,
            description=description,
            category="Compositional",
        )
        self.num_functions = 2

    @abstractmethod
    def compute_results(self, combined: CombinedFunctionUnderTest, a, b, c):
        """Compute the pair of results (r1, r2) to compare."""
        ...

    @abstractmethod
    def format_counterexample(self, a, b, c, r1, r2, f_name, g_name):
        """Format a counterexample message on failure."""
        ...

    @abstractmethod
    def success_message(self, f_name, g_name) -> str:
        """Message to use when the property holds for all inputs."""
        ...

    def test(
            self, combined: CombinedFunctionUnderTest, inputs, max_counterexamples: int
    ) -> TestResult:
        fut_f, fut_g = combined.funcs
        f_name, g_name = fut_f.func.__name__, fut_g.func.__name__
        input_arity = self.input_arity

        valid_inputs = [
            inp[:input_arity] for inp in inputs if len(inp) >= input_arity
        ]
        if not valid_inputs:
            return {
                "holds": False,
                "counterexamples": ["No valid inputs found"],
                "successes": [],
                "stats": {"total_count": 0, "success_count": 0},
            }

        total_tests = 0
        counterexamples = []
        for a, b, c in valid_inputs:
            total_tests += 1
            r1, r2 = self.compute_results(combined, a, b, c)
            if not combined.compare_results(r1, r2):
                counterexamples.append(
                    self.format_counterexample(a, b, c, r1, r2, f_name, g_name)
                )
                if len(counterexamples) >= max_counterexamples:
                    break

        stats: TestStats = {
            "total_count": total_tests,
            "success_count": total_tests - len(counterexamples),
        }

        return {
            "holds": not counterexamples,
            "counterexamples": counterexamples,
            "successes": [self.success_message(f_name, g_name)],
            "stats": stats,
        }


class LeftDistributivityTest(_DistributivityTest):
    """Test whether a function is left-distributive over another function."""

    def __init__(self):
        super().__init__(
            name="Left Distributivity",
            description="Tests left distributivity: f(a, g(b, c)) == g(f(a, b), f(a, c))",
        )

    def compute_results(self, combined, a, b, c):
        fut_f, fut_g = combined.funcs
        # f(a, g(b, c))
        inner_bc = combined.call(1, *combined.convert_args(1, b, c, arg_converter=fut_g.arg_converter))
        r1 = combined.call(0, *combined.convert_args(0, a, inner_bc, arg_converter=fut_f.arg_converter))

        # g(f(a, b), f(a, c))
        left = combined.call(0, *combined.convert_args(0, a, b, arg_converter=fut_f.arg_converter))
        right = combined.call(0, *combined.convert_args(0, a, c, arg_converter=fut_f.arg_converter))
        r2 = combined.call(1, *combined.convert_args(1, left, right, arg_converter=fut_g.arg_converter))
        return r1, r2

    def format_counterexample(self, a, b, c, r1, r2, f_name, g_name):
        return (
            f"{f_name}({a}, {g_name}({b}, {c})): {r1}\n\t"
            f"{g_name}({f_name}({a}, {b}), {f_name}({a}, {c})): {r2}\n"
        )

    def success_message(self, f_name, g_name) -> str:
        return f"{f_name}(a, {g_name}(b, c)) == {g_name}({f_name}(a, b), {f_name}(a, c)) for all tested inputs\n"


class RightDistributivityTest(_DistributivityTest):
    """Test whether a function is right-distributive over another function."""

    def __init__(self):
        super().__init__(
            name="Right Distributivity",
            description="Tests right distributivity: f(g(a, b), c) == g(f(a, c), f(b, c))",
        )

    def compute_results(self, combined, a, b, c):
        fut_f, fut_g = combined.funcs
        # f(g(a, b), c)
        inner_ab = combined.call(1, *combined.convert_args(1, a, b, arg_converter=fut_g.arg_converter))
        r1 = combined.call(0, *combined.convert_args(0, inner_ab, c, arg_converter=fut_f.arg_converter))

        # g(f(a, c), f(b, c))
        left = combined.call(0, *combined.convert_args(0, a, c, arg_converter=fut_f.arg_converter))
        right = combined.call(0, *combined.convert_args(0, b, c, arg_converter=fut_f.arg_converter))
        r2 = combined.call(1, *combined.convert_args(1, left, right, arg_converter=fut_g.arg_converter))
        return r1, r2

    def format_counterexample(self, a, b, c, r1, r2, f_name, g_name):
        return (
            f"{f_name}({g_name}({a}, {b}), {c}): {r1}\n\t"
            f"{g_name}({f_name}({a}, {c}), {f_name}({b}, {c})): {r2}\n"
        )

    def success_message(self, f_name, g_name) -> str:
        return f"{f_name}({g_name}(a, b), c) == {g_name}({f_name}(a, c), {f_name}(b, c)) for all tested inputs\n"


class DistributivityTest(PropertyTest):
    """Test whether a function is distributive over another function (general distributivity property)."""

    def __init__(self):
        super().__init__(
            name="Distributivity",
            input_arity=3,
            function_arity=2,
            description="Tests both left and right distributivity",
            category="Compositional",
        )
        self.num_functions = 2
        self.left_test = LeftDistributivityTest()
        self.right_test = RightDistributivityTest()

    def test(self, combined, inputs, max_counterexamples) -> TestResult:
        left_res = self.left_test.test(combined, inputs, max_counterexamples)
        right_res = self.right_test.test(combined, inputs, max_counterexamples)
        total_tests = (
                left_res["stats"]["total_count"] + right_res["stats"]["total_count"]
        )
        successes = (
                left_res["stats"]["success_count"] + right_res["stats"]["success_count"]
        )
        all_ce = left_res["counterexamples"] + right_res["counterexamples"]
        both_hold = left_res["holds"] and right_res["holds"]
        if len(all_ce) > max_counterexamples:
            all_ce = all_ce[:max_counterexamples]

        stats: TestStats = {"total_count": total_tests, "success_count": successes}
        return {
            "holds": both_hold,
            "counterexamples": all_ce,
            "successes": left_res["successes"] + right_res["successes"] if both_hold else [],
            "stats": stats,
        }


class AssociativityTest(PropertyTest):
    """Test whether a function is associative, i.e., f(f(x, y), z) == f(x, f(y, z)) for all x, y, z."""

    def __init__(self):
        """Create a new associativity property test.

        Parameters
        function_arity:
            The arity of both functions under test. Defaults to ``2``.
        """
        super().__init__(
            name="Associativity",
            input_arity=3,
            function_arity=2,
            description="Tests if f(a, g(b, c)) equals f(g(a, b), c)",
            category="Compositional",
        )
        self.num_functions = 2

    def test(
            self, combined: CombinedFunctionUnderTest, inputs, max_counterexamples
    ) -> TestResult:
        fut_f, fut_g = combined.funcs
        f_name, g_name = fut_f.func.__name__, fut_g.func.__name__

        input_arity = self.input_arity

        # Filter valid inputs based on arity
        valid_inputs = [inp[:input_arity] for inp in inputs if len(inp) >= input_arity]

        if not valid_inputs:
            return {
                "holds": False,
                "counterexamples": ["Not enough elements provided\n"],
                "successes": [],
                "stats": {"total_count": 0, "success_count": 0},
            }

        # Test associativity for each valid input
        total_tests = 0
        counterexamples = []

        for args in valid_inputs:
            a, b, c = args
            total_tests += 1

            g_bc = combined.call(1, *combined.convert_args(1, b, c, arg_converter=fut_g.arg_converter))
            r1 = combined.call(0, *combined.convert_args(0, a, g_bc, arg_converter=fut_f.arg_converter))

            g_ab = combined.call(1, *combined.convert_args(1, a, b, arg_converter=fut_g.arg_converter))
            r2 = combined.call(0, *combined.convert_args(0, g_ab, c, arg_converter=fut_f.arg_converter))

            if not combined.compare_results(r1, r2):
                counterexamples.append(
                    f"{f_name}({a}, {g_name}({b}, {c})): {r1}\n\t"
                    f"{f_name}({g_name}({a}, {b}), {c}): {r2}\n"
                )

                if len(counterexamples) >= max_counterexamples:
                    break

        # Build result
        test_stats: TestStats = {
            "total_count": total_tests,
            "success_count": total_tests - len(counterexamples),
        }

        return {
            "holds": not counterexamples,
            "counterexamples": counterexamples,
            "successes": [
                f"{f_name}(a, {g_name}(b, c)) == {f_name}({g_name}(a, b), c) for all tested inputs\n"
            ],
            "stats": test_stats,
        }

# class ScalarHomomorphismTest(PropertyTest):
#     """
#     Test if for two functions f (unary) and g (binary):
#         f(g(k, a)) == g(k, f(a))
#     """
#
#     def __init__(self) -> None:
#         super().__init__(
#             name="ScalarHomomorphism",
#             input_arity=2,
#             function_arity=0,  # overridden in is_applicable
#             description="Checks f(g(k,a)) == g(k, f(a)) for two functions f, g",
#             category="Composition"
#         )
#         self.num_functions = 2
#
#     def is_applicable(self, candidate: CombinedFunctionUnderTest) -> bool:
#         """
#         Applicable exactly when candidate is CombinedFunctionUnderTest of length 2,
#         where:
#           - funcs[0] takes 1 argument (f: A -> B)
#           - funcs[1] takes 2 arguments (g: K x A -> B)
#         """
#         if self.num_functions != len(candidate.funcs):
#             return False
#
#         f_ut, g_ut = candidate.funcs
#         sig_f = inspect.signature(f_ut.func)
#         sig_g = inspect.signature(g_ut.func)
#
#         return (len(sig_f.parameters) == 1) and (len(sig_g.parameters) == 2)
#
#     def test(self, combined: CombinedFunctionUnderTest, inputs, max_counterexamples) -> TestResult:
#         # Unpack f and g
#         f_ut, g_ut = combined.funcs
#         f_name = f_ut.func.__name__
#         g_name = g_ut.func.__name__
#
#         all_elements = frozenset(chain.from_iterable(inputs))
#
#         if len(all_elements) < self.input_arity:
#             return {
#                 "holds": False,
#                 "counterexamples": ["Not enough elements provided\n"],
#                 "stats": {"total_count": 0, "success_count": 0},
#             }
#
#         # Test scalar homomorphism for each valid input
#         total_tests = 0
#         counterexamples = []
#
#         for k, a in combinations(all_elements, 2):
#             total_tests += 1
#
#             # Test f(g(k, a)) == g(k, f(a))
#             # Compute f(g(k, a))
#             ga = combined.call(1, k, a)  # g(k, a)
#             r1 = combined.call(0, ga)  # f(g(k, a))
#
#             # Compute g(k, f(a))
#             fa = combined.call(0, a)  # f(a)
#             r2 = combined.call(1, k, fa)  # g(k, f(a))
#
#             if not combined.compare_results(r1, r2):
#                 counterexamples.append(
#                     f"{f_name}({g_name}({k}, {a})): {r1}\n\t"
#                     f"{g_name}({k}, {f_name}({a})): {r2}\n"
#                 )
#
#                 if len(counterexamples) >= max_counterexamples:
#                     break
#
#         # Build result
#         test_stats: TestStats = {
#             'total_count': total_tests,
#             'success_count': total_tests - len(counterexamples)
#         }
#
#         if not counterexamples:
#             return {
#                 "holds": True,
#                 "counterexamples": [f"{f_name}({g_name}(k, a)) == {g_name}(k, {f_name}(a)) for all tested inputs\n"],
#                 "stats": test_stats,
#             }
#         else:
#             return {
#                 "holds": False,
#                 "counterexamples": counterexamples,
#                 "stats": test_stats,
#             }
#
#
# class HomomorphismTest(PropertyTest):
#     """
#     Test if for two functions f (unary) and g (binary):
#         f(g(a, b)) == g(f(a), f(b))
#     """
#
#     def __init__(self) -> None:
#         super().__init__(
#             name="Homomorphism",
#             input_arity=2,
#             function_arity=0,  # overridden in is_applicable
#             description="Checks f(g(a,b)) == g(f(a), f(b)) for two functions f, g",
#             category="Composition"
#         )
#         self.num_functions = 2
#
#     def is_applicable(self, candidate: CombinedFunctionUnderTest) -> bool:
#         """
#         Applicable exactly when candidate is CombinedFunctionUnderTest of length 2,
#         where:
#           - funcs[0] takes 1 argument (f: A → B)
#           - funcs[1] takes 2 arguments (g: A × A → A or B)
#         """
#         if self.num_functions != len(candidate.funcs):
#             return False
#
#         f_ut, g_ut = candidate.funcs
#         sig_f = inspect.signature(f_ut.func)
#         sig_g = inspect.signature(g_ut.func)
#
#         return (len(sig_f.parameters) == 1) and (len(sig_g.parameters) == 2)
#
#     def test(self, combined: CombinedFunctionUnderTest, inputs, max_counterexamples) -> TestResult:
#         # Unpack f and g
#         f_ut, g_ut = combined.funcs
#         f_name = f_ut.func.__name__
#         g_name = g_ut.func.__name__
#
#         all_elements = frozenset(chain.from_iterable(inputs))
#
#         if len(all_elements) < self.input_arity:
#             return {
#                 "holds": False,
#                 "counterexamples": ["Not enough elements provided\n"],
#                 "stats": {"total_count": 0, "success_count": 0},
#             }
#         # Test homomorphism for each valid input
#         total_tests = 0
#         counterexamples = []
#
#         for a, b in combinations(all_elements, 2):
#             total_tests += 1
#
#             # Test f(g(a, b)) == g(f(a), f(b))
#             # Compute f(g(a, b))
#             gab = combined.call(1, a, b)  # g(a, b)
#             r1 = combined.call(0, gab)  # f(g(a, b))
#
#             # Compute g(f(a), f(b))
#             fa = combined.call(0, a)  # f(a)
#             fb = combined.call(0, b)  # f(b)
#             r2 = combined.call(1, fa, fb)  # g(f(a), f(b))
#
#             if not combined.compare_results(r1, r2):
#                 counterexamples.append(
#                     f"{f_name}({g_name}({a}, {b})): {r1}\n\t"
#                     f"{g_name}({f_name}({a}), {f_name}({b})): {r2}\n"
#                 )
#
#                 if len(counterexamples) >= max_counterexamples:
#                     break
#
#         # Build result
#         test_stats: TestStats = {
#             'total_count': total_tests,
#             'success_count': total_tests - len(counterexamples)
#         }
#
#         if not counterexamples:
#             return {
#                 "holds": True,
#                 "counterexamples": [
#                     f"{f_name}({g_name}(a, b)) == {g_name}({f_name}(a), {f_name}(b)) for all tested inputs\n"],
#                 "stats": test_stats,
#             }
#         else:
#             return {
#                 "holds": False,
#                 "counterexamples": counterexamples,
#                 "stats": test_stats,
#             }
