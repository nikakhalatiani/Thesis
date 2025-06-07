class GrammarConfig:
    def __init__(self, path: str, extra_constraints: list[str] | None = None) -> None:
        self.path = path
        self.extra_constraints = extra_constraints

    def __str__(self) -> str:
        return f"GrammarConfig(path={self.path}, extra_constraints={self.extra_constraints})"