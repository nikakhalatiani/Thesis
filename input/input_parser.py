from fandango import FandangoParseError, Fandango
from fandango.language.tree import DerivationTree, NonTerminal

from collections.abc import Callable


class InputParser:
    """
    A parser that extracts inputs from a derivation tree using a specified extraction strategy.

    Attributes:
            extraction_strategy: A function that takes a parse tree and returns the extracted inputs.
    """

    def __init__(self, extraction_strategy: Callable) -> None:

        self.extraction_strategy: Callable = extraction_strategy

    def parse(self, fan: Fandango, tree: DerivationTree) -> tuple | None:
        """
        Parse a derivation tree and extract inputs using the extraction strategy.

        Args:
            fan: The Fandango object used for parsing.
            tree: The derivation tree to parse.

        Returns:
            The extracted inputs if parsing is successful, otherwise None.

        Raises:
            Parsing errors are handled internally and ``None`` is returned on
            failure.
        """
        try:
            for tree in fan.parse(tree):
                return self.extraction_strategy(tree)
        except FandangoParseError as e:
            print(f"❌ Parsing failed at position {e.position} in '{tree}'")
        return None

    @staticmethod
    def extract_all_numbers_with_tree_api(tree: DerivationTree) -> tuple[str, ...]:
        """
        Extract every <number> subtree in one go, using the tree API,
        and return their string values in the order they appear.
        """
        # Construct the NonTerminal
        number_nt = NonTerminal("<number>")

        # Walk the entire tree
        number_nodes = tree.find_all_trees(number_nt)

        elements = tuple(node.to_string() for node in number_nodes)

        return elements

    @staticmethod
    def old_basic_recursion_with_built_in_detector(tree: DerivationTree) -> tuple[str, ...]:

        elements: list[str] = []

        def visit(node: DerivationTree):
            children = node.children
            # If this node has children and its entire text is a number, treat it as one <number>
            if children and node.is_num():
                elements.append(node.to_string())
                return
            # Otherwise, recurse into all children
            for child in children:
                visit(child)

        visit(tree)

        print(elements)
        return tuple(elements)

    @staticmethod
    def basic_recursion_with_built_in_detector(tree: DerivationTree) -> tuple[str, ...]:

        elements: list[str] = []

        def visit(node: DerivationTree):
            if node.is_num():
                # Get the actual value represented by the node
                value = node.value()
                if value is not None:
                    elements.append(str(value))
                return

            for child in node.children:
                visit(child)

        visit(tree)

        return tuple(elements)
