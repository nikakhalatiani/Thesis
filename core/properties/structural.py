from abc import abstractmethod

from core.function_under_test import CombinedFunctionUnderTest
from core.properties.property_test import PropertyTest, TestResult, TestStats, ExecutionTrace


class _SwapArgumentsTest(PropertyTest):
    """Generic base class for tests that check the effect of swapping two arguments of a function. Used for commutativity and similar properties."""

    def __init__(
            self,
            name: str,
            description: str,
            function_arity: int,
            swap_indices: tuple[int, int],
    ) -> None:
        # Validate swap_indices
        if not isinstance(swap_indices, (tuple, list)) or len(swap_indices) != 2:
            raise ValueError("swap_indices must be a tuple or list of two indices")
        if not all(isinstance(i, int) for i in swap_indices):
            raise ValueError("swap_indices must contain integers")
        if swap_indices[0] == swap_indices[1]:
            raise ValueError("swap_indices must contain distinct indices")
        if any(i < 0 for i in swap_indices):
            raise ValueError("swap_indices must contain non-negative indices")
        if function_arity < max(swap_indices) + 1:
            raise ValueError("function_arity must be greater than max(swap_indices)")

        super().__init__(
            name=name,
            input_arity=function_arity,
            function_arity=function_arity,
            description=description,
            category="Structural",
        )
        self.swap_indices = swap_indices

    def test(
            self, function: CombinedFunctionUnderTest, inputs, max_counterexamples: int
    ) -> TestResult:
        fut = function.funcs[0]
        f_name = fut.func.__name__
        input_arity = self.input_arity

        # Filter inputs matching the required arity
        valid_inputs = [inp[:input_arity] for inp in inputs if len(inp) >= input_arity]

        if not valid_inputs:
            return {
                "holds": False,
                "counterexamples": ["No valid inputs found\n"],
                "successes": [],
                "stats": {"total_count": 0, "success_count": 0},
                "execution_traces": [],
            }

        orig_conv = list(fut.arg_converter)
        total_tests = 0
        counterexamples: list[str] = []
        execution_traces: list[ExecutionTrace] = []

        for args in valid_inputs:
            # Create swapped argument list
            swapped = list(args)
            i, j = self.swap_indices
            swapped[i], swapped[j] = swapped[j], swapped[i]

            swapped_conv = orig_conv.copy()
            if max(self.swap_indices) < len(swapped_conv):
                swapped_conv[i], swapped_conv[j] = swapped_conv[j], swapped_conv[i]

            # Convert and call
            conv_args = function.convert_args(0, *args, arg_converter=orig_conv)
            conv_swapped = function.convert_args(
                0, *swapped, arg_converter=swapped_conv
            )
            r1 = function.call(0, *conv_args)
            r2 = function.call(0, *conv_swapped)

            comparison = function.compare_results(r1, r2)
            execution_traces.append(
                {
                    "input": tuple(args),
                    "comparison_result": comparison,
                    "property_name": self.name,
                }
            )

            total_tests += 1
            if not comparison:
                counterexamples.append(
                    f"{f_name}{tuple(conv_args)}: {r1}\n\t"
                    f"{f_name}{tuple(conv_swapped)}: {r2}\n"
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
            "successes": [
                f"Swapping arguments at positions {self.swap_indices} yields same result for all tested inputs\n"
            ] if not counterexamples else [],
            "stats": stats,
            "execution_traces": execution_traces,
        }


class CommutativityTest(_SwapArgumentsTest):
    """Test whether swapping two arguments of a function yields the same result (commutativity)."""

    def __init__(
            self, function_arity: int = 2, swap_indices: tuple[int, int] = (0, 1)
    ) -> None:
        # Ensure basic validity preconditions
        if function_arity < 2:
            raise ValueError("function_arity must be at least 2 for commutativity test")
        super().__init__(
            name="Commutativity",
            description="Tests if swapping two arguments yields the same result",
            function_arity=function_arity,
            swap_indices=swap_indices,
        )


