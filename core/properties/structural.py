from core.function_under_test import CombinedFunctionUnderTest
from core.property_tester import PropertyTest, TestResult, TestStats


class TypePreservationTest(PropertyTest):
    """Test if function preserves input type"""

    def __init__(self):
        super().__init__(
            name="Type Preservation",
            input_arity=1,
            function_arity=1,
            description="Tests if function preserves the type of input",
            category="Structural"
        )

    def test(self, function: CombinedFunctionUnderTest, inputs, early_stopping) -> TestResult:
        f_name = function.funcs[0].func.__name__
        input_arity = self.input_arity

        # Filter valid inputs based on arity
        valid_inputs = [input_set for input_set in inputs if len(input_set) >= input_arity]

        if not valid_inputs:
            return {
                "holds": False,
                "counterexamples": [f"Type preservation test failed: No valid input sets provided for {f_name}\n"],
                "stats": {"total_count": 0, "success_count": 0},
            }
        # Test type preservation for each valid input
        total_tests = 0
        counterexamples = []

        for input_set in valid_inputs:
            a = input_set[0]
            total_tests += 1

            result = function.call(0, a)

            if type(result) != type(a):
                counterexamples.append(
                    f"Input type: {type(a).__name__}\n\t"
                    f"Output type: {type(result).__name__}\n"
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
                "counterexamples": [f"{f_name} preserves input type\n"],
                "stats": test_stats,
            }
        else:
            return {
                "holds": False,
                "counterexamples": counterexamples,
                "stats": test_stats,
            }

