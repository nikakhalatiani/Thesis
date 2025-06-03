from fandango import Fandango
from fandango.language.tree import DerivationTree

from typing import TypedDict
from itertools import product

from config.property_inference_config import PropertyInferenceConfig
from core.function_under_test import CombinedFunctionUnderTest, ComparisonStrategy
from core.property_tester import PropertyTester, PropertyOutcome
from config.grammar_config import GrammarConfig
from core.properties.property_test import PropertyTest


class InferenceResult(TypedDict):
    outcomes: dict[str, PropertyOutcome]


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

    def run(self) -> dict[str, InferenceResult]:
        results: dict[str, InferenceResult] = {}

        properties_to_test: list[PropertyTest] = (
                    self.config.properties_to_test or self.config.registry.get_all().values())

        for prop in properties_to_test:
            n: int = prop.num_functions

            for funcs in product(self.config.functions_under_test, repeat=n):
                combined = CombinedFunctionUnderTest(funcs, self.config.comparison_strategy)

                if not prop.is_applicable(combined):
                    print(f"⚠️ Property '{prop.name}' is not applicable to combination: {combined.names()}. Skipping.")
                    continue

                # collect the names for lookup
                names = tuple(fut.func.__name__ for fut in funcs)

                # 1) combination-level explicit override
                grammar = (
                        self.config.combination_to_grammar.get(names)
                        or None
                )
                parser = (
                        self.config.combination_to_parser.get(names)
                        or None
                )

                # 2) if no explicit combo override, try to merge per-function ones
                if grammar is None:
                    # gather each function's override or default
                    base = None
                    combined_constraints: set[str] = set()

                    for fut in funcs:
                        fg = self.config.function_to_grammar.get(fut.func.__name__, self.config.default_grammar)
                        if base is None:
                            base = fg
                        elif fg.path != base.path:
                            raise ValueError(
                                f"Cannot combine grammars with different spec paths: "f"{base.path} vs {fg.path}")
                        # 2) Merge constraints into a set (automatically dedupes)
                        if fg.extra_constraints:
                            combined_constraints.update(fg.extra_constraints)

                    # 3) Build a new GrammarConfig using the base path + deduped constraints
                    grammar = GrammarConfig(
                        base.path,
                        list(combined_constraints) if combined_constraints else None
                    )

                if parser is None:
                    per_fs = [
                        self.config.function_to_parser.get(fut.func.__name__, self.config.default_parser)
                        for fut in funcs
                    ]
                    # Collect unique parser objects
                    unique = {p for p in per_fs}
                    if len(unique) == 1:
                        # All slots share the same parser instance
                        parser = unique.pop()
                    else:
                        # Conflicting slot‐specific parsers → raise or fallback
                        raise ValueError(
                            f"Cannot combine different parsers for functions: "
                            f"{', '.join(fut.func.__name__ for fut in funcs)}"
                        )

                # import time
                # start_time = time.perf_counter()
                fan, examples = self._generate_examples(grammar, self.config.example_count)
                input_sets = [parser.parse(fan, tree) for tree in examples]
                input_sets = [i for i in input_sets if i is not None]
                input_sets = [(1,1,1)] + input_sets
                # end_time = time.perf_counter()
                # print(f"Execution time: {end_time - start_time:.4f} seconds")

                # from collections import Counter
                # counts = Counter(len(s) for s in input_sets)
                # print("🎲 input‐tuple length distribution:", counts)

                tester = PropertyTester(self.config.max_counterexamples)
                outcome = tester.test_property(combined, prop, input_sets, self.config.early_stopping)

                key = f"combination ({combined.names()})"

                # If we haven’t initialized an entry for this combination yet, do so
                if key not in results:
                    results[key] = InferenceResult(outcomes={})

                results[key]["outcomes"][prop.name] = outcome

        return results
