from fandango import Fandango
from fandango.language.tree import DerivationTree

from typing import TypedDict

from config.property_inference_config import PropertyInferenceConfig
from core.property_tester import PropertyTester
from input.input_parser import InputParser

class InferenceResult(TypedDict):
    properties: dict[str, bool]
    counter_examples:  dict[str, list[dict[str, str] | str]]
    confidence: dict[str, float]
    total_tests: dict[str, int]

class PropertyInferenceEngine:
    def __init__(self, config: PropertyInferenceConfig) -> None:
        self.config: PropertyInferenceConfig = config

    @staticmethod
    def _generate_examples(path_to_grammar: str, num_examples: int) -> tuple[Fandango, list[DerivationTree]]:
        with open(path_to_grammar) as spec_file:
            fan: Fandango = Fandango(spec_file)
            # print("📦 Fuzzing examples:")
            examples: list[DerivationTree] = fan.fuzz(desired_solutions=int(num_examples),
                                                      population_size=int(num_examples * 1.1))
            # for example in examples:
            #     print(example.to_string())
        return fan, examples

    def run(self) ->  dict[str, InferenceResult]:
        results: dict[str, InferenceResult] = {}
        for idx, fut in enumerate(self.config.functions_under_test):
            name: str = fut.func.__name__
            grammar: str = self.config.function_to_grammar.get(name, self.config.default_grammar)
            parser: InputParser = self.config.function_to_parser.get(name, self.config.default_parser)

            fan, examples = self._generate_examples(grammar, self.config.example_count)

            input_sets = [parser.parse(fan, tree) for tree in examples]
            input_sets = [i for i in input_sets if i is not None]

            # from collections import Counter
            # counts = Counter(len(s) for s in input_sets)
            # print("🎲 input‐tuple length distribution:", counts)

            tester = PropertyTester(registry=self.config.registry, max_examples=self.config.max_counterexamples)
            properties, counter_examples, confidence, total_tests = tester.infer_properties(
                fut,
                self.config.properties_to_test,
                input_sets,
                early_stopping=self.config.early_stopping
            )

            # key: str = f"{name} ({idx + 1}/{len(self.config.functions_under_test)})"
            key: str = (f"{'function ' + fut.func.__name__}" " with "
                        f"{fut.arg_converter.__name__ if fut.arg_converter.__name__ != '<lambda>' else 'default'}" " converter and "
                        f"{fut.result_comparator.__name__ if fut.result_comparator.__name__ != '<lambda>' else 'default'}" " comparator")

            # key: str = f"{fut.func.__name__}"

            results[key] = InferenceResult(
                properties=properties,
                counter_examples=counter_examples,
                confidence=confidence,
                total_tests=total_tests,
            )

        return results
