from fandango import FandangoParseError, Fandango
from fandango.language.tree import DerivationTree, NonTerminal

from collections.abc import Callable
from typing import Any


class InputParser:
    """
    A parser that extracts inputs from a derivation tree using a specified extraction strategy.
    """

    def __init__(self, extraction_strategy: Callable[[DerivationTree], Any]) -> None:
        self.extraction_strategy = extraction_strategy

    def parse(self, fan: Fandango, tree: DerivationTree) -> Any | None:
        """
        Parse a derivation tree and extract inputs using the extraction strategy.

        Args:
            fan: The Fandango object used for parsing.
            tree: The derivation tree to parse.

        Returns:
            The extracted inputs if parsing is successful, otherwise None.
        """
        try:
            parsed_trees = fan.parse(tree)
            first_tree = next(parsed_trees, None)
            if first_tree is not None:
                return self.extraction_strategy(first_tree)
        except FandangoParseError as e:
            print(f"❌ Parsing failed at position {e.position} in '{tree}'")
        return None

    # ===== Extraction Strategies =====

    @staticmethod
    def extract_by_nonterminal(tree: DerivationTree, nonterminal: str) -> tuple[str, ...]:
        """
        Extract all subtrees matching a specific nonTerminal.

        Args:
            tree: The derivation tree to search
            nonterminal: The nonTerminal to search for (e.g., "<number>")

        Returns:
            Tuple of string representations of matching subtrees
        """
        nt = NonTerminal(nonterminal)
        nodes = tree.find_all_trees(nt)
        return tuple(node.to_string() for node in nodes)

    @staticmethod
    def extract_numbers(tree: DerivationTree) -> tuple[str, ...]:
        """Extract all number values as strings from the tree."""
        return InputParser.extract_by_nonterminal(tree, "<number>")

    @staticmethod
    def extract_number_values(tree: DerivationTree) -> tuple[int | float, ...]:
        """Extract all numeric values from the tree, converted to appropriate types."""
        number_strings = InputParser.extract_numbers(tree)
        values = []

        for num_str in number_strings:
            try:
                if '.' in num_str or 'e' in num_str.lower():
                    values.append(float(num_str))
                else:
                    values.append(int(num_str))
            except ValueError:
                # If conversion fails, keep as string or skip
                continue

        return tuple(values)

    # @staticmethod
    # def basic_recursion_with_built_in_detector(tree: DerivationTree) -> tuple[str, ...]:
    #
    #     elements: list[str] = []
    #
    #     def visit(node: DerivationTree):
    #         if node.is_num():
    #             # Get the actual value represented by the node
    #             value = node.value()
    #             if value is not None:
    #                 elements.append(str(value))
    #             return
    #
    #         for child in node.children:
    #             visit(child)
    #
    #     visit(tree)
    #
    #     return tuple(elements)

    # ===== Grammar-Aware Extraction Methods =====

    @staticmethod
    def extract_sets(tree: DerivationTree) -> tuple[str, ...]:
        """Extract all <set> nonterminals from the tree."""
        return InputParser.extract_by_nonterminal(tree, "<set>")


    # ===== Factory methods for common patterns =====

    @classmethod
    def for_numbers(cls) -> 'InputParser':
        """Create a parser that extracts all numbers."""
        return cls(cls.extract_numbers)

    @classmethod
    def for_number_values(cls) -> 'InputParser':
        """Create a parser that extracts numeric values."""
        return cls(cls.extract_number_values)

    @classmethod
    def for_all_sets(cls) -> 'InputParser':
        """Create a parser that extracts all sets."""
        return cls(cls.extract_sets)

    @classmethod
    def for_nonterminal(cls, nonterminal: str) -> 'InputParser':
        """Create a parser that extracts all instances of a specific nonterminal."""
        return cls(lambda tree: cls.extract_by_nonterminal(tree, nonterminal))

    # ===== Advanced Grammar-Aware Extraction =====

    @classmethod
    def for_grammar_pattern(cls, *nonterminals: str) -> 'InputParser':
        """
        Create a parser that extracts specific nonterminals in order.

        Example:
            # For grammar: <start> ::= <set> ", " <number>
            parser = InputParser.for_grammar_pattern("<set>", "<number>")
            # Returns tuple with first <set> and first <number>
        """

        def extract_pattern(tree: DerivationTree) -> tuple[str, ...]:
            results = []
            for nt in nonterminals:
                matches = cls.extract_by_nonterminal(tree, nt)
                if matches:
                    results.append(matches[0])  # Take first match
                else:
                    raise ValueError(f"No matches found for nonterminal: {nt}")
            return tuple(results)

        return cls(extract_pattern)