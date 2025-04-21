from typing import Any

from fandango import FandangoParseError, Fandango
from fandango.language.tree import DerivationTree

from collections.abc import Callable


class InputParser:
    """
    A parser that extracts inputs from a derivation tree using a specified extraction strategy.

    Attributes:
            extraction_strategy: A function that takes a parse tree and returns the extracted inputs.
    """

    def __init__(self, extraction_strategy: Callable) -> None:

        self.extraction_strategy: Callable = extraction_strategy

    def parse(self, fan: Fandango, tree: DerivationTree) -> Any | None:
        """
        Parse a derivation tree and extract inputs using the extraction strategy.

        Args:
            fan: The Fandango object used for parsing.
            tree: The derivation tree to parse.

        Returns:
            The extracted inputs if parsing is successful, otherwise None.

        Raises:
            FandangoParseError: If parsing fails, an error message is printed.
        """
        try:
            # TODO ask if parsing DerivationTree is better than parsing str
            # TODO maybe it will always return tuple, NOT SURE
            for tree in fan.parse(tree):
                return self.extraction_strategy(tree)
        except FandangoParseError as e:
            print(f"❌ Parsing failed at position {e.position} in '{tree}'")
        return None

    @staticmethod
    def extract_two_numbers(tree: DerivationTree) -> tuple[str, str]:
        pair = tree.children[0]  # <start> → <expr>
        a = str(pair.children[0])  # <expr> → <term> ", " <term>
        b = str(pair.children[2])
        return a, b

    @staticmethod
    def extract_elements_recursive(tree: DerivationTree, expected_count: int = None) -> tuple:
        """
        Extract elements from a derivation tree with recursive structure.

        Handles grammar structures where expr -> term, expr -> term, expr -> ... -> term

        Args:
            tree: The derivation tree to extract elements from
            expected_count: Optional number of elements to expect (for validation)

        Returns:
            A tuple containing the extracted elements
        """
        elements = []

        def collect_terms(node: DerivationTree):
            if not hasattr(node, 'children') or not node.children:
                # Base case: this is a leaf node
                print(f"Found leaf node: {node}")
                elements.append(str(node))
                return

            # Check if this is a term node
            if node.is_terminal():
                print(f"Found terminal node: {node}")
                elements.append(str(node))
                return

            # Process all children
            for child in node.children:
                collect_terms(child)

        # Start collecting from the root
        collect_terms(tree)

        # Remove any empty strings or separator elements
        elements = [e for e in elements if e and e.strip() and e.strip() != ',']

        # Check if we have the expected number of elements
        if expected_count is not None and len(elements) != expected_count:
            raise ValueError(f"Expected {expected_count} elements, but found {len(elements)}")

        return tuple(elements)

    # TODO compare with extract_elements_recursive
    @staticmethod
    def extract_elements_and_clean(tree: DerivationTree, expected_count: int = None) -> tuple:
        """
        Extract elements from a derivation tree and clean up any comma separators.

        Args:
            tree: The derivation tree to extract elements from
            expected_count: Optional number of elements to expect (for validation)

        Returns:
            A tuple containing the cleaned extracted elements
        """
        # Get to the expression node
        expr_node = tree.children[0]  # <start> → <expr>

        # Extract all raw elements
        raw_elements = []
        current_node = expr_node

        # Keep extracting until we reach the end of the recursive structure
        while hasattr(current_node, 'children') and current_node.children:
            # First child is always a term
            raw_elements.append(str(current_node.children[0]))

            # If there are more children, continue with second child
            if len(current_node.children) > 2:
                current_node = current_node.children[2]  # 2 is the index to skip the separator (comma)
            else:
                break

        # Check if we have the expected number of elements
        if expected_count is not None and len(raw_elements) != expected_count:
            raise ValueError(f"Expected {expected_count} elements, but found {len(raw_elements)}")

        return tuple(raw_elements)