class _CandidateElementTest(PropertyTest):
    """Base class for tests that check for special elements (identity or absorbing) at specific argument positions in a function."""

    def __init__(
            self,
            name: str,
            description: str,
            function_arity: int,
            element_positions: list[int],
            target_positions: list[int],
    ):
        super().__init__(
            name=name,
            input_arity=function_arity,
            function_arity=function_arity,
            description=description,
            category="Structural",
        )
        if len(element_positions) != len(target_positions):
            raise ValueError(
                "element_positions and target_positions lengths must match"
            )

        self.element_positions = list(element_positions)
        self.target_positions = list(target_positions)

    def _extract_candidates(self, valid_inputs, orig_conv, default_conv):
        """Extract unique candidates and their converters from inputs."""
        candidates = set()
        converter_map = {}

        # Scan all inputs at positions where we expect to find special elements
        for raw in valid_inputs:
            for pos in self.element_positions:
                if pos < len(raw):
                    val = raw[pos]
                    candidates.add(val)
                    # Map each unique candidate to its converter (based on position found)
                    if val not in converter_map:
                        conv = orig_conv[pos] if pos < len(orig_conv) else default_conv
                        converter_map[val] = conv

        return candidates, converter_map

    @staticmethod
    def _build_test_converter(orig_conv, pos, candidate_conv, default_conv):
        """Build a converter list with the candidate converter at the specified position."""
        if pos < len(orig_conv):
            # Replace converter at existing position
            return orig_conv[:pos] + [candidate_conv] + orig_conv[pos + 1:]
        else:
            # Extend converter list to reach the position
            padding_needed = pos - len(orig_conv)
            return orig_conv + [default_conv] * padding_needed + [candidate_conv]

    def _test_single_case(
            self,
            combined,
            raw_args,
            candidate,
            pos,
            target,
            candidate_conv,
            orig_conv,
            default_conv,
    ):
        """Test a single candidate-position-input combination."""
        # Create test arguments with candidate at specified position
        args = list(raw_args)
        args[pos] = candidate

        # Build converter list that preserves candidate's type
        test_conv = self._build_test_converter(orig_conv, pos, candidate_conv, default_conv)

        # Convert arguments and execute function
        conv_args = combined.convert_args(0, *args, arg_converter=test_conv)
        result = combined.call(0, *conv_args)

        # Expected result is the value at the target position
        expected = conv_args[target]

        return result, expected, conv_args

    def _validate_candidate(
            self,
            combined,
            candidate,
            valid_inputs,
            converter_map,
            orig_conv,
            default_conv,
            execution_traces: list[ExecutionTrace],
    ):
        """Validate a single candidate across all inputs and positions."""
        fut = combined.funcs[0]
        candidate_conv = converter_map[candidate]
        counterexamples = []
        test_count = 0

        for raw_args in valid_inputs:
            for pos, target in zip(self.element_positions, self.target_positions):
                result, expected, conv_args = self._test_single_case(
                    combined,
                    raw_args,
                    candidate,
                    pos,
                    target,
                    candidate_conv,
                    orig_conv,
                    default_conv,
                )
                test_count += 1

                comparison = combined.compare_results(result, expected)
                execution_traces.append(
                    {
                        "input": tuple(raw_args),
                        "comparison_result": comparison,
                        "property_name": self.name,
                    }
                )

                if not comparison:
                    counterexamples.append(
                        f"{fut.func.__name__}{tuple(conv_args)}: {result}\n\t"
                        f"Expected: {expected}\n"
                    )
                    return False, counterexamples, test_count

        # All tests passed - candidate is valid
        return True, [], test_count

    def test(
            self, function: CombinedFunctionUnderTest, inputs, max_counterexamples: int
    ) -> TestResult:
        fut = function.funcs[0]
        orig_conv = list(fut.arg_converter)
        input_arity = self.input_arity
        default_conv = orig_conv[-1] if orig_conv else fut._smart_converter

        # Pre-filter valid inputs
        valid_inputs = [inp[:input_arity] for inp in inputs if len(inp) >= input_arity]
        if not valid_inputs:
            return {
                "holds": False,
                "counterexamples": ["No valid inputs found\n"],
                "successes": [],
                "stats": {"total_count": 0, "success_count": 0},
                "execution_traces": [],
            }

        # Extract candidates
        candidates, converter_map = self._extract_candidates(
            valid_inputs, orig_conv, default_conv
        )
        if not candidates:
            return {
                "holds": False,
                "counterexamples": ["No valid candidates found\n"],
                "successes": [],
                "stats": {"total_count": 0, "success_count": 0},
                "execution_traces": [],
            }

        # Test each candidate
        valid_candidates = []
        all_counterexamples = []
        total_tests = 0
        execution_traces: list[ExecutionTrace] = []

        for candidate in candidates:
            is_valid, counterexamples, test_count = self._validate_candidate(
                function,
                candidate,
                valid_inputs,
                converter_map,
                orig_conv,
                default_conv,
                execution_traces,
            )
            total_tests += test_count

            if is_valid:
                valid_candidates.append(candidate)
            else:
                all_counterexamples.extend(counterexamples)

        # Prepare final result
        stats: TestStats = {
            "total_count": total_tests,
            "success_count": total_tests if valid_candidates else 0,
        }

        return {
            "holds": bool(valid_candidates),
            "counterexamples": all_counterexamples,
            "successes": [self.success_message(c, fut.func.__name__) for c in
                          valid_candidates],
            "stats": stats,
            "execution_traces": execution_traces,
        }

    @abstractmethod
    def success_message(self, candidate, f_name) -> str:
        ...


