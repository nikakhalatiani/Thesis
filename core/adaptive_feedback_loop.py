from typing import Any, Optional
from dataclasses import dataclass, field
from copy import deepcopy
import time

from config.property_inference_config import PropertyInferenceConfig
from config.grammar_config import GrammarConfig
from core.property_inference_engine import PropertyInferenceEngine
from core.properties.property_test import PropertyTest, TestResult
from core.function_under_test import CombinedFunctionUnderTest

from .constraint_inference_engine import (
    ConstraintInferenceModel, InferenceInput, TestCase,
    ConstraintInferenceResult, RuleBasedModel
)


@dataclass
class FeedbackIteration:
    """Records data from one iteration of the feedback loop."""
    iteration: int
    test_result: TestResult
    inferred_constraints: list[str]
    cumulative_constraints: list[str]
    elapsed_time: float
    confidence: float = 1.0
    reasoning: str = ""


@dataclass
class AdaptiveFeedbackResult:
    """Final result of the adaptive feedback loop."""
    success: bool
    iterations: list[FeedbackIteration]
    final_constraints: list[str]
    total_time: float
    final_test_result: Optional[TestResult] = None
    termination_reason: str = ""


class AdaptiveFeedbackLoop:
    """Orchestrates the adaptive feedback loop for property testing."""

    def __init__(
            self,
            config: PropertyInferenceConfig,
            constraint_model: Optional[ConstraintInferenceModel] = None,
            max_iterations: int = 10,
            min_examples_per_iteration: int = 50,
            verbose: bool = True
    ):
        """
        Initialize the adaptive feedback loop.

        Args:
            config: Property inference configuration
            constraint_model: Model for inferring constraints (defaults to RuleBasedModel)
            max_iterations: Maximum number of feedback iterations
            min_examples_per_iteration: Minimum examples to generate per iteration
            verbose: Whether to print progress
        """
        self.config = config
        self.constraint_model = constraint_model or RuleBasedModel()
        self.max_iterations = max_iterations
        self.min_examples_per_iteration = min_examples_per_iteration
        self.verbose = verbose
        self.original_example_count = config.example_count

    def run_adaptive_test(
            self,
            property_test: PropertyTest,
            function: CombinedFunctionUnderTest,
            initial_constraints: Optional[list[str]] = None
    ) -> AdaptiveFeedbackResult:
        """
        Run the adaptive feedback loop for a specific property and function.

        Args:
            property_test: The property to test
            function: The function(s) under test
            initial_constraints: Optional initial constraints

        Returns:
            AdaptiveFeedbackResult with all iteration data
        """
        start_time = time.time()
        iterations = []
        cumulative_constraints = initial_constraints or []

        # Get function names for logging
        func_names = ', '.join(f.func.__name__ for f in function.funcs)

        if self.verbose:
            print(f"\n🔄 Starting adaptive feedback loop")
            print(f"   Property: {property_test.name}")
            print(f"   Function(s): {func_names}")
            print(f"   Max iterations: {self.max_iterations}")

        for iteration in range(1, self.max_iterations + 1):
            iter_start = time.time()

            if self.verbose:
                print(f"\n📍 Iteration {iteration}")
                if cumulative_constraints:
                    print(f"   Current constraints: {cumulative_constraints}")

            # Update grammar with current constraints
            self._update_grammar_constraints(function, cumulative_constraints)

            # Ensure we generate enough examples
            self.config.example_count = max(
                self.min_examples_per_iteration,
                self.original_example_count
            )

            # Run property test
            test_result = self._run_single_test(property_test, function)

            if self.verbose:
                success_rate = (test_result['stats']['success_count'] /
                                test_result['stats']['total_count'] * 100)
                print(f"   Test result: {'✅ PASS' if test_result['holds'] else '❌ FAIL'}")
                print(f"   Success rate: {success_rate:.1f}%")
                print(f"   Tests run: {test_result['stats']['total_count']}")

            # Check if all tests passed
            if test_result['holds']:
                elapsed = time.time() - start_time

                if self.verbose:
                    print(f"\n🎉 All tests passed after {iteration} iteration(s)!")
                    print(f"   Final constraints: {cumulative_constraints or ['None']}")

                return AdaptiveFeedbackResult(
                    success=True,
                    iterations=iterations,
                    final_constraints=cumulative_constraints,
                    total_time=elapsed,
                    final_test_result=test_result,
                    termination_reason="All tests passed"
                )

            # Infer new constraints from test results
            inference_result = self._infer_constraints(
                property_test, function, test_result,
                cumulative_constraints, iteration
            )

            if self.verbose and inference_result.constraints:
                print(f"   Inferred constraints: {inference_result.constraints}")
                print(f"   Confidence: {inference_result.confidence:.2f}")

            # Add new constraints
            new_constraints = [
                c for c in inference_result.constraints
                if c not in cumulative_constraints
            ]

            if not new_constraints:
                if self.verbose:
                    print("   ⚠️  No new constraints inferred")

                # If no new constraints and tests still failing, terminate
                if iteration > 1:  # Give it at least 2 iterations
                    elapsed = time.time() - start_time
                    return AdaptiveFeedbackResult(
                        success=False,
                        iterations=iterations,
                        final_constraints=cumulative_constraints,
                        total_time=elapsed,
                        final_test_result=test_result,
                        termination_reason="No new constraints could be inferred"
                    )

            cumulative_constraints.extend(new_constraints)

            # Record iteration
            iter_time = time.time() - iter_start
            iterations.append(FeedbackIteration(
                iteration=iteration,
                test_result=test_result,
                inferred_constraints=new_constraints,
                cumulative_constraints=cumulative_constraints.copy(),
                elapsed_time=iter_time,
                confidence=inference_result.confidence,
                reasoning=inference_result.reasoning
            ))

        # Max iterations reached
        elapsed = time.time() - start_time

        if self.verbose:
            print(f"\n⚠️  Max iterations ({self.max_iterations}) reached")

        return AdaptiveFeedbackResult(
            success=False,
            iterations=iterations,
            final_constraints=cumulative_constraints,
            total_time=elapsed,
            termination_reason=f"Max iterations ({self.max_iterations}) reached"
        )

    def _update_grammar_constraints(
            self,
            function: CombinedFunctionUnderTest,
            constraints: list[str]
    ) -> None:
        """Update the grammar configuration with new constraints."""
        # Get the grammar for the first function (they should all use the same grammar)
        func_name = function.funcs[0].func.__name__
        current_grammar = self.config.function_to_grammar.get(
            func_name,
            self.config.default_grammar
        )

        # Create new grammar with updated constraints
        if current_grammar:
            base_constraints = current_grammar.extra_constraints or []
            # Merge constraints, avoiding duplicates
            all_constraints = list(set(base_constraints + constraints))

            new_grammar = GrammarConfig(
                current_grammar.path,
                all_constraints if all_constraints else None
            )

            # Update grammar for all functions in the combination
            for fut in function.funcs:
                self.config.function_to_grammar[fut.func.__name__] = new_grammar

    def _run_single_test(
            self,
            property_test: PropertyTest,
            function: CombinedFunctionUnderTest
    ) -> TestResult:
        """Run a single property test and return results."""
        # Create a temporary config with just this property and function
        temp_config = deepcopy(self.config)
        temp_config.properties_to_test = [property_test]
        temp_config.functions_under_test = list(function.funcs)

        # Run the test
        engine = PropertyInferenceEngine(temp_config)
        results = engine.run()

        # Extract the result for this specific combination
        for key, result in results.items():
            if property_test in result['outcomes']:
                return result['outcomes'][property_test]

        # Fallback if no result found
        return TestResult(
            holds=False,
            counterexamples=["No test results found"],
            stats={'total_count': 0, 'success_count': 0}
        )

    def _infer_constraints(
            self,
            property_test: PropertyTest,
            function: CombinedFunctionUnderTest,
            test_result: TestResult,
            current_constraints: list[str],
            iteration: int
    ) -> ConstraintInferenceResult:
        """Use the constraint model to infer new constraints."""

        # Extract test cases from counterexamples
        test_cases = []

        # Parse counterexamples to extract inputs/outputs
        # This is a simplified parser - you may need to enhance based on your format
        for ce in test_result['counterexamples']:
            if ce.strip().endswith('\n'):
                # Try to parse the counterexample
                # Format typically: "func(args): result"
                try:
                    parts = ce.strip().split('\n')
                    for part in parts:
                        if '(' in part and ')' in part and ':' in part:
                            # Extract function call
                            func_call = part.split(':')[0].strip()
                            result = part.split(':')[1].strip()

                            # Extract arguments (simplified)
                            args_str = func_call[func_call.find('(') + 1:func_call.rfind(')')]
                            args = [arg.strip() for arg in args_str.split(',')]

                            test_cases.append(TestCase(
                                inputs=args,
                                output=result,
                                passed=False
                            ))
                except Exception:
                    continue

        # Add some passing cases (inferred from stats)
        # Since we don't have explicit passing cases, we'll let the model work with failures

        # Prepare inference input
        func_names = ', '.join(f.func.__name__ for f in function.funcs)
        inference_input = InferenceInput(
            function_name=func_names,
            property_name=property_test.name,
            test_cases=test_cases,
            current_constraints=current_constraints,
            iteration=iteration
        )

        # Call the constraint inference model
        return self.constraint_model.infer_constraints(inference_input)


