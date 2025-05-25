from fandango import Fandango
from fandango.language.tree import DerivationTree

from typing import TypedDict
from collections.abc import Callable

from config.property_inference_config import PropertyInferenceConfig
from core.function_under_test import FunctionUnderTest
from core.property_tester import PropertyTester
from input.input_parser import InputParser
from config.grammar_config import GrammarConfig
from core.properties.property_test import PropertyTest


class InferenceResult(TypedDict):
    properties: dict[str, bool]
    counterexamples: dict[str, list[dict[str, str] | str]]
    confidence: dict[str, float]
    total_tests: dict[str, int]


class PropertyInferenceEngine:
    def __init__(self, config: PropertyInferenceConfig) -> None:
        self.config: PropertyInferenceConfig = config

    @staticmethod
    def _generate_examples(grammar: GrammarConfig, num_examples: int) -> tuple[Fandango, list[DerivationTree]]:
        path_to_grammar: str = grammar.path
        extra_constraints: list[str] = grammar.extra_constraints
        with open(path_to_grammar) as spec_file:
            fan: Fandango = Fandango(spec_file)
            # print("📦 Fuzzing examples:")
            fuzz_kwargs = {}
            if extra_constraints is not None:
                fuzz_kwargs["extra_constraints"] = extra_constraints

            fuzz_kwargs["desired_solutions"] = int(num_examples)
            fuzz_kwargs["population_size"] = int(num_examples * 1.5)

            examples: list[DerivationTree] = fan.fuzz(**fuzz_kwargs)
            # for example in examples:
            #     print(example.to_string())
        return fan, examples

    def _get_applicable_properties(self, function: FunctionUnderTest) -> list[PropertyTest]:
        """Get only the properties that apply to the given function arity."""
        if not self.config.properties_to_test:
            # If no specific properties are configured, check all registry properties
            return self.config.registry.get_applicable_tests(function)
        else:
            return [prop for prop in self.config.properties_to_test
                    if prop.is_applicable(function)]

    def run(self) -> dict[str, InferenceResult]:
        results: dict[str, InferenceResult] = {}

        def get_name(helper: Callable) -> str:
            helper_name = helper.__name__
            if helper_name.startswith('_'):
                return 'default'
            elif helper_name == '<lambda>':
                return 'default'
            else:
                return helper_name

        for idx, fut in enumerate(self.config.functions_under_test):
            name: str = fut.func.__name__


            # Check if there are any applicable properties before generating examples
            applicable_properties = self._get_applicable_properties(fut)
            if not applicable_properties:
                print(f"⚠️  No applicable properties for function '{name}'. Skipping example generation.")
                continue

            grammar: GrammarConfig = self.config.function_to_grammar.get(name, self.config.default_grammar)
            parser: InputParser = self.config.function_to_parser.get(name, self.config.default_parser)

            fan, examples = self._generate_examples(grammar, self.config.example_count)

            input_sets = [parser.parse(fan, tree) for tree in examples]
            input_sets = [i for i in input_sets if i is not None]

            # from collections import Counter
            # counts = Counter(len(s) for s in input_sets)
            # print("🎲 input‐tuple length distribution:", counts)

            tester = PropertyTester(registry=self.config.registry, max_examples=self.config.max_counterexamples)
            properties, counterexamples, confidence, total_tests = tester.infer_properties(
                fut,
                applicable_properties,
                input_sets,
                early_stopping=self.config.early_stopping
            )

            # Get the name of the function and converters properly
            func_name = fut.func.__name__
            arg_converter_name = get_name(fut.arg_converter)
            result_comparator_name = get_name(fut.result_comparator)

            # Create the key with proper string formatting - no nested f-strings
            key: str = f"function {func_name} with {arg_converter_name} converter and {result_comparator_name} comparator"

            # key: str = f"{name} ({idx + 1}/{len(self.config.functions_under_test)})"

            # key: str = f"{fut.func.__name__}"

            results[key] = InferenceResult(
                properties=properties,
                counterexamples=counterexamples,
                confidence=confidence,
                total_tests=total_tests,
            )

        return results
