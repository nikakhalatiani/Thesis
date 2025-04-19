from typing import Any

from fandango import FandangoParseError, Fandango
from fandango.language.tree import DerivationTree

from collections.abc import Callable


class InputParser:
    """
    A parser that extracts inputs from a derivation tree using a specified extraction strategy.
    """

    def __init__(self, extraction_strategy: Callable):
        """
        Initialize the InputParser with an extraction strategy.

        Args:
            extraction_strategy: A function that takes a parse tree and returns the extracted inputs.
        """
        self.extraction_strategy = extraction_strategy

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
            for tree in fan.parse(tree):
                return self.extraction_strategy(tree)
        except FandangoParseError as e:
            print(f"❌ Parsing failed at position {e.position} in '{tree}'")
        return None