from core.function_under_test import CombinedFunctionUnderTest
from core.properties.property_test import PropertyTest, TestResult


class DeterminismTest(PropertyTest):
    """Test if a function is deterministic (same input gives same output)"""

    def __init__(self):
        super().__init__(
            name="Determinism",
            input_arity=1,
            function_arity=1,
            description="Tests if function gives same output for same input",
            category="Information"
        )

    def test(self, function: CombinedFunctionUnderTest, inputs: tuple) -> TestResult:
        a = inputs[0]
        fut = function.funcs[0]
        f_name = fut.func.__name__

        # Call a function multiple times with the same input
        results = [function.call(0, a) for _ in range(1000)]

        # Check if all results are the same
        first_result = results[0]
        first_different_result = None
        for idx, r in enumerate(results[1:], start=1):
            if not function.compare_results(first_result, r):
                first_different_result = (idx, r)
                break


        if first_different_result is None:
            return True, f"{f_name}({a}) is deterministic for all tested runs"
        else:
            # If results differ, return the first different result
            idx_diff, diff_val = first_different_result
            return False, (
                f"{f_name}({a}) on run #1: {first_result}\n\t"
                f"{f_name}({a}) on run #{idx_diff+1}: {diff_val}\n"
            )
