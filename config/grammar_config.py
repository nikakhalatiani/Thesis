class GrammarConfig:
    def __init__(self, path: str, extra_constraints: list[str] | None = None) -> None:
        self.path = path
        self.extra_constraints = extra_constraints or []

    def with_additional_constraints(self, new_constraints: list[str]) -> 'GrammarConfig':
        """Return a new GrammarConfig with additional constraints appended."""
        combined_constraints = list(self.extra_constraints) + new_constraints
        return GrammarConfig(self.path, combined_constraints)

    def __str__(self) -> str:
        return f"GrammarConfig(path={self.path}, extra_constraints={self.extra_constraints})"

    def __repr__(self) -> str:
        return self.__str__()