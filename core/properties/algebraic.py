from collections.abc import Hashable

from core.function_under_test import CombinedFunctionUnderTest
from core.properties.property_test import TestResult, TestStats, PropertyTest


class CommutativityTest(PropertyTest):
    """Test if swapping two arguments of ``f`` yields the same result."""

    def __init__(self, function_arity: int = 2,
                 swap_indices: tuple[int, int] = (0, 1)) -> None:
        """Create a new commutativity property test.

        Parameters
        function_arity:
            The number of arguments ``f`` accepts. Defaults to ``2``.
        swap_indices:
            A pair of argument positions that should be swapped when calling
            ``f``. Defaults to ``(0, 1)`` to check ``f(a, b) equals f(b, a)``.
        """

        if len(swap_indices) != 2 or swap_indices[0] == swap_indices[1]:
            raise ValueError("swap_indices must be a tuple of two distinct indices")

        if function_arity < 2:
            raise ValueError("function_arity must be at least 2 for commutativity test")

        super().__init__(
            name="Commutativity",
            input_arity=function_arity,
            function_arity=function_arity,
            description="Tests if swapping two arguments yields the same result",
            category="Algebraic"
        )
        self.swap_indices = swap_indices

    def test(self, function: CombinedFunctionUnderTest, inputs, max_counterexamples) -> TestResult:
        fut = function.funcs[0]
        f_name = fut.func.__name__

        input_arity = self.input_arity

        # Gather all unique elements from valid input sets
        valid_inputs = [inp[:input_arity] for inp in inputs if len(inp) >= input_arity]

        if not valid_inputs:
            return {
                "holds": False,
                "counterexamples": ["No valid inputs found\n"],
                "stats": {"total_count": 0, "success_count": 0},
            }

        total_tests = 0
        counterexamples = []

        for args in valid_inputs:
            swapped = list(args)
            if max(self.swap_indices) >= len(swapped):
                continue
            # Swap the specified indices
            swapped[self.swap_indices[0]], swapped[self.swap_indices[1]] = \
                swapped[self.swap_indices[1]], swapped[self.swap_indices[0]]

            arg_converter = fut.arg_converter
            rev_converter = list(reversed(arg_converter))

            conv_args = function.convert_args(0, *args, arg_converter=arg_converter)
            conv_swapped = function.convert_args(0, *swapped, arg_converter=rev_converter)

            r1 = function.call(0, *conv_args)
            r2 = function.call(0, *conv_swapped)
            total_tests += 1

            if not function.compare_results(r1, r2):
                counterexamples.append(
                    f"{f_name}{tuple(conv_args)}: {r1}\n\t"
                    f"{f_name}{tuple(conv_swapped)}: {r2}\n"
                )
                if len(counterexamples) >= max_counterexamples:
                    break

        test_stats: TestStats = {
            "total_count": total_tests,
            "success_count": total_tests - len(counterexamples)
        }

        if total_tests == 0:
            return {
                "holds": False,
                "counterexamples": ["No tests were performed due to inapplicable configuration\n"],
                "stats": test_stats,
            }

        if not counterexamples:
            return {
                "holds": True,
                "counterexamples": [
                    f"Swapping arguments at positions {self.swap_indices} yields same result for all tested inputs\n"],
                "stats": test_stats,
            }
        else:
            return {
                "holds": False,
                "counterexamples": counterexamples,
                "stats": test_stats,
            }


class AssociativityTest(PropertyTest):
    """Test if ``f(a, f(b, c))`` equals ``f(f(a, b), c)``."""

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
            category="Algebraic"
        )
        self.num_functions = 2

    def test(self, combined: CombinedFunctionUnderTest, inputs, max_counterexamples) -> TestResult:
        fut_f, fut_g = combined.funcs
        f_name, g_name = fut_f.func.__name__, fut_g.func.__name__

        input_arity = self.input_arity

        # Filter valid inputs based on arity
        valid_inputs = [inp[:input_arity] for inp in inputs if len(inp) >= input_arity]

        if not valid_inputs:
            return {
                "holds": False,
                "counterexamples": ["Not enough elements provided\n"],
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

            # 5) compare
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


class _DistributivityTest(PropertyTest):
    """Private base class for distributivity tests."""

    def __init__(self, name: str, description: str):
        super().__init__(
            name=name,
            input_arity=3,
            function_arity=2,
            description=description,
            category="Algebraic"
        )
        self.num_functions = 2

    def compute_results(self, combined: CombinedFunctionUnderTest, a, b, c):
        """Compute (r1, r2) for given inputs; to be implemented by subclasses."""
        raise NotImplementedError

    def format_counterexample(self, a, b, c, r1, r2, f_name, g_name):
        """Format counterexample message; to be implemented by subclasses."""
        raise NotImplementedError

    def test(self, combined: CombinedFunctionUnderTest, inputs, max_counterexamples) -> TestResult:
        fut_f, fut_g = combined.funcs
        f_name, g_name = fut_f.func.__name__, fut_g.func.__name__
        valid_inputs = [inp[:self.input_arity] for inp in inputs if len(inp) >= self.input_arity]

        if not valid_inputs:
            return {
                "holds": False,
                "counterexamples": ["No valid inputs found\n"],
                "stats": {"total_count": 0, "success_count": 0},
            }

        total_tests = 0
        counterexamples = []
        for args in valid_inputs:
            a, b, c = args
            total_tests += 1
            r1, r2 = self.compute_results(combined, a, b, c)

            if not combined.compare_results(r1, r2):
                counterexamples.append(
                    self.format_counterexample(a, b, c, r1, r2, f_name, g_name)
                )
                if len(counterexamples) >= max_counterexamples:
                    break

        stats: TestStats = {"total_count": total_tests, "success_count": total_tests - len(counterexamples)}

        if not counterexamples:
            if self.name == "Left Distributivity":
                result = f"{f_name}(a, {g_name}(b, c)) == {g_name}({f_name}(a, b), {f_name}(a, c)) for all tested inputs\n"
            else:
                result = f"{f_name}({g_name}(a, b), c) == {g_name}({f_name}(a, c), {f_name}(b, c)) for all tested inputs\n"
            return {
                "holds": True,
                "counterexamples": [result],
                "stats": stats,
            }
        return {"holds": False, "counterexamples": counterexamples, "stats": stats}


class LeftDistributivityTest(_DistributivityTest):
    """Test left distributivity: f(a, g(b, c)) == g(f(a, b), f(a, c))"""

    def __init__(self):
        super().__init__(
            name="Left Distributivity",
            description="Tests left distributivity: f(a, g(b, c)) == g(f(a, b), f(a, c))"
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
        return (f"{f_name}({a}, {g_name}({b}, {c})): {r1}\n\t"
                f"{g_name}({f_name}({a}, {b}), {f_name}({a}, {c})): {r2}\n")


class RightDistributivityTest(_DistributivityTest):
    """Test right distributivity: f(g(a, b), c) == g(f(a, c), f(b, c))"""

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
        return (f"{f_name}({g_name}({a}, {b}), {c}): {r1}\n\t"
                f"{g_name}({f_name}({a}, {c}), {f_name}({b}, {c})): {r2}\n")


class DistributivityTest(PropertyTest):
    """Test two-sided distributivity: both left and right distributivity must hold"""

    def __init__(self):
        super().__init__(
            name="Distributivity",
            input_arity=3,
            function_arity=2,
            description="Tests both left and right distributivity",
            category="Algebraic"
        )
        self.num_functions = 2
        self.left_test = LeftDistributivityTest()
        self.right_test = RightDistributivityTest()

    def test(self, combined, inputs, max_counterexamples) -> TestResult:
        left_result = self.left_test.test(combined, inputs, max_counterexamples)
        right_result = self.right_test.test(combined, inputs, max_counterexamples)
        both_hold = left_result["holds"] and right_result["holds"]

        combined_stats: TestStats = {
            'total_count': left_result["stats"]["total_count"] + right_result["stats"]["total_count"],
            'success_count': left_result["stats"]["success_count"] + right_result["stats"]["success_count"]
        }

        all_ce = []
        if not left_result["holds"]:
            all_ce.extend([f"Left distributivity failed:\n\t{ce}" for ce in left_result["counterexamples"]])
        if not right_result["holds"]:
            all_ce.extend([f"Right distributivity failed:\n\t{ce}" for ce in right_result["counterexamples"]])

        if len(all_ce) > max_counterexamples:
            all_ce = all_ce[:max_counterexamples]

        if both_hold:
            fut_f, fut_g = combined.funcs
            f_name, g_name = fut_f.func.__name__, fut_g.func.__name__
            return {
                "holds": True,
                "counterexamples": [
                    f"Two-sided distributivity holds for {f_name} and {g_name}:\n\t"
                    f"Left: {f_name}(a, {g_name}(b, c)) == {g_name}({f_name}(a, b), {f_name}(a, c))\n\t"
                    f"Right: {f_name}({g_name}(a, b), c) == {g_name}({f_name}(a, c), {f_name}(b, c))\n"
                ],
                "stats": combined_stats,
            }
        else:
            return {"holds": False, "counterexamples": all_ce, "stats": combined_stats}


class _CandidateElementTest(PropertyTest):
    """Private base class for candidate element tests (identity or absorbing)."""

    def __init__(
            self,
            name: str,
            description: str,
            function_arity: int,
            element_positions: list[int],
            target_positions: list[int]
    ):
        super().__init__(
            name=name,
            input_arity=function_arity,
            function_arity=function_arity,
            description=description,
            category="Algebraic"
        )
        if len(element_positions) != len(target_positions):
            raise ValueError("element_positions and target_positions lengths must match")
        self.element_positions = element_positions
        self.target_positions = target_positions

    def test(
            self,
            combined: CombinedFunctionUnderTest,
            inputs,
            max_counterexamples: int
    ) -> TestResult:
        fut = combined.funcs[0]
        orig_conv = list(fut.arg_converter)

        # determine default converter exactly as convert_args does
        if orig_conv:
            default_conv = orig_conv[-1]
        else:
            default_conv = fut._smart_converter  # fallback if no converters

        # filter valid inputs and collect candidate values
        valid_inputs = [
            inp[: self.function_arity]
            for inp in inputs
            if len(inp) >= self.function_arity
        ]
        candidates = {
            raw[pos]
            for raw in valid_inputs
            for pos in self.element_positions
            if pos < len(raw)
        }

        if not valid_inputs:
            return {
                "holds": False,
                "counterexamples": ["No valid inputs found\n"],
                "stats": {"total_count": 0, "success_count": 0},
            }

        # map each candidate back to its “home” converter
        candidate_to_conv: dict = {}
        for raw in valid_inputs:
            for pos in self.element_positions:
                if pos < len(raw):
                    val = raw[pos]
                    # pick converter[pos] if it exists, else default_conv
                    conv = orig_conv[pos] if pos < len(orig_conv) else default_conv
                    # skip if already mapped
                    candidate_to_conv.setdefault(val, conv)

        counterexamples: list[str] = []
        total_tests = 0

        for raw_args in valid_inputs:
            if not candidates:
                break
            to_remove = set()

            for candidate in candidates:
                for pos, target in zip(self.element_positions, self.target_positions):
                    args = list(raw_args)
                    args[pos] = candidate

                    # build a fresh copy of the converter list
                    test_conv = orig_conv.copy()
                    # pad if pos is beyond current length
                    if pos >= len(test_conv):
                        test_conv.extend([default_conv] * (pos + 1 - len(test_conv)))
                    # swap in the candidate’s original converter
                    test_conv[pos] = candidate_to_conv.get(candidate, default_conv)

                    # convert & call
                    conv_args = combined.convert_args(0, *args, arg_converter=test_conv)
                    result = combined.call(0, *conv_args)
                    expected = conv_args[target]
                    total_tests += 1

                    if not combined.compare_results(result, expected):
                        to_remove.add(candidate)
                        counterexamples.append(
                            f"{fut.func.__name__}{tuple(conv_args)}: {result}\n\t"
                            f"Expected: {expected} (pos {pos}->{target})\n"
                        )
                        break

            candidates -= to_remove

        stats: TestStats = {"total_count": total_tests, "success_count": total_tests if candidates else 0}
        if candidates:
            return {
                "holds": True,
                "counterexamples": [
                    f"{c} is a valid element for {self.name}\n" for c in candidates
                ],
                "stats": stats,
            }
        else:
            return {"holds": False, "counterexamples": counterexamples, "stats": stats}


class LeftIdentityElementTest(_CandidateElementTest):
    """Test for left identity element: f(e, a, ...) == a"""

    def __init__(self, function_arity: int = 2, identity_position: int = 0, target_position: int = 1):
        super().__init__(
            name="LeftIdentityElement",
            description=f"Checks whether f(e, a, ...) = a at pos {identity_position}->{target_position}",
            function_arity=function_arity,
            element_positions=[identity_position],
            target_positions=[target_position]
        )


class RightIdentityElementTest(_CandidateElementTest):
    """Test for right identity element: f(a, e) == a"""

    def __init__(self, function_arity: int = 2, identity_position: int = 1, target_position: int = 0):
        super().__init__(
            name="RightIdentityElement",
            description=f"Checks whether f(a, e) = a at pos {identity_position}->{target_position}",
            function_arity=function_arity,
            element_positions=[identity_position],
            target_positions=[target_position]
        )


class IdentityElementTest(_CandidateElementTest):
    """Test for two-sided identity elements."""

    def __init__(self, function_arity: int = 2, positions: list[int] = (0, 1), targets: list[int] = (1, 0)):
        super().__init__(
            name="IdentityElement",
            description=f"Checks two-sided identity at {positions}->{targets}",
            function_arity=function_arity,
            element_positions=positions,
            target_positions=targets
        )


class GeneralIdentityElementTest(_CandidateElementTest):
    """Test for identity elements at arbitrary positions."""

    def __init__(self, function_arity: int = 2, identity_positions: list[int] | None = None):
        if identity_positions is None:
            identity_positions = list(range(function_arity))
        target_positions = identity_positions[::-1]

        super().__init__(
            name="GeneralIdentityElement",
            description=f"Checks identity at positions {identity_positions}->"
                        f"{target_positions} for arity {function_arity}",
            function_arity=function_arity,
            element_positions=identity_positions,
            target_positions=target_positions
        )


class LeftAbsorbingElementTest(_CandidateElementTest):
    """Test for left absorbing: f(z, a, ...) = z (or target)"""

    def __init__(self, function_arity: int = 2, absorbing_position: int = 0, target_position: int = 0):
        super().__init__(
            name="LeftAbsorbingElement",
            description=f"Checks absorbing element at pos {absorbing_position}->{target_position}",
            function_arity=function_arity,
            element_positions=[absorbing_position],
            target_positions=[target_position]
        )


class RightAbsorbingElementTest(_CandidateElementTest):
    """Test for right absorbing: f(a, z) = z (or target)"""

    def __init__(self, function_arity: int = 2, absorbing_position: int = 1, target_position: int = 1):
        super().__init__(
            name="RightAbsorbingElement",
            description=f"Checks absorbing element at pos {absorbing_position}->{target_position}",
            function_arity=function_arity,
            element_positions=[absorbing_position],
            target_positions=[target_position]
        )


class AbsorbingElementTest(_CandidateElementTest):
    """Test for two-sided absorbing elements."""

    def __init__(self, function_arity: int = 2, positions: list[int] = (0, 1), targets: list[int] = (0, 1)):
        super().__init__(
            name="AbsorbingElement",
            description=f"Checks two-sided absorbing at {positions}->{targets}",
            function_arity=function_arity,
            element_positions=positions,
            target_positions=targets
        )


class GeneralAbsorbingElementTest(_CandidateElementTest):
    """Test for absorbing elements at arbitrary positions."""

    def __init__(self, function_arity: int = 2, absorbing_positions: list[int] | None = None):
        if absorbing_positions is None:
            absorbing_positions = list(range(function_arity))

        target_positions = absorbing_positions
        super().__init__(
            name="GeneralAbsorbingElement",
            description=f"Checks absorbing at positions {absorbing_positions}->{target_positions}",
            function_arity=function_arity,
            element_positions=absorbing_positions,
            target_positions=target_positions
        )


class InjectivityTest(PropertyTest):
    """Test injectivity with configurable function arity and projection strategy"""

    def __init__(self, function_arity: int = 1, projection_func=None):
        """Create a new injectivity test.

        Parameters:
        function_arity:
            The number of arguments the function accepts. Defaults to 1.
        projection_func:
            Optional function to extract comparable values from function results.
            Useful for functions that return complex objects where only part
            should be compared for injectivity.
        """
        super().__init__(
            name="Injectivity",
            input_arity=function_arity,
            function_arity=function_arity,
            description=f"Checks injectivity for {function_arity}-ary function",
            category="Algebraic"
        )
        self.projection_func = projection_func or (lambda x: x)

    @staticmethod
    def _make_hashable(obj):
        """Convert an object to a hashable representation."""
        if isinstance(obj, Hashable):
            return obj
        elif isinstance(obj, set):
            return frozenset(obj)
        elif isinstance(obj, list):
            return tuple(obj)
        elif isinstance(obj, dict):
            return tuple(sorted(obj.items()))
        else:
            return str(obj)

    def test(self, function: CombinedFunctionUnderTest, inputs, max_counterexamples) -> TestResult:
        fut = function.funcs[0]
        f_name = fut.func.__name__

        valid_inputs = {tuple(input_set[:self.function_arity]) for input_set in inputs if
                        len(input_set) >= self.function_arity}

        if not valid_inputs:
            return {
                "holds": False,
                "counterexamples": ["No valid inputs found\n"],
                "stats": {"total_count": 0, "success_count": 0},
            }

        counterexamples = []
        total_tests = 0
        result_map = {}  # Maps projected results to the input that produced them

        for args in valid_inputs:
            total_tests += 1

            # Convert args using the function's argument converter
            conv_args = function.convert_args(0, *args, arg_converter=fut.arg_converter)
            # Call the function with converted args
            result = function.call(0, *conv_args)

            projected_result = self.projection_func(result)
            projected_result = self._make_hashable(projected_result)

            # Check if we've seen this projected result before
            if projected_result in result_map:
                prev_args, prev_result = result_map[projected_result]
                counterexamples.append(
                    f"{f_name}{tuple(conv_args)} = {result}\n\t"
                    f"{f_name}{tuple(prev_args)} = {prev_result}\n")

                if len(counterexamples) >= max_counterexamples:
                    break
            else:
                result_map[projected_result] = (conv_args, result)

        test_stats: TestStats = {
            'total_count': total_tests,
            'success_count': total_tests - len(counterexamples)
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


class FixedPointTest(PropertyTest):
    """Test for fixed points with configurable function arity and comparison index."""

    def __init__(self, function_arity: int = 1, result_index: int = 0):
        """Create a new fixed point test.

        Parameters:
        function_arity:
            The number of arguments the function accepts. Defaults to 1.
        result_index:
            Which argument position to compare with the result for fixed point.
            For f(x) = x, this would be 0. For f(state, value) where we check
            if the state is unchanged, this would be 0.
        """
        super().__init__(
            name="FixedPoint",
            input_arity=function_arity,
            function_arity=function_arity,
            description=f"Checks for fixed points comparing result with argument {result_index}",
            category="Algebraic"
        )
        self.result_index = result_index

    def test(self, function: CombinedFunctionUnderTest, inputs, max_counterexamples) -> TestResult:
        fut = function.funcs[0]
        f_name = fut.func.__name__

        # Extract all unique elements from valid input tuples
        valid_inputs = [input_set[:self.function_arity] for input_set in inputs if
                        len(input_set) >= self.function_arity]

        if not valid_inputs:
            return {
                "holds": False,
                "counterexamples": ["No valid inputs found\n"],
                "stats": {"total_count": 0, "success_count": 0},
            }

        total_tests = 0
        fixed_points = []
        counterexamples = []

        for valid_input in valid_inputs:
            total_tests += 1

            if self.result_index < len(valid_input):
                args = list(valid_input)
                # Convert args using the function's argument converter
                conv_args = function.convert_args(0, *args, arg_converter=fut.arg_converter)
                # Call the function with converted args
                expected = conv_args[self.result_index]
                # Call the function
                result1 = function.call(0, *conv_args)
                # Double-check if result really matches expected
                result2 = function.call(0, *conv_args)

                if function.compare_results(result1, expected) and function.compare_results(result2, expected):
                    fixed_points.append(
                        f"{f_name}{tuple(conv_args)}: {result1} == {conv_args[self.result_index]}\n"
                    )
                else:
                    counterexamples.append(f"{f_name}{tuple(conv_args)}: {result1} ≠ {conv_args[self.result_index]}\n")

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
