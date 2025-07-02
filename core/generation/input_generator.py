from fandango import Fandango
from fandango.language.tree import DerivationTree

from config.grammar_config import GrammarConfig
from input.input_parser import InputParser
from core.function_under_test import FunctionUnderTest
from config.property_inference_config import PropertyInferenceConfig


class InputGenerator:
    """Generate and cache input sets for combinations of functions."""

    def __init__(self, config: PropertyInferenceConfig) -> None:
        self.config = config
        self._input_cache: dict[tuple[str, ...], list[tuple] | None] = {}

    def build_grammar_for_functions(self, funcs: tuple[FunctionUnderTest, ...]) -> GrammarConfig | None:
        base_grammar = None
        combined_constraints: set[str] = set()

        for fut in funcs:
            fg = self.config.function_to_grammar.get(
                fut.func.__name__, self.config.default_grammar
            )
            if base_grammar is None:
                base_grammar = fg
            elif fg.path != base_grammar.path:
                return None
            if fg.extra_constraints:
                combined_constraints.update(fg.extra_constraints)

        return GrammarConfig(base_grammar.path, list(combined_constraints)) if base_grammar else None

    def get_parser_for_functions(self, funcs: tuple[FunctionUnderTest, ...]) -> InputParser | None:
        unique_parsers = {
            self.config.function_to_parser.get(
                fut.func.__name__, self.config.default_parser
            )
            for fut in funcs
        }
        return unique_parsers.pop() if len(unique_parsers) == 1 else None

    @staticmethod
    def _generate_examples(grammar: GrammarConfig, num_examples: int) -> tuple[Fandango, list[DerivationTree]]:
        path_to_grammar: str = grammar.path
        extra_constraints: list[str] = grammar.extra_constraints
        with open(path_to_grammar) as spec_file:
            fan: Fandango = Fandango(spec_file)
            fuzz_kwargs = {}
            if extra_constraints is not None:
                fuzz_kwargs["extra_constraints"] = extra_constraints

            fuzz_kwargs["desired_solutions"] = int(num_examples)
            fuzz_kwargs["population_size"] = int(num_examples * 2)

            examples: list[DerivationTree] = fan.fuzz(**fuzz_kwargs)
        return fan, examples

    def get_inputs_for_combination(self, funcs: tuple[FunctionUnderTest, ...], grammar_override: GrammarConfig | None = None) -> list[tuple] | None:
        combination_key = tuple(fut.func.__name__ for fut in funcs)
        if grammar_override is None and self.config.use_input_cache and combination_key in self._input_cache:
            cached = self._input_cache[combination_key]
            return list(cached) if cached is not None else None

        grammar = grammar_override or self.build_grammar_for_functions(funcs)
        if grammar is None:
            if self.config.use_input_cache and grammar_override is None:
                self._input_cache[combination_key] = None
            return None

        parser = self.get_parser_for_functions(funcs)
        if parser is None:
            if self.config.use_input_cache and grammar_override is None:
                self._input_cache[combination_key] = None
            return None

        fan, examples = self._generate_examples(grammar, self.config.example_count)
        input_sets = [parser.parse(fan, tree) for tree in examples]
        input_sets = [i for i in input_sets if i is not None]

        if grammar_override is None and self.config.use_input_cache:
            self._input_cache[combination_key] = input_sets
        return list(input_sets)