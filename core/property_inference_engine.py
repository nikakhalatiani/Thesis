from fandango import Fandango
from fandango.language.tree import DerivationTree

from typing import TypedDict
from itertools import product

from config.property_inference_config import PropertyInferenceConfig
from core.function_under_test import CombinedFunctionUnderTest
from config.grammar_config import GrammarConfig
from core.properties.property_test import PropertyTest, TestResult
from core.constraint_inference_engine import ConstraintInferenceEngine, LocalModel, OllamaService


class InferenceResult(TypedDict):
    """Mapping of property labels to their test outcomes."""
    outcomes: dict[PropertyTest, TestResult]
    constraints_history: dict[PropertyTest, list[list[str]]]


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
        self.constraint_engine = ConstraintInferenceEngine(LocalModel(OllamaService("qwen2.5-coder:14b-instruct-q4_K_M")))

    def _build_grammar_for_functions(self, funcs: tuple) -> GrammarConfig | None:
        """Build a combined grammar configuration from multiple functions.

        Args:
            funcs: Tuple of functions to build grammar for

        Returns:
            Combined GrammarConfig or None if functions have incompatible grammars
        """
        base_grammar = None
        combined_constraints: set[str] = set()

        for fut in funcs:
            fg = self.config.function_to_grammar.get(
                fut.func.__name__, self.config.default_grammar
            )
            if base_grammar is None:
                base_grammar = fg
            elif fg.path != base_grammar.path:
                # print(
                #     f"⚠️ Cannot combine grammars with different spec paths: "
                #     f"{base_grammar.path} vs {fg.path}. Skipping combination: "
                #     f"{', '.join(f.func.__name__ for f in funcs)}."
                # )
                return None
            if fg.extra_constraints:
                combined_constraints.update(fg.extra_constraints)

        return GrammarConfig(base_grammar.path, list(combined_constraints))

    def _get_parser_for_functions(self, funcs: tuple):
        """Get a compatible parser for multiple functions.

        Args:
            funcs: Tuple of functions to get parser for

        Returns:
            Compatible parser or None if functions have incompatible parsers
        """
        unique_parsers = {
            self.config.function_to_parser.get(
                fut.func.__name__, self.config.default_parser
            )
            for fut in funcs
        }

        if len(unique_parsers) == 1:
            return unique_parsers.pop()
        else:
            # print(
            #     f"⚠️ Cannot combine different parsers for functions: "
            #     f"{', '.join(fut.func.__name__ for fut in funcs)}. "
            #     f"Skipping combination: {', '.join(f.func.__name__ for f in funcs)}."
            # )
            return None

    def _get_inputs_for_combination(self, funcs: tuple, grammar_override: GrammarConfig = None) -> list[tuple] | None:
        """Return cached inputs for ``funcs`` or generate and cache them.

        Args:
            funcs: Tuple of functions to get inputs for
            grammar_override: If provided, use this grammar instead of building from function configs.
                             When provided, caching is bypassed since the grammar may be dynamic.
        """
        combination_key = tuple(fut.func.__name__ for fut in funcs)

        # Only use cache if no grammar override is provided
        if grammar_override is None and self.config.use_input_cache and combination_key in self._input_cache:
            cached = self._input_cache[combination_key]
            # return a shallow copy to avoid accidental modification
            return list(cached) if cached is not None else None

        # If grammar override is provided, use it directly
        if grammar_override is not None:
            grammar = grammar_override
        else:
            # Build grammar from function configurations
            grammar = self._build_grammar_for_functions(funcs)
            if grammar is None:
                if self.config.use_input_cache:
                    self._input_cache[combination_key] = None
                return None

        # Validate parser compatibility
        parser = self._get_parser_for_functions(funcs)
        if parser is None:
            if grammar_override is None and self.config.use_input_cache:
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

        # Only cache if no grammar override (i.e., this is the base case)
        if grammar_override is None and self.config.use_input_cache:
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

        return TestResult(
            holds=result['holds'],
            counterexamples=result['counterexamples'][:max_counterexamples],
            successes=result['successes'][:max_counterexamples],
            stats=result['stats'],
            execution_traces=result['execution_traces']
        )

    def run(self) -> dict[str, InferenceResult]:
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
                base_grammar = self._build_grammar_for_functions(funcs)
                if base_grammar is None:
                    continue
                current_grammar: GrammarConfig = base_grammar

                # Feedback loop
                attempts = 0
                outcome = None

                while attempts <= max_attempts:
                    # Generate inputs with current grammar (first iteration uses base grammar)
                    input_sets = self._get_inputs_for_combination(funcs, grammar_override=current_grammar)
                    if not input_sets:
                        break

                    print(input_sets)

                    # Test the property with current inputs
                    outcome = self._test_property(prop, combined, input_sets, self.config.max_counterexamples)

                    # If property holds or feedback is disabled, we're done
                    if outcome["holds"] or not self.config.feedback_enabled:
                        break

                    # If we've reached max attempts, don't generate more constraints
                    if attempts >= max_attempts:
                        break

                    # Infer new constraints from execution traces
                    new_constraints = self.constraint_engine.infer(outcome["execution_traces"], current_grammar)
                    constraints_history.append(new_constraints)

                    print(f"Function: {combined.names()}")
                    print(f"[Feedback Iteration {attempts + 1}] New inferred constraints: {new_constraints}")

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

                    attempts += 1

                # Store results
                key = f"combination ({combined.names()})"

                if key not in results:
                    results[key] = InferenceResult(outcomes={}, constraints_history={})

                results[key]["outcomes"][prop] = outcome
                results[key]["constraints_history"][prop] = constraints_history

        return results
