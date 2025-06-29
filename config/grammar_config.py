import re


class GrammarConfig:
    def __init__(self, path: str, extra_constraints: list[str] | None = None) -> None:
        self.path = path
        self.extra_constraints = extra_constraints

    def __str__(self) -> str:
        return f"GrammarConfig(path={self.path}, extra_constraints={self.extra_constraints})"

    def add_constraints(self, constraints: list[str]) -> "GrammarConfig":
        """Return a new GrammarConfig with extra constraints appended."""
        new_constraints = list(self.extra_constraints) if self.extra_constraints else []
        new_constraints.extend(constraints)
        return GrammarConfig(self.path, new_constraints)

    def nonterminals(self) -> list[str]:
        """Extract all nonterminal names (e.g. <expr>) defined in this grammar."""
        try:
            with open(self.path, 'r') as f:
                content = f.read()
            pattern = r'<(\w+)>\s*::='
            return re.findall(pattern, content)
        except Exception:
            return []

    def validate_constraint(self, constraint: str) -> bool:
        """Return True if `constraint` uses only allowed nonterminals,
           applies only int(...) or len(...) to nonterminals, or uses numeric literals."""
        nts = self.nonterminals()
        # Allow int(<nt>) or len(<nt>) or literal on either side of a comparison operator
        pattern = (
            r'^(?:(?:int|len)\(<(\w+)>\)|-?\d+(?:\.\d+)?)\s*'
            r'(?:[<>]=?|==|!=)\s*'
            r'(?:(?:int|len)\(<(\w+)>\)|-?\d+(?:\.\d+)?)$'
        )
        match = re.match(pattern, constraint.strip())
        if not match:
            return False

        # Extract nonterminal names used
        used = [g for g in match.groups() if g]
        # All referenced nonterminals must be in the grammar
        return all(nt in nts for nt in used)