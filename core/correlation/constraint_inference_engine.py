from util.grammar_config import GrammarConfig
from core.evaluation.library import ExecutionTrace
from .constraint_model import ConstraintModel


class ConstraintInferenceEngine:
    """Engine coordinating constraint inference and grammar updates."""

    def __init__(self, model: ConstraintModel) -> None:
        self.model = model

    def infer(self, traces: list[ExecutionTrace], grammar: GrammarConfig) -> list[str]:
        """Infer new constraints from execution traces."""
        return self.model.infer_constraints(traces, grammar)