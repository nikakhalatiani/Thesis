from itertools import product

from config.property_inference_config import PropertyInferenceConfig
from config.grammar_config import GrammarConfig
from core.function_under_test import CombinedFunctionUnderTest
from core.correlation.inference import ConstraintInferenceEngine, LocalModel, OllamaService
from core.generation.input_generator import InputGenerator
from core.evaluation.property_evaluator import PropertyEvaluator
from core.properties.property_test import PropertyTest, TestResult


class Orchestrator:
    """Coordinate input generation, property evaluation and constraint inference."""

    def __init__(self, config: PropertyInferenceConfig) -> None:
        self.config = config
        self.generator = InputGenerator(config)
        self.evaluator = PropertyEvaluator()
        self.constraint_engine = ConstraintInferenceEngine(
            LocalModel(OllamaService("qwen2.5-coder:14b-instruct-q4_K_M"))
        )

    def run(self) -> dict[str, dict[str, TestResult]]:
        results: dict[str, dict[str, TestResult]] = {}
        properties_to_test: list[PropertyTest] = (
            self.config.properties_to_test or self.config.registry.get_all()
        )

        for prop in properties_to_test:
            n = prop.num_functions
            for funcs in product(self.config.functions_under_test, repeat=n):
                combined = CombinedFunctionUnderTest(funcs, self.config.comparison_strategy)
                if not prop.is_applicable(combined):
                    continue

                constraints_history: list[list[str]] = []
                max_attempts = self.config.max_feedback_attempts
                base_grammar = self.generator.build_grammar_for_functions(funcs)
                if base_grammar is None:
                    continue
                current_grammar: GrammarConfig = base_grammar
                attempts = 0
                outcome: TestResult | None = None

                while attempts <= max_attempts:
                    input_sets = self.generator.get_inputs_for_combination(funcs, grammar_override=current_grammar)
                    if not input_sets:
                        break

                    outcome = self.evaluator.test_property(prop, combined, input_sets, self.config.max_counterexamples)
                    if outcome["holds"] or not self.config.feedback_enabled:
                        break
                    if attempts >= max_attempts:
                        break

                    new_constraints = self.constraint_engine.infer(outcome["execution_traces"], current_grammar)
                    constraints_history.append(new_constraints)
                    if not new_constraints:
                        break
                    current_grammar = base_grammar.add_constraints(new_constraints)
                    attempts += 1

                key = f"combination ({combined.names()})"
                results.setdefault(key, {})[str(prop)] = outcome

        return results