class LeftIdentityElementTest(_CandidateElementTest):
    """Test for left identity: f(e, a, ...) == a"""

    def __init__(
            self,
            function_arity: int = 2,
            identity_position: int = 0,
            target_position: int = 1,
    ):
        super().__init__(
            name="LeftIdentityElement",
            description=f"Checks f(e, a, ...) == a at pos {identity_position}->{target_position}",
            function_arity=function_arity,
            element_positions=[identity_position],
            target_positions=[target_position],
        )

    def success_message(self, candidate, f_name) -> str:
        return (
            f"{candidate} is a right identity element\n\t"
            f"{f_name}({candidate}, x) = x\n"
        )


class RightIdentityElementTest(_CandidateElementTest):
    """Test for right identity: f(a, e) == a"""

    def __init__(
            self,
            function_arity: int = 2,
            identity_position: int = 1,
            target_position: int = 0,
    ):
        super().__init__(
            name="RightIdentityElement",
            description=f"Checks f(a, e) == a at pos {identity_position}->{target_position}",
            function_arity=function_arity,
            element_positions=[identity_position],
            target_positions=[target_position],
        )

    def success_message(self, candidate, f_name) -> str:
        return (
            f"{candidate} is a right identity element\n\t"
            f"{f_name}(x, {candidate}) = x\n"
        )


class IdentityElementTest(_CandidateElementTest):
    """Test for two-sided identity elements."""

    def __init__(
            self,
            function_arity: int = 2,
            positions: list[int] = (0, 1),
            targets: list[int] = (1, 0),
    ):
        super().__init__(
            name="IdentityElement",
            description=f"Checks two-sided identity at {positions}->{targets}",
            function_arity=function_arity,
            element_positions=list(positions),
            target_positions=list(targets),
        )

    def success_message(self, candidate, f_name) -> str:
        return (
            f"{candidate} is a two-sided identity element\n\t"
            f"{f_name}({candidate}, x) = x and {f_name}(x, {candidate}) = x\n"
        )


class LeftAbsorbingElementTest(_CandidateElementTest):
    """Test for left absorbing: f(z, a, ...) == z"""

    def __init__(
            self,
            function_arity: int = 2,
            absorbing_position: int = 0,
            target_position: int = 0,
    ):
        super().__init__(
            name="LeftAbsorbingElement",
            description=f"Checks absorbing element at pos {absorbing_position}->{target_position}",
            function_arity=function_arity,
            element_positions=[absorbing_position],
            target_positions=[target_position],
        )

    def success_message(self, candidate, f_name) -> str:
        return (
            f"{candidate} is a left absorbing element\n\t"
            f"{f_name}({candidate}, x) = {candidate}\n"
        )


class RightAbsorbingElementTest(_CandidateElementTest):
    """Test for right absorbing: f(a, z) == z"""

    def __init__(
            self,
            function_arity: int = 2,
            absorbing_position: int = 1,
            target_position: int = 1,
    ):
        super().__init__(
            name="RightAbsorbingElement",
            description=f"Checks absorbing element at pos {absorbing_position}->{target_position}",
            function_arity=function_arity,
            element_positions=[absorbing_position],
            target_positions=[target_position],
        )

    def success_message(self, candidate, f_name) -> str:
        return (
            f"{candidate} is a right absorbing element\n\t"
            f"{f_name}(x, {candidate}) = {candidate}\n"
        )


class AbsorbingElementTest(_CandidateElementTest):
    """Test for two-sided absorbing elements."""

    def __init__(
            self,
            function_arity: int = 2,
            positions: list[int] = (0, 1),
            targets: list[int] = (0, 1),
    ):
        super().__init__(
            name="AbsorbingElement",
            description=f"Checks two-sided absorbing at {positions}->{targets}",
            function_arity=function_arity,
            element_positions=list(positions),
            target_positions=list(targets),
        )

    def success_message(self, candidate, f_name) -> str:
        return (
            f"{candidate} is a two-sided absorbing element\n\t"
            f"{f_name}({candidate}, x) = {candidate} and {f_name}(x, {candidate}) = {candidate}\n"
        )

