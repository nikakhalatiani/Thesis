from util.grammar_config import GrammarConfig
from core.evaluation.library import ExecutionTrace
from .constraint_model import ConstraintModel
from .model_services import ModelService, ServiceHealthChecker
from .prompt_builder import PromptBuilder
from .constraint_parser import ConstraintParser


class LocalModel(ConstraintModel):
    """Local inference model using dependency injection for better testability."""

    def __init__(
            self,
            model_service: ModelService,
            health_checker: ServiceHealthChecker | None = None,
            prompt_builder: PromptBuilder | None = None,
            constraint_parser: ConstraintParser | None = None
    ):
        self.model_service = model_service
        self.health_checker = health_checker
        self.prompt_builder = prompt_builder or PromptBuilder()
        self.constraint_parser = constraint_parser or ConstraintParser()

        # Ensure service is healthy if health checker is provided
        if self.health_checker:
            self.health_checker.start_if_needed()

    def infer_constraints(self, traces: list[ExecutionTrace], grammar: GrammarConfig) -> list[str]:
        """Infer constraints using the injected model service."""
        if not traces:
            return []

        prompt = self.prompt_builder.build_constraint_prompt(traces, grammar)

        try:
            raw_text = self.model_service.generate(prompt)
            return self.constraint_parser.parse_constraints(raw_text, grammar)
        except Exception as e:
            raise RuntimeError(f"Constraint inference failed: {e}")