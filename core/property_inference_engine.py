from typing import TypedDict
from itertools import product

from core.config import PropertyInferenceConfig
from util.function_under_test import CombinedFunctionUnderTest
from core.properties.property_test import PropertyTest, TestResult
from core.correlation import ConstraintInferenceEngine, LocalModel, OllamaService
from core.generation import InputGenerator
from core.evaluation import PropertyEvaluator


class InferenceResult(TypedDict):
    """Mapping of property labels to their test outcomes."""
    outcomes: dict[PropertyTest, TestResult]
    constraints_history: dict[PropertyTest, list[list[str]]]


class PropertyInferenceEngine:
    """
    Orchestrates the property inference process using generation, evaluation, and correlation modules.

    This engine coordinates:
    1. Input generation using grammar-based fuzzing
    2. Property evaluation against functions under test
    3. Constraint inference and feedback loops for improved testing
    """

    def __init__(self, config: PropertyInferenceConfig) -> None:
        self.config: PropertyInferenceConfig = config

        # Initialize the three main modules
        self.input_generator = InputGenerator(config)
        self.evaluator = PropertyEvaluator()
        self.constraint_engine = ConstraintInferenceEngine(
            LocalModel(OllamaService("qwen2.5-coder:14b-instruct-q4_K_M")))

    def run(self) -> dict[str, InferenceResult]:
        """
        Run the complete property inference process.

        Returns:
            Dictionary mapping function combinations to their inference results
        """
        results: dict[str, InferenceResult] = {}

        # Gather properties to test. A single property name may correspond to
        # several variants, so we work with a flat list.
        properties_to_test: list[PropertyTest] = (self.config.properties_to_test or self.config.registry.get_all())

        for prop in properties_to_test:
            n: int = prop.num_functions

            for funcs in product(self.config.functions_under_test, repeat=n):
                combined = CombinedFunctionUnderTest(funcs, self.config.comparison_strategy)

                if not prop.is_applicable(combined):
                    # print(f"⚠️ Property '{str(prop)}' is not applicable to combination: {combined.names()}. Skipping.")
                    continue

                # Initialize feedback loop variables
                constraints_history: list[list[str]] = []
                max_attempts = self.config.max_feedback_attempts

                # Build base grammar for potential feedback iterations
                base_grammar = self.input_generator.build_grammar_for_functions(funcs)
                if base_grammar is None:
                    continue
                current_grammar = base_grammar

                input_sets = self.input_generator.get_inputs_for_combination(funcs, grammar_override=current_grammar)

                if not input_sets:
                    continue

                # Feedback loop
                attempts = 0
                outcome = None

                while attempts <= max_attempts:
                    # Test the property with current inputs using the evaluator
                    outcome = self.evaluator.test_property(prop, combined, input_sets, self.config.max_counterexamples)

                    # If property holds or feedback is disabled, we're done
                    if outcome["holds"] or not self.config.feedback_enabled:
                        break

                    attempts += 1

                    # If we've reached max attempts, don't generate more constraints
                    if attempts >= max_attempts:
                        break

                    # Infer new constraints from execution traces
                    new_constraints = self.constraint_engine.infer(outcome["execution_traces"], current_grammar)
                    constraints_history.append(new_constraints)

                    # print(f"Function: {combined.names()}")
                    # print(f"[Feedback Iteration {attempts + 1}] New inferred constraints: {new_constraints}")

                    # Check for potential overfitting warnings
                    # for constraint in new_constraints:
                    #     if (("==" in constraint or "!=" in constraint)
                    #             and any(char.isdigit() for char in constraint)):
                    #         print(
                    #             f"[Warning] The constraint '{constraint}' may be overfitting to a small set of passing examples.")

                    # If no new constraints, stop trying
                    if not new_constraints:
                        break

                    # Apply new constraints to grammar for next iteration
                    current_grammar = base_grammar.add_constraints(new_constraints)

                    # Generate new inputs with updated constraints
                    input_sets = self.input_generator.get_inputs_for_combination(funcs,
                                                                                 grammar_override=current_grammar)
                    if not input_sets:
                        break

                    # print(input_sets)

                # Store results
                key = f"combination ({combined.names()})"

                if key not in results:
                    results[key] = InferenceResult(outcomes={}, constraints_history={})

                results[key]["outcomes"][prop] = outcome
                results[key]["constraints_history"][prop] = constraints_history

        return results
