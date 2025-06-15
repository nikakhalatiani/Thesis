from fandango import Fandango
from fandango.language.tree import DerivationTree

from typing import TypedDict
from itertools import product

from config.property_inference_config import PropertyInferenceConfig
from core.function_under_test import CombinedFunctionUnderTest
from config.grammar_config import GrammarConfig
from core.properties.property_test import PropertyTest, TestResult


class InferenceResult(TypedDict):
    """Mapping of property labels to their test outcomes."""
    outcomes: dict[PropertyTest, TestResult]


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
            fuzz_kwargs["population_size"] = int(num_examples * 2)

            examples: list[DerivationTree] = fan.fuzz(**fuzz_kwargs)
            # for example in examples:
            #     print(example.to_string())
        return fan, examples

    @staticmethod
    def _test_property(property_test: PropertyTest, function: CombinedFunctionUnderTest, input_sets: list,
                       max_counterexamples: int) -> TestResult:
        result = property_test.test(function, input_sets, max_counterexamples)

        return TestResult(
            holds=result['holds'],
            counterexamples=result['counterexamples'][:max_counterexamples],
            stats=result['stats'],
        )

    def run(self) -> dict[str, InferenceResult]:
        results: dict[str, InferenceResult] = {}

        # Gather properties to test. A single property name may correspond to
        # several variants, so we work with a flat list.
        properties_to_test: list[PropertyTest] = (
                self.config.properties_to_test or self.config.registry.get_all())

        for prop in properties_to_test:
            n: int = prop.num_functions

            for funcs in product(self.config.functions_under_test, repeat=n):
                combined = CombinedFunctionUnderTest(funcs, self.config.comparison_strategy)

                if not prop.is_applicable(combined):
                    # print(f"⚠️ Property '{str(prop)}' is not applicable to combination: {combined.names()}. Skipping.")
                    continue

                # gather each function's override or default
                base = None
                combined_constraints: set[str] = set()

                for fut in funcs:
                    fg = self.config.function_to_grammar.get(fut.func.__name__, self.config.default_grammar)
                    if base is None:
                        base = fg
                    elif fg.path != base.path:
                        print(
                            f"⚠️ Cannot combine grammars with different spec paths: {base.path} vs {fg.path}. "
                            f"Skipping combination: {combined.names()}.")
                        break
                    # merge constraints into a set
                    if fg.extra_constraints:
                        combined_constraints.update(fg.extra_constraints)
                else:
                    # This else clause executes only if the for loop completed without breaking
                    # 3) Build a new GrammarConfig using the base path + deduped constraints
                    grammar = GrammarConfig(
                        base.path,
                        list(combined_constraints) if combined_constraints else None
                    )

                    # Collect unique parser objects
                    unique_parsers = {
                        self.config.function_to_parser.get(fut.func.__name__, self.config.default_parser)
                        for fut in funcs
                    }
                    if len(unique_parsers) == 1:
                        # All slots share the same parser instance
                        parser = unique_parsers.pop()
                    else:
                        # Conflicting slot‐specific parsers
                        print(
                            f"⚠️ Cannot combine different parsers for functions: {', '.join(fut.func.__name__ for fut in funcs)}. "
                            f"Skipping combination: {combined.names()}.")
                        continue

                    fan, examples = self._generate_examples(grammar, self.config.example_count)
                    input_sets = [parser.parse(fan, tree) for tree in examples]
                    # print(input_sets)
                    input_sets = [i for i in input_sets if i is not None]
                    # input_sets = ["1", "0"] + input_sets  # Add some trivial inputs for testing
                    # from collections import Counter
                    # counts = Counter(len(s) for s in input_sets)
                    # print("🎲 input‐tuple length distribution:", counts)

                    outcome = self._test_property(prop, combined, input_sets, self.config.max_counterexamples)

                    key = f"combination ({combined.names()})"

                    # If we haven't initialized an entry for this combination yet, do so
                    if key not in results:
                        results[key] = InferenceResult(outcomes={})

                    results[key]["outcomes"][prop] = outcome
        return results