def run_adaptive_property_test(
        config: PropertyInferenceConfig,
        property_name: str = "Commutativity",
        function_names: Optional[list[str]] = None,
        constraint_model: Optional[ConstraintInferenceModel] = None,
        **kwargs
) -> dict[str, AdaptiveFeedbackResult]:
    """
    Convenience function to run adaptive tests for specific properties and functions.

    Args:
        config: Property inference configuration
        property_name: Name of the property to test
        function_names: List of function names to test (tests all if None)
        constraint_model: Constraint inference model to use
        **kwargs: Additional arguments for AdaptiveFeedbackLoop

    Returns:
        Dictionary mapping function combinations to their adaptive test results
    """
    # Get the property test
    property_tests = config.registry.get_by_name(property_name)
    if not property_tests:
        raise ValueError(f"Property '{property_name}' not found in registry")

    property_test = property_tests[0]  # Use first variant

    # Filter functions if specified
    if function_names:
        functions = [
            fut for fut in config.functions_under_test
            if fut.func.__name__ in function_names
        ]
    else:
        functions = config.functions_under_test

    # Create adaptive loop
    loop = AdaptiveFeedbackLoop(config, constraint_model, **kwargs)

    # Run tests for each applicable function combination
    results = {}

    from itertools import product
    for funcs in product(functions, repeat=property_test.num_functions):
        combined = CombinedFunctionUnderTest(funcs, config.comparison_strategy)

        if property_test.is_applicable(combined):
            key = f"{combined.names()} - {property_name}"
            results[key] = loop.run_adaptive_test(property_test, combined)

    return results