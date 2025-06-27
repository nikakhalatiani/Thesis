from fandango import Fandango
from fandango.language.tree import DerivationTree

from typing import TypedDict
from itertools import product

from config.property_inference_config import PropertyInferenceConfig
from core.function_under_test import CombinedFunctionUnderTest
from config.grammar_config import GrammarConfig
from core.properties.property_test import PropertyTest, TestResult
from core.constraint_inference_engine import ConstraintInferenceEngine, GeminiModel, TestCase


class InferenceResult(TypedDict):
    """Mapping of property labels to their test outcomes."""
    outcomes: dict[PropertyTest, TestResult]


class PropertyInferenceEngine:
    def __init__(self, config: PropertyInferenceConfig) -> None:
        self.config: PropertyInferenceConfig = config
        # Cache generated input sets for function combinations so they can be
        # reused across properties. The key is the tuple of function names in
        # the combination and the value is the list of parsed input tuples. If
        # a combination cannot be processed (e.g. grammar mismatch) we store
        # ``None`` to avoid repeating work.
        self._input_cache: dict[tuple[str, ...], list[tuple] | None] = {}

        # Initialize constraint inference engine
        self.constraint_engine = ConstraintInferenceEngine(GeminiModel())

    def _get_inputs_for_combination(self, funcs: tuple) -> list[tuple] | None:
        """Return cached inputs for ``funcs`` or generate and cache them."""

        combination_key = tuple(fut.func.__name__ for fut in funcs)
        if self.config.use_input_cache and combination_key in self._input_cache:
            cached = self._input_cache[combination_key]
            # return a shallow copy to avoid accidental modification
            return list(cached) if cached is not None else None

        base = None
        combined_constraints: set[str] = set()

        for fut in funcs:
            fg = self.config.function_to_grammar.get(
                fut.func.__name__, self.config.default_grammar
            )
            if base is None:
                base = fg
            elif fg.path != base.path:
                print(
                    f"⚠️ Cannot combine grammars with different spec paths: "
                    f"{base.path} vs {fg.path}. Skipping combination: "
                    f"{', '.join(f.func.__name__ for f in funcs)}."
                )
                if self.config.use_input_cache:
                    self._input_cache[combination_key] = None
                return None
            if fg.extra_constraints:
                combined_constraints.update(fg.extra_constraints)
        else:
            grammar = GrammarConfig(
                base.path,
                list(combined_constraints) if combined_constraints else None,
            )

            unique_parsers = {
                self.config.function_to_parser.get(
                    fut.func.__name__, self.config.default_parser
                )
                for fut in funcs
            }
            if len(unique_parsers) == 1:
                parser = unique_parsers.pop()
            else:
                print(
                    f"⚠️ Cannot combine different parsers for functions: "
                    f"{', '.join(fut.func.__name__ for fut in funcs)}. "
                    f"Skipping combination: {', '.join(f.func.__name__ for f in funcs)}."
                )
                if self.config.use_input_cache:
                    self._input_cache[combination_key] = None
                return None

            fan, examples = self._generate_examples(grammar, self.config.example_count)
            input_sets = [parser.parse(fan, tree) for tree in examples]
            # print(input_sets)
            input_sets = [i for i in input_sets if i is not None]
            # input_sets = [("1", "0")] + input_sets  # Add some trivial inputs for testing
            # from collections import Counter
            # counts = Counter(len(s) for s in input_sets)
            # print("🎲 input‐tuple length distribution:", counts)

            if self.config.use_input_cache:
                self._input_cache[combination_key] = input_sets
            return list(input_sets)

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

        traces = result.get('execution_traces', [])
        cases: list[TestCase] = []
        for tr in traces:
            cases.append(
                TestCase(
                    property=tr.get('property_name', property_test.name),
                    original_args=tuple(tr.get('input', ())),
                    passed=bool(tr.get('comparison_result')),
                    result1=tr.get('output'),
                    result2=tr.get('expected_output', tr.get('swapped_output')),
                )
            )

        return TestResult(
            holds=result['holds'],
            counterexamples=result['counterexamples'][:max_counterexamples],
            successes=result['successes'][:max_counterexamples],
            stats=result['stats'],
            execution_traces=traces,
            cases=cases,
        )

    def _test_property_with_feedback(
            self,
            prop: PropertyTest,
            fut: CombinedFunctionUnderTest,
            max_attempts: int = 5,
    ) -> tuple[TestResult, list[list[str]]]:
        """Test a property with adaptive constraint feedback."""
        constraints_history: list[list[str]] = []

        base_grammar = None
        combined_constraints: set[str] = set()

        for f in fut.funcs:
            fg = self.config.function_to_grammar.get(
                f.func.__name__, self.config.default_grammar
            )
            if base_grammar is None:
                base_grammar = fg
            if fg.extra_constraints:
                combined_constraints.update(fg.extra_constraints)

        current_grammar = GrammarConfig(
            base_grammar.path,
            list(combined_constraints) if combined_constraints else None, )

        attempts = 0
        last_result: TestResult | None = None

        while attempts < max_attempts:
            parser = self.config.function_to_parser.get(
                fut.funcs[0].func.__name__, self.config.default_parser
            )
            fan, examples = self._generate_examples(current_grammar, self.config.example_count)
            input_sets = [parser.parse(fan, t) for t in examples]
            input_sets = [i for i in input_sets if i is not None]

            result = self._test_property(
                prop,
                fut,
                input_sets,
                self.config.max_counterexamples
            )
            last_result = result

            if result["holds"]:
                return result, constraints_history

            new_constraints = self.constraint_engine.infer(result.get("cases", []), current_grammar)
            constraints_history.append(new_constraints)

            print(f"Function: {fut.names()}")
            print(f"Input sets: {input_sets}")
            print(f"[Feedback Iteration {attempts + 1}] New inferred constraints: {new_constraints}")

            for constraint in new_constraints:
                if (
                        ("==" in constraint or "!=" in constraint)
                        and any(char.isdigit() for char in constraint)
                ):
                    print(
                        f"[Warning] The constraint '{constraint}' may be overfitting to a small set of passing examples. Consider providing more diverse passing cases or increasing input diversity.")

            if not new_constraints:
                return result, constraints_history

            current_grammar = self.constraint_engine.apply_constraints(current_grammar, new_constraints)
            attempts += 1

        return last_result if last_result is not None else result, constraints_history

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

                outcome, constraints_history = self._test_property_with_feedback(
                    prop,
                    combined,
                    max_attempts=getattr(self.config, 'max_feedback_attempts', 5)
                )

                key = f"combination ({combined.names()})"

                if key not in results:
                    results[key] = InferenceResult(outcomes={}, constraints_history={})

                results[key]["outcomes"][prop] = outcome
                results[key]["constraints_history"][prop] = constraints_history
        # print(f"🔍 Tested {len(results)} combinations with {len(properties_to_test)} properties.")
        # print(f"📦 Cached {len(self._input_cache)} unique input sets for function combinations.")

        return results

    def run_with_feedback(
            self,
            prop: PropertyTest,
            fut: CombinedFunctionUnderTest,
            grammar: GrammarConfig,
            engine: ConstraintInferenceEngine,
            max_attempts: int = 5,
    ) -> tuple[TestResult, list[list[str]]]:
        """Legacy method - consider using the integrated feedback in run() instead."""
        return self._test_property_with_feedback(prop, fut, max_attempts)
