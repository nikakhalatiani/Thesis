from fandango import Fandango
from fandango.language.tree import DerivationTree

from config.property_inference_config import PropertyInferenceConfig
from core.property_tester import PropertyTester
from input.input_parser import InputParser


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
            #     print(str(example))
        return fan, examples

    def run(self) -> dict[str, dict[str, dict]]:
        results: dict[str, dict[str, dict]] = {}
        for idx, fut in enumerate(self.config.functions_under_test):
            name: str = fut.func.__name__
            grammar: str = self.config.function_to_grammar.get(name, self.config.default_grammar)
            parser: InputParser = self.config.function_to_parser.get(name, self.config.default_parser)

            fan, examples = self._generate_examples(grammar, self.config.example_count)

            input_sets = [parser.parse(fan, tree) for tree in examples]
            input_sets = [i for i in input_sets if i is not None]

            tester = PropertyTester(self.config.registry)
            properties, examples, confidence = tester.infer_properties(
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

            results[key] = {
                "properties": properties,
                "examples": examples,
                "confidence": confidence,
            }

        return results
