"""Adaptive constraint inference using model feedback."""

from typing import Protocol, TypedDict, Any
from config.grammar_config import GrammarConfig
import json
from urllib import request, error
from typing import Optional, List
import re
import os


class TestCase(TypedDict):
    """Type definition for test case data."""
    property: str
    original_args: tuple
    passed: bool
    result1: Any
    result2: Any
    # Additional fields may be present depending on the property type


class ConstraintModel(Protocol):
    """Model interface for inferring constraints from test cases."""

    def infer_constraints(self, cases: list[TestCase], grammar: GrammarConfig) -> list[str]:
        """Return a list of constraint expressions using grammar nonterminals."""


class ConstraintInferenceEngine:
    """Engine coordinating constraint inference and grammar updates."""

    def __init__(self, model: Optional[ConstraintModel] = None) -> None:
        self.model = model or SimpleNumericModel()

    def infer(self, cases: list[TestCase], grammar: GrammarConfig) -> list[str]:
        """Infer new constraints from executed test cases."""
        return self.model.infer_constraints(cases, grammar)

    @staticmethod
    def apply_constraints(grammar: GrammarConfig, constraints: list[str]) -> GrammarConfig:
        """Return updated grammar config with new constraints appended."""
        return grammar.with_additional_constraints(constraints)


class SimpleNumericModel:
    """Very small heuristic model inferring numeric ranges."""

    def infer_constraints(self, cases: list[TestCase], grammar: GrammarConfig) -> list[str]:
        """Infer simple numeric range constraints from passing test cases."""
        passing_cases = [c for c in cases if c["passed"]]
        if not passing_cases:
            return []

        # Extract numeric values from original_args
        all_values = []
        for case in passing_cases:
            for arg in case["original_args"]:
                try:
                    # Try to convert string arguments to numeric values
                    if isinstance(arg, str):
                        if arg.lstrip('-').isdigit():
                            all_values.append(int(arg))
                        else:
                            try:
                                all_values.append(float(arg))
                            except ValueError:
                                continue
                    elif isinstance(arg, (int, float)):
                        all_values.append(arg)
                except (ValueError, TypeError):
                    continue

        if not all_values:
            return []

        lo, hi = min(all_values), max(all_values)

        # Use grammar-appropriate nonterminals - assume <number> or <arg> for simplicity
        # In a real implementation, you'd parse the grammar to find the correct nonterminals
        constraints = []
        if lo >= 0:
            constraints.append(f"int(<number>) >= {lo}")
        if hi <= 100:  # Arbitrary upper bound for demonstration
            constraints.append(f"int(<number>) <= {hi}")

        return constraints


