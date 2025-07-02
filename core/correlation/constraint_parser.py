from util.grammar_config import GrammarConfig


class ConstraintParser:
    """Parser for extracting valid constraints from model output."""

    @staticmethod
    def parse_constraints(raw_text: str, grammar: GrammarConfig) -> list[str]:
        """Parse and validate constraints from raw model output."""
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
        valid_constraints = []

        for line in lines:
            # Skip explanation lines
            if ConstraintParser._is_explanation_line(line):
                continue

            # Validate and collect constraints
            if grammar.validate_constraint(line):
                valid_constraints.append(line)

        return valid_constraints

    @staticmethod
    def _is_explanation_line(line: str) -> bool:
        """Check if a line is an explanation rather than a constraint."""
        explanation_keywords = ['analysis:', 'explanation:', 'note:', 'based on']
        return any(word in line.lower() for word in explanation_keywords)