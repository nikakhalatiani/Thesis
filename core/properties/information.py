from core.function_under_test import FunctionUnderTest
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

    def test(self, function: FunctionUnderTest, inputs: tuple) -> TestResult:
        a = inputs[0]

        # Call a function multiple times with the same input
        results = [function.call(a) for _ in range(1000)]

        # Check if all results are the same
        first_result = results[0]
        first_different_result = None
        for r in results[1:]:
            if not function.compare_results(first_result, r):
                first_different_result = r
                break

        f_name = function.func.__name__

        if not first_different_result:
            return True, f"{f_name}(a) is deterministic for all tested inputs"
        else:
            # If results differ, return the first different result
            return False, {
                f"{f_name}({a}) on run #{results.index(first_result)+1}: ": first_result,
                f"{f_name}({a}) on run #{results.index(first_different_result)+1}: ": f"{first_different_result}\n"
            }