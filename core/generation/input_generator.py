from fandango import Fandango
from fandango.language.tree import DerivationTree

from util.grammar_config import GrammarConfig
from core.config import PropertyInferenceConfig


class InputGenerator:
    """Handles generation of test inputs using grammars and Fandango."""

    def __init__(self, config: PropertyInferenceConfig):
        self.config = config
        # Cache generated input sets for function combinations so they can be
        # reused across library. The key is the tuple of function names in
        # the combination and the value is the list of parsed input tuples. If
        # a combination cannot be processed (e.g. grammar mismatch) we store
        # ``None`` to avoid repeating work.
        self._input_cache: dict[tuple[str, ...], list[tuple] | None] = {}

    def build_grammar_for_functions(self, funcs: tuple) -> GrammarConfig | None:
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
                #     f"{', '.join(f.func.__name__ for f in funcs)}.")
                return None
            if fg.extra_constraints:
                combined_constraints.update(fg.extra_constraints)

        return GrammarConfig(base_grammar.path, list(combined_constraints))

    #TODO need to handle parser better as set functions are not combined because of this
    def get_parser_for_functions(self, funcs: tuple):
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
            #     f"Skipping combination: {', '.join(f.func.__name__ for f in funcs)}.")
            return None

    def get_inputs_for_combination(self, funcs: tuple, grammar_override: GrammarConfig = None) -> list[tuple] | None:
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
            grammar = self.build_grammar_for_functions(funcs)
            if grammar is None:
                if self.config.use_input_cache:
                    self._input_cache[combination_key] = None
                return None

        # Validate parser compatibility
        parser = self.get_parser_for_functions(funcs)
        if parser is None:
            if grammar_override is None and self.config.use_input_cache:
                self._input_cache[combination_key] = None
            return None

        fan, examples = self.generate_examples(grammar, self.config.example_count)
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
    def generate_examples(grammar: GrammarConfig, num_examples: int) -> tuple[Fandango, list[DerivationTree]]:
        """Generate examples using Fandango based on the provided grammar configuration.

        Args:
            grammar: Grammar configuration containing path and constraints
            num_examples: Number of examples to generate

        Returns:
            Tuple of (Fandango instance, list of derivation trees)
        """
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