from abc import ABC, abstractmethod

from util.grammar_config import GrammarConfig
from core.evaluation.library import ExecutionTrace


class ConstraintModel(ABC):
    """Model interface for inferring constraints from execution traces."""

    @abstractmethod
    def infer_constraints(self, traces: list[ExecutionTrace], grammar: GrammarConfig) -> list[str]:
        """Return a list of constraint expressions using grammar nonterminals."""
        ...