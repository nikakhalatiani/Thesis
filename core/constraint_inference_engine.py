from abc import ABC, abstractmethod
import json
import os
from urllib import request, error

from config.grammar_config import GrammarConfig
from core.properties.property_test import ExecutionTrace

from dotenv import load_dotenv

load_dotenv()


class ConstraintModel(ABC):
    """Model interface for inferring constraints from execution traces."""

    @abstractmethod
    def infer_constraints(self, traces: list[ExecutionTrace], grammar: GrammarConfig) -> list[str]:
        """Return a list of constraint expressions using grammar nonterminals."""
        ...


class ConstraintInferenceEngine:
    """Engine coordinating constraint inference and grammar updates."""

    def __init__(self, model: ConstraintModel) -> None:
        self.model = model

    def infer(self, traces: list[ExecutionTrace], grammar: GrammarConfig) -> list[str]:
        """Infer new constraints from execution traces."""
        return self.model.infer_constraints(traces, grammar)


class GeminiModel(ConstraintModel):
    """Inference model backed by the Gemini generative API (v1beta, generateContent)."""

    def __init__(self, api_key: str | None = None, model: str = "gemini-2.0-flash") -> None:
        if api_key is None:
            api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("Gemini API key not provided. Please set GEMINI_API_KEY in your environment or .env file.")
        self.api_key = api_key
        self.model = model

    def _build_prompt(self, traces: list[ExecutionTrace], grammar: GrammarConfig) -> str:
        nonterminals = grammar.nonterminals()
        nonterminals_text = ", ".join(f"<{nt}>" for nt in nonterminals)

        # Few-shot examples
        valid_examples = [
            "int(<number>) >= 0",
            "len(<set>) > >",
            "5 <= int(<number>)",
            "len(<set>) != 2  #  prevent generating empty sets",
            "int(<number_to_add>) == int(<number>)"

        ]
        invalid_examples = [
            "int(<set>) >= 0   # invalid: cannot convert set to int",
            "int(<elements>) == 0  # invalid: cannot convert elements to int",
            "len(<number>) > 0    # invalid: cannot take length of a number"
        ]
        examples_text = (
                "Examples of valid constraints:\n"
                + "\n".join(f"- {c}" for c in valid_examples)
                + "\n\nExamples of invalid constraints:\n"
                + "\n".join(f"- {c}" for c in invalid_examples)
        )

        # Prepare trace descriptions
        passing_traces = [t for t in traces if t.get("comparison_result")]
        failing_traces = [t for t in traces if not t.get("comparison_result")]

        lines = ["PASSING TEST CASES:"]
        for trace in passing_traces:
            lines.append(f"  input={trace['input']}, property={trace['property_name']}")

        lines.append("\nFAILING TEST CASES:")
        for trace in failing_traces:
            lines.append(f"  input={trace['input']}, property={trace['property_name']}")

        cases_text = "\n".join(lines)

        return (
            "You are an expert in mathematical property testing and constraint inference.\n"
            "Your main goal is to analyze the provided execution traces and discover correlations "
            "between the patterns of passing and failing inputs.\n"
            "You must generate new constraints that, when applied, will cause future generated inputs "
            "to follow these correlations—so that inputs likely to pass the property are included, "
            "and those likely to fail are excluded.\n\n"
            "Examples of valid Fandango constraints:\n"
            f"{examples_text}\n\n"
            "IMPORTANT: Only use nonterminals that are explicitly listed in the grammar below when writing constraints.\n"
            "Do NOT invent or use any nonterminals that are not present in the grammar.\n"
            "- Use int(<nonterminal>) for numeric comparisons, e.g., int(<number>) >= 0.\n\n"
            f"Available grammar nonterminals: {nonterminals_text}\n"
            f"Current constraints: {grammar.extra_constraints or 'None'}\n\n"
            f"{cases_text}\n\n"
            "Feedback Loop Instructions:\n"
            "- Carefully compare the patterns in passing and failing execution traces.\n"
            "- Pay attention to the converted_input values which show how inputs were processed.\n"
            "- Consider candidate values and positions for identity/absorbing element properties.\n"
            "- Your main objective is to propose Fandango constraint expressions that will generate inputs matching "
            "the observed correlations: inputs that pass should be allowed, and those that fail should be excluded.\n"
            "- Prefer constraints that are as general as possible, while still excluding the failing cases.\n"
            "- Avoid constraints that are overly specific to the current set of passing examples.\n"
            "- If multiple constraints are possible, choose the one that allows the broadest set of passing inputs.\n"
            "- Each constraint must use only the allowed grammar nonterminals.\n"
            "- Constraints must be syntactically valid for the Fandango constraint system.\n"
            "- Focus on constraints that are likely to distinguish between passing and failing input patterns.\n"
            "- Return only the constraint expressions, one per line, with no extra explanation.\n"
        )

    def infer_constraints(self, traces: list[ExecutionTrace], grammar: GrammarConfig) -> list[str]:
        if not traces:
            return []
        prompt = self._build_prompt(traces, grammar)

        url = (
            "https://generativelanguage.googleapis.com/v1beta/"
            f"models/{self.model}:generateContent?key={self.api_key}"
        )

        body = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.3, "maxOutputTokens": 500, "topP": 0.8},
        }
        data = json.dumps(body).encode("utf-8")

        req = request.Request(url, data=data, method="POST") # type: ignore[arg-type]
        req.add_header("Content-Type", "application/json")

        try:
            with request.urlopen(req) as resp:
                resp_data = json.load(resp)
        except error.HTTPError as e:
            if e.code == 404:
                raise RuntimeError(f"Gemini endpoint not found: check API version & model name ({self.model})") from e
            elif e.code == 400:
                raise RuntimeError("Gemini API error (400): Invalid request - check API key and model") from e
            raise RuntimeError(f"Gemini request failed: {e.reason}") from e

        try:
            raw_text = resp_data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError, TypeError):
            raise RuntimeError("Unexpected Gemini response structure")

        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
        valid_constraints = []
        for line in lines:
            if any(word in line.lower() for word in ['analysis:', 'explanation:', 'note:', 'based on']):
                continue
            if grammar.validate_constraint(line):
                valid_constraints.append(line)
        return valid_constraints

