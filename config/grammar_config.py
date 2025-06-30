import ast
import re


class SimpleConstraintValidator:
    """Validate constraints by combining a quick regex scan with an AST safety walk."""

    # Extend this set if you decide to allow more helper functions later.
    _ALLOWED_FUNCS: set[str] = {
        "int", "len", "str", "float", "abs", "min", "max", "sum"
    }

    def __init__(self, nonterminals: set[str]):
        self._nonterminals = nonterminals

        # Pre-compile a tiny regex so we only walk the AST if all tags look valid.
        self._tag_pattern = re.compile(r"<(\w+)>")

    def validate_constraint(self, constraint: str) -> bool:
        """
        Return True if the constraint:
        1. References only known non-terminals, and
        2. Parses as an expression containing only “safe” operations.
        """
        try:
            # ---------- 1. All <tags> must be legal NTs ----------
            for tag in self._tag_pattern.findall(constraint):
                if tag not in self._nonterminals:
                    return False

            # ---------- 2. Replace each <tag> with a dummy value and parse ----------
            dummy_expr = constraint
            for nt in self._nonterminals:
                dummy_expr = dummy_expr.replace(f"<{nt}>", "1")

            tree = ast.parse(dummy_expr, mode="eval")
            return self._is_safe(tree.body)

        except Exception:
            # Anything unexpected – treat as invalid.
            return False

    def _is_safe(self, node: ast.expr) -> bool:
        """
        A very small whitelist of node types we deem safe for simple
        arithmetic/comparison expressions.
        """
        if isinstance(node, ast.Constant):
            return isinstance(node.value, (int, float, bool))

        if isinstance(node, ast.Name):
            # Names may only appear as function identifiers for allowed calls.
            return node.id in self._ALLOWED_FUNCS

        if isinstance(node, ast.UnaryOp):
            return self._is_safe(node.operand)

        if isinstance(node, ast.BinOp):
            return self._is_safe(node.left) and self._is_safe(node.right)

        if isinstance(node, ast.BoolOp):
            return all(self._is_safe(v) for v in node.values)

        if isinstance(node, ast.Compare):
            return self._is_safe(node.left) and all(
                self._is_safe(c) for c in node.comparators
            )

        if isinstance(node, ast.Call):
            # Only plain‐name calls – no attribute lookups (e.g., math.sin)
            if isinstance(node.func, ast.Name) and node.func.id in self._ALLOWED_FUNCS:
                return all(self._is_safe(arg) for arg in node.args)
            return False

        # Anything else (Lambda, Attribute, Subscript, etc.) is rejected.
        return False


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
        """Extract all non-terminal names (e.g., <expr>) defined in this grammar."""
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                content = f.read()
            pattern = r"<(\w+)>\s*::="
            return re.findall(pattern, content)
        except Exception:
            return []

    def get_structure(self) -> str:
        """
        Return the grammar file content as-is for the model to understand production rules.
        """
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            return f"Error reading grammar file: {str(e)}"

    def validate_constraint(self, constraint: str) -> bool:
        """
        Drop-in replacement for the older regex-only validator.

        Uses the SimpleConstraintValidator for AST-backed validation.
        """
        nts: set[str] = set(self.nonterminals())
        validator = SimpleConstraintValidator(nts)
        return validator.validate_constraint(constraint)
