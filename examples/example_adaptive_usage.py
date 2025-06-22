#!/usr/bin/env python3
"""
Example script demonstrating how to use the adaptive feedback loop
with different constraint inference models.
"""

import os
import sys
from typing import Any

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.properties import create_basic_registry
from input.input_parser import InputParser
from config.property_inference_config import PropertyInferenceConfig
from core.function_under_test import FunctionUnderTest, ComparisonStrategy

from core.constraint_inference_engine import (
    RuleBasedModel, MockLLMModel, LLMAPIModel, PythonScriptModel
)
from core.adaptive_feedback_loop import AdaptiveFeedbackLoop, run_adaptive_property_test

# Get the project root directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Example functions to test
class ExampleFunctions:
    """Functions with properties that hold under certain constraints."""

    @staticmethod
    def safe_divide(x, y):
        """Division that's commutative when both inputs are reciprocals."""
        if y == 0:
            return float('inf')
        return x / y

    @staticmethod
    def conditional_add(x, y):
        """Addition that's only commutative for positive numbers."""
        if x < 0 or y < 0:
            return x - y  # Non-commutative for negative
        return x + y  # Commutative for positive

    @staticmethod
    def modular_multiply(x, y):
        """Multiplication that's commutative except when one input is 0."""
        if x == 0:
            return y + 1  # Break commutativity
        if y == 0:
            return x + 1  # Break commutativity
        return x * y


def example_basic_usage():
    """Basic example using the rule-based model."""
    print("=" * 60)
    print("Example 1: Basic Adaptive Testing with Rule-Based Model")
    print("=" * 60)

    # Create configuration
    registry = create_basic_registry()
    config = (PropertyInferenceConfig(registry)
              .set_default_grammar(os.path.join(PROJECT_ROOT, "grammars/test.fan"))
              .set_default_parser(InputParser.for_numbers())
              .set_example_count(50)
              .set_max_counterexamples(5))

    # Register test function
    fut = FunctionUnderTest(
        ExampleFunctions.conditional_add,
        arg_converter=[int, int]
    )
    config.add_function(fut)

    # Run adaptive test
    results = run_adaptive_property_test(
        config,
        property_name="Commutativity",
        function_names=["conditional_add"],
        max_iterations=5,
        verbose=True
    )

    # Display results
    for key, result in results.items():
        print(f"\n📊 Results for {key}:")
        print(f"   Success: {result.success}")
        print(f"   Iterations: {len(result.iterations)}")
        print(f"   Final constraints: {result.final_constraints}")
        print(f"   Termination: {result.termination_reason}")


def example_llm_usage():
    """Example using LLM for constraint inference."""
    print("\n" + "=" * 60)
    print("Example 2: Adaptive Testing with LLM Model")
    print("=" * 60)

    # Check if API key is available
    api_key = os.environ.get("OPENAI_API_KEY")

    if api_key:
        model = LLMAPIModel(api_key)
        print("Using real LLM API")
    else:
        model = MockLLMModel()
        print("Using mock LLM (set OPENAI_API_KEY to use real API)")

    # Create configuration
    registry = create_basic_registry()
    config = (PropertyInferenceConfig(registry)
              .set_default_grammar(os.path.join(PROJECT_ROOT, "grammars/test.fan"))
              .set_default_parser(InputParser.for_numbers())
              .set_example_count(30))

    # Register test function
    fut = FunctionUnderTest(
        ExampleFunctions.modular_multiply,
        arg_converter=[int, int]
    )
    config.add_function(fut)

    # Create adaptive loop with LLM model
    loop = AdaptiveFeedbackLoop(
        config,
        constraint_model=model,
        max_iterations=3,
        verbose=True
    )

    # Get commutativity test
    comm_test = registry.get_by_name("Commutativity")[0]

    # Run adaptive test
    from core.function_under_test import CombinedFunctionUnderTest
    combined = CombinedFunctionUnderTest((fut,))

    result = loop.run_adaptive_test(comm_test, combined)

    print(f"\n📊 Final Result:")
    print(f"   Success: {result.success}")
    print(f"   Total time: {result.total_time:.2f}s")

    # Show iteration details
    for iteration in result.iterations:
        print(f"\n   Iteration {iteration.iteration}:")
        print(f"     New constraints: {iteration.inferred_constraints}")
        print(f"     Confidence: {iteration.confidence:.2f}")
        if iteration.reasoning:
            print(f"     Reasoning: {iteration.reasoning}")


def example_custom_model():
    """Example with custom constraint inference logic."""
    print("\n" + "=" * 60)
    print("Example 3: Custom Constraint Inference Model")
    print("=" * 60)

    from core.constraint_inference_engine import ConstraintInferenceModel, ConstraintInferenceResult

    class DivisionAwareModel(ConstraintInferenceModel):
        """Custom model that understands division by zero issues."""

        def infer_constraints(self, inference_input):
            constraints = []

            # Look for infinity in outputs (indicates division by zero)
            for tc in inference_input['test_cases']:
                if not tc['passed'] and 'inf' in str(tc['output']):
                    # Check which input might be zero
                    for i, val in enumerate(tc['inputs']):
                        if str(val) == '0' and i == 1:  # Second argument (divisor)
                            constraints.append("int(<term_2>) != 0")
                            break

            return ConstraintInferenceResult(
                constraints=list(set(constraints)),  # Remove duplicates
                confidence=0.95,
                reasoning="Detected division by zero pattern"
            )

    # Setup and run
    registry = create_basic_registry()
    config = (PropertyInferenceConfig(registry)
              .set_default_grammar(os.path.join(PROJECT_ROOT, "grammars/test.fan"))
              .set_default_parser(InputParser.for_numbers()))

    fut = FunctionUnderTest(
        ExampleFunctions.safe_divide,
        arg_converter=[float, float]
    )
    config.add_function(fut)

    # Note: Division is not commutative, but let's see what constraints emerge
    results = run_adaptive_property_test(
        config,
        property_name="Commutativity",
        function_names=["safe_divide"],
        constraint_model=DivisionAwareModel(),
        max_iterations=3,
        min_examples_per_iteration=20,
        verbose=True
    )


def example_multiple_properties():
    """Test multiple properties with adaptive feedback."""
    print("\n" + "=" * 60)
    print("Example 4: Testing Multiple Properties")
    print("=" * 60)

    # Create configuration with multiple properties
    registry = create_basic_registry()
    config = (PropertyInferenceConfig(registry)
              .set_default_grammar(os.path.join(PROJECT_ROOT, "grammars/test.fan"))
              .set_default_parser(InputParser.for_numbers())
              .set_example_count(40))

    # Simple max function
    def bounded_max(x, y):
        """Max function that only works correctly for inputs in range [0, 100]."""
        if x < 0 or y < 0 or x > 100 or y > 100:
            return -1  # Breaks properties outside range
        return max(x, y)

    config.add_function(FunctionUnderTest(bounded_max, arg_converter=[int, int]))

    # Test different properties
    properties_to_test = ["Commutativity", "Associativity", "IdentityElement"]

    model = RuleBasedModel()

    for prop_name in properties_to_test:
        print(f"\n🔍 Testing {prop_name}...")

        try:
            results = run_adaptive_property_test(
                config,
                property_name=prop_name,
                function_names=["bounded_max"],
                constraint_model=model,
                max_iterations=4,
                verbose=False  # Less verbose for multiple tests
            )

            for key, result in results.items():
                print(f"   Result: {'✅ PASS' if result.success else '❌ FAIL'}")
                print(f"   Constraints found: {result.final_constraints or ['None']}")

        except ValueError as e:
            print(f"   ⚠️  {e}")


if __name__ == "__main__":
    # Run all examples
    example_basic_usage()
    example_llm_usage()
    example_custom_model()
    example_multiple_properties()

    print("\n" + "=" * 60)
    print("✨ Adaptive feedback loop examples completed!")
    print("=" * 60)