class GrammarConfig:
    def __init__(self, path: str, extra_constraints: list[str] | None = None) -> None:
        self.path = path
        self.extra_constraints = extra_constraints