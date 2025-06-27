class GrammarConfig:
    def __init__(self, path: str, extra_constraints: list[str] | None = None) -> None:
        self.path = path
        self.extra_constraints = extra_constraints

    def __str__(self) -> str:
        return f"GrammarConfig(path={self.path}, extra_constraints={self.extra_constraints})"

    def with_additional_constraints(self, constraints: list[str]) -> "GrammarConfig":
        """Return a new GrammarConfig with extra constraints appended."""
        new_constraints = list(self.extra_constraints) if self.extra_constraints else []
        new_constraints.extend(constraints)
        return GrammarConfig(self.path, new_constraints)