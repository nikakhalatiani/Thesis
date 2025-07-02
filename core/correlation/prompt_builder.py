from util.grammar_config import GrammarConfig
from core.library.property_test import ExecutionTrace


class PromptBuilder:
    """Builder for creating constraint inference prompts."""

    @staticmethod
    def build_constraint_prompt(traces: list[ExecutionTrace], grammar: GrammarConfig) -> str:
        """Build a prompt for constraint inference."""
        nonterminals = grammar.nonterminals()
        nonterminals_text = ", ".join(f"<{nt}>" for nt in nonterminals)

        examples_text = PromptBuilder._get_examples_text()
        cheatsheet = PromptBuilder._get_cheatsheet()
        cases_text = PromptBuilder._format_traces(traces)

        return (
            "You are an expert in mathematical property testing and constraint inference.\n"
            "Your main goal is to analyze the provided execution traces and discover correlations "
            "between the patterns of passing and failing inputs.\n"
            "You must generate new constraints that, when applied, will cause future generated inputs "
            "to follow these correlations—so that inputs likely to pass the property are included, "
            "and those likely to fail are excluded.\n\n"
            f"{examples_text}\n\n"
            f"{cheatsheet}\n"
            "IMPORTANT: Only use non-terminals listed below.\n"
            f"Available grammar nonterminals: {nonterminals_text}\n"
            "Do NOT invent or use any nonterminals that are not present in the grammar.\n"
            "- Cast to int() **only** non-terminals that expand exclusively to plain digits.\n"
            "- Cast to len() **only** non-terminals that expand to strings or sequences.\n"
            f"Current constraints: {grammar.extra_constraints or 'None'}\n\n"
            f"{cases_text}\n\n"
            "Feedback Loop Instructions:\n"
            "- Carefully compare the patterns in passing and failing execution traces.\n"
            "- IMPORTANT: You must produce NEW constraints that are different from existing ones. "
            "Repeating existing constraints is not optimal as it clearly won't change the outcome.\n"
            "- Your main objective is to propose Fandango constraint expressions that will generate inputs matching "
            "the observed correlations: inputs that pass should be allowed, and those that fail should be excluded.\n"
            "- Prefer constraints that are as general as possible, while still excluding the failing cases.\n"
            "- Each constraint must use only the allowed grammar nonterminals.\n"
            "- Constraints must be syntactically valid for the Fandango constraint system.\n"
            "- Focus on constraints that are likely to distinguish between passing and failing input patterns.\n"
            "- Return only the constraint expressions, one per line, with no extra explanation.\n"
        )

    @staticmethod
    def _get_examples_text() -> str:
        """Get examples text for the prompt."""
        valid_examples = [
            "int(<number>) != 0",
            "abs(int(<number>)) >= 1",
            "int(<number>) == int(<number>)",
            "int(<number>) + int(<number>) < 100",
            "len(<word>) > 0",
        ]

        invalid_examples = [
            "int(<term>) != 0                        # <term> may be algebraic text",
            "int(<expr>) == int(<expr>)              # <expr> can expand to '1,2'",
            "<number> > 10                           # raw NT not allowed",
        ]

        return (
                "Examples of valid constraints:\n"
                + "\n".join(f"- {c}" for c in valid_examples)
                + "\n\nExamples of invalid constraints:\n"
                + "\n".join(f"- {c}" for c in invalid_examples)
        )

    @staticmethod
    def _get_cheatsheet() -> str:
        """Get cheatsheet text for the prompt."""
        return (
            "ALLOWED CONSTRUCTS:\n"
            "int(<numeric_nt>) – where <numeric_nt> expands to digits only\n"
            "len(<string_nt>) – where <string_nt> expands to a sequence of characters\n"
            "abs(), min(), max(), sum() on numeric expressions already wrapped in int()\n"
            "\n"
            "FORBIDDEN CONSTRUCTS (never output these):\n"
            "int(<any_nt>) if <any_nt> may contain non-digits or commas\n"
            "len(<numeric_nt>)\n"
            "Mixing int() and len() in the same comparison\n"
            "Using raw <nonterminal> without a wrapper\n"
        )

    @staticmethod
    def _format_traces(traces: list[ExecutionTrace]) -> str:
        """Format execution traces for the prompt."""
        passing_traces = [t for t in traces if t.get("comparison_result")]
        failing_traces = [t for t in traces if not t.get("comparison_result")]

        lines = []

        if passing_traces:
            prop = passing_traces[0]["property_name"]
            lines.append(f"PASSING TEST CASES for {prop}:")
            for trace in passing_traces:
                lines.append(f"  input={trace['input']}")
        else:
            lines.append("NO PASSING TEST CASES")

        if failing_traces:
            prop = failing_traces[0]["property_name"]
            lines.append(f"\nFAILING TEST CASES for {prop}:")
            for trace in failing_traces:
                lines.append(f"  input={trace['input']}")
        else:
            lines.append("\nNO FAILING TEST CASES")

        return "\n".join(lines)