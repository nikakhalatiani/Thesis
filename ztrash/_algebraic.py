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
