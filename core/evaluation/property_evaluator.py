from core.function_under_test import CombinedFunctionUnderTest
from core.properties.property_test import PropertyTest, TestResult


class PropertyEvaluator:
    """Evaluate properties on generated inputs."""

    @staticmethod
    def test_property(property_test: PropertyTest, function: CombinedFunctionUnderTest,
                      input_sets: list, max_counterexamples: int) -> TestResult:
        result = property_test.test(function, input_sets, max_counterexamples)
        return TestResult(
            holds=result['holds'],
            counterexamples=result['counterexamples'][:max_counterexamples],
            successes=result['successes'][:max_counterexamples],
            stats=result['stats'],
            execution_traces=result['execution_traces'],
        )