class GeminiModel:
    """Inference model backed by the Gemini generative API (v1beta, generateContent)."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-2.0-flash") -> None:
        """
        :param api_key: Google Cloud API key with Generative Language API enabled.
        :param model: Model ID as listed in Cloud Console (e.g. "gemini-2.0-flash").
        """
        # Load API key from environment if not provided
        if api_key is None:
            api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("Gemini API key not provided. Please set GEMINI_API_KEY in your environment or .env file.")
        self.api_key = api_key
        self.model = model

    def _extract_nonterminals_from_grammar(self, grammar: GrammarConfig) -> list[str]:
        """Extract nonterminal names from grammar file for constraint generation."""
        try:
            with open(grammar.path, 'r') as f:
                grammar_content = f.read()

            # Find nonterminals using regex (BNF format: <nonterminal> ::= ...)
            nonterminal_pattern = r'<(\w+)>\s*::='
            nonterminals = re.findall(nonterminal_pattern, grammar_content)
            return nonterminals
        except Exception:
            # Fallback to common nonterminals if we can't read the grammar
            return ['number', 'arg', 'term', 'expr']

    def _build_prompt(self, cases: List[TestCase], grammar: GrammarConfig) -> str:
        """Build prompt with grammar context and test case analysis."""
        nonterminals = self._extract_nonterminals_from_grammar(grammar)

        # Analyze test cases
        passing_cases = [c for c in cases if c["passed"]]
        failing_cases = [c for c in cases if not c["passed"]]

        lines = ["PASSING TEST CASES:"]
        for c in passing_cases:
            lines.append(f"  args={c['original_args']}, property={c['property']}")

        lines.append("\nFAILING TEST CASES:")
        for c in failing_cases:
            lines.append(f"  args={c['original_args']}, property={c['property']}")

        cases_text = "\n".join(lines)
        nonterminals_text = ", ".join(f"<{nt}>" for nt in nonterminals)

        return (
            "You are an expert in mathematical property testing and constraint inference.\n"
            "Your main goal is to analyze the provided test cases and discover correlations between the patterns of passing and failing inputs.\n"
            "You must generate new constraints that, when applied, will cause future generated inputs to follow these correlations—so that inputs likely to pass the property are included, and those likely to fail are excluded.\n\n"
            "IMPORTANT: Only use nonterminals that are explicitly listed in the grammar below when writing constraints.\n"
            "Do NOT invent or use any nonterminals that are not present in the grammar.\n\n"
            f"Available grammar nonterminals: {nonterminals_text}\n"
            f"Grammar file: {grammar.path}\n"
            f"Current constraints: {grammar.extra_constraints or 'None'}\n\n"
            f"{cases_text}\n\n"
            "Feedback Loop Instructions:\n"
            "- Carefully compare the patterns in passing and failing cases.\n"
            "- Your main objective is to propose Fandango constraint expressions that will generate inputs matching the observed correlations: inputs that pass should be allowed, and those that fail should be excluded.\n"
            "- Prefer constraints that are as general as possible, while still excluding the failing cases.\n"
            "- Avoid constraints that are overly specific to the current set of passing examples.\n"
            "- If multiple constraints are possible, choose the one that allows the broadest set of passing inputs.\n"
            "- Each constraint must use only the allowed grammar nonterminals.\n"
            "- Use int(<nonterminal>) for numeric comparisons, e.g., int(<number>) >= 0.\n"
            "- Constraints must be syntactically valid for the Fandango constraint system.\n"
            "- Focus on constraints that are likely to distinguish between passing and failing input patterns.\n"
            "- Return only the constraint expressions, one per line, with no extra explanation.\n"
        )

    def _validate_constraint_syntax(self, constraint: str, nonterminals: list[str]) -> bool:
        """Validate that constraint uses proper Fandango syntax."""
        # Check for basic structure: int(<nonterminal>) operator value
        pattern = r'^int\(<(\w+)>\)\s*(?:[<>]=?|==|!=)\s*(?:int\(<(\w+)>\)|-?\d+(?:\.\d+)?)$'
        match = re.match(pattern, constraint.strip())

        if not match:
            return False

        # Check that referenced nonterminals exist in grammar
        referenced_nts = [match.group(1)]
        if match.group(2):  # If comparing two nonterminals
            referenced_nts.append(match.group(2))

        return all(nt in nonterminals for nt in referenced_nts)

    def infer_constraints(self, cases: List[TestCase], grammar: GrammarConfig) -> List[str]:
        """Infer constraints via Gemini API with grammar context and validation."""
        if not cases:
            return []

        nonterminals = self._extract_nonterminals_from_grammar(grammar)
        prompt = self._build_prompt(cases, grammar)

        url = (
            "https://generativelanguage.googleapis.com/v1beta/"
            f"models/{self.model}:generateContent?key={self.api_key}"
        )

        body = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.3,  # Lower temperature for more focused output
                "maxOutputTokens": 500,
                "topP": 0.8
            }
        }
        data = json.dumps(body).encode("utf-8")

        req = request.Request(
            url,
            data=data,
            method="POST",
            headers={"Content-Type": "application/json"}
        )

        try:
            with request.urlopen(req) as resp:
                resp_data = json.load(resp)
        except error.HTTPError as e:
            if e.code == 404:
                raise RuntimeError(
                    f"Gemini endpoint not found: check API version & model name ({self.model})"
                ) from e
            elif e.code == 400:
                raise RuntimeError(f"Gemini API error (400): Invalid request - check API key and model") from e
            raise RuntimeError(f"Gemini request failed: {e.reason}") from e

        try:
            raw_text = resp_data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError, TypeError):
            raise RuntimeError("Unexpected Gemini response structure")

        # Parse and validate constraints
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
        valid_constraints = []

        for line in lines:
            # Skip lines that are clearly not constraints (explanatory text, etc.)
            if any(word in line.lower() for word in ['analysis:', 'explanation:', 'note:', 'based on']):
                continue

            if self._validate_constraint_syntax(line, nonterminals):
                valid_constraints.append(line)

        return valid_constraints