# class TypePreservationTest(PropertyTest):
#     """Test if function preserves input type"""
#
#     def __init__(self):
#         super().__init__(
#             name="Type Preservation",
#             input_arity=1,
#             function_arity=1,
#             description="Tests if function preserves the type of input",
#             category="Structural"
#         )
#
#     def test(self, function: CombinedFunctionUnderTest, inputs, max_counterexamples) -> TestResult:
#         fut = function.funcs[0]
#         f_name = fut.func.__name__
#
#         all_elements = frozenset(chain.from_iterable(inputs))
#
#         if len(all_elements) < self.input_arity:
#             return {
#                 "holds": False,
#                 "counterexamples": ["Not enough elements provided\n"],
#                 "stats": {"total_count": 0, "success_count": 0},
#             }
#         # Test type preservation for each valid input
#         total_tests = 0
#         counterexamples = []
#
#         for a in all_elements:
#             total_tests += 1
#             a = fut.arg_converter(a)
#             result = function.call(0, a)
#
#             if type(result) != type(a):
#                 counterexamples.append(
#                     f"Input type: {type(a).__name__}\n\t"
#                     f"Output type: {type(result).__name__}\n"
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
#                 "counterexamples": [f"{f_name} preserves input type for all tested inputs\n"],
#                 "stats": test_stats,
#             }
#         else:
#             return {
#                 "holds": False,
#                 "counterexamples": counterexamples,
#                 "stats": test_stats,
#             }

# TODO think about how to integrate try except into the logic
# class SizePreservationTest(PropertyTest):
#     """
#     Test if a unary function f preserves the size/length of its input where:
#         len(f(x)) == len(x)
#     """
#
#     def __init__(self) -> None:
#         super().__init__(
#             name="SizePreservation",
#             input_arity=1,
#             function_arity=1,
#             description="Checks whether function preserves size/length of input",
#             category="Structural"
#         )
#
#     def test(self, function: CombinedFunctionUnderTest, inputs, early_stopping) -> TestResult:
#         fut = function.funcs[0]
#         f_name = fut.func.__name__
#         input_arity = self.input_arity
#
#         # Extract all unique elements from valid input tuples
#         all_elements = set()
#         all_elements.update(element for input_set in inputs if len(input_set) >= input_arity for element in input_set)
#
#         if not all_elements:
#             return {
#                 "holds": False,
#                 "counterexamples": [f"SizePreservation test failed: No valid input sets provided for {f_name}\n"],
#                 "stats": {"total_count": 0, "success_count": 0},
#             }
#
#         # Setup conversion cache
#         conversion_cache = {}
#
#         def cached_convert(raw_val):
#             if raw_val not in conversion_cache:
#                 conversion_cache[raw_val] = fut.arg_converter(raw_val)
#             return conversion_cache[raw_val]
#
#         # Test each element for size preservation
#         total_tests = 0
#         size_preserved = []
#         counterexamples = []
#         skipped_items = []
#
#         for candidate in all_elements:
#             total_tests += 1
#             converted_input = cached_convert(candidate)
#             result = function.call(0, candidate)
#
#             try:
#                 input_len = len(converted_input)
#                 output_len = len(result)
#
#                 if input_len == output_len:
#                     size_preserved.append(f"{f_name}({candidate}): size preserved ({input_len})\n")
#                 else:
#                     counterexamples.append(
#                         f"{f_name}({candidate}): input size {input_len} → output size {output_len}\n"
#                     )
#                     if early_stopping:
#                         break
#
#             except TypeError:
#                 # Skip items where length is not applicable
#                 skipped_items.append(f"{f_name}({candidate}): size test skipped (length not applicable)\n")
#
#         # Build result
#         successful_tests = len(size_preserved)
#
#         # If we have skipped items but no failures, we still consider it a success
#         # since the property holds for all testable inputs
#         has_counterexamples = len(counterexamples) > 0
#
#         test_stats: TestStats = {
#             'total_count': total_tests,
#             'success_count': successful_tests + len(skipped_items) if not has_counterexamples else successful_tests
#         }
#
#         # Combine results for reporting
#         all_results = size_preserved + skipped_items
#
#         if not has_counterexamples and (size_preserved or skipped_items):
#             return {
#                 "holds": True,
#                 "counterexamples": all_results,
#                 "stats": test_stats,
#             }
#         else:
#             return {
#                 "holds": False,
#                 "counterexamples": counterexamples if counterexamples else [
#                     f"No valid inputs for size preservation test on {f_name}\n"],
#                 "stats": test_stats,
#             }
