"""
Property evaluation module for testing properties against functions.
"""

from util.function_under_test import CombinedFunctionUnderTest
from core.properties.property_test import PropertyTest, TestResult


class PropertyEvaluator:
    """Evaluates properties against functions under test."""

    @staticmethod
    def test_property(
            property_test: PropertyTest,
            function: CombinedFunctionUnderTest,
            input_sets: list,
            max_counterexamples: int
    ) -> TestResult:
        """Test a property against a function with given inputs.

        Args:
            property_test: The property to test
            function: The function(s) to test against
            input_sets: List of input tuples to test with
            max_counterexamples: Maximum number of counterexamples to collect

        Returns:
            TestResult containing the test outcome and statistics
        """
        result = property_test.test(function, input_sets, max_counterexamples)

        return TestResult(
            holds=result['holds'],
            counterexamples=result['counterexamples'][:max_counterexamples],
            successes=result['successes'][:max_counterexamples],
            stats=result['stats'],
            execution_traces=result['execution_traces']
        )
