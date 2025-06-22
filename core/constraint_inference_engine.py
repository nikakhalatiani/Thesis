from abc import ABC, abstractmethod
from typing import Any, TypedDict
from dataclasses import dataclass
import json
import subprocess
import requests
from core.properties.property_test import TestResult


class TestCase(TypedDict):
    """Represents a single test case with inputs, output, and pass/fail status."""
    inputs: list[Any]
    output: Any
    passed: bool


class InferenceInput(TypedDict):
    """Input format for constraint inference models."""
    function_name: str
    property_name: str
    test_cases: list[TestCase]
    current_constraints: list[str]
    iteration: int


class InferenceOutput(TypedDict):
    """Output format from constraint inference models."""
    constraints: list[str]  # Python expressions compatible with Fandango
    confidence: float  # Optional confidence score
    reasoning: str  # Optional explanation


@dataclass
class ConstraintInferenceResult:
    """Result of constraint inference including the constraints and metadata."""
    constraints: list[str]
    confidence: float = 1.0
    reasoning: str = ""

    def to_fandango_constraint(self) -> str:
        """Convert constraints to a single Fandango-compatible constraint string."""
        if not self.constraints:
            return ""
        return " and ".join(f"({c})" for c in self.constraints)


class ConstraintInferenceModel(ABC):
    """Abstract base class for constraint inference models."""

    @abstractmethod
    def infer_constraints(self, inference_input: InferenceInput) -> ConstraintInferenceResult:
        """
        Infer constraints from test results.

        Args:
            inference_input: Test results and metadata

        Returns:
            ConstraintInferenceResult with inferred constraints
        """
        pass

    def validate_constraint(self, constraint: str) -> bool:
        """Validate that a constraint is valid Python syntax."""
        try:
            compile(constraint, '<string>', 'eval')
            return True
        except SyntaxError:
            return False


class RuleBasedModel(ConstraintInferenceModel):
    """Simple rule-based model for constraint inference."""

    def infer_constraints(self, inference_input: InferenceInput) -> ConstraintInferenceResult:
        """Infer constraints using simple heuristics."""
        constraints = []
        test_cases = inference_input['test_cases']

        # Separate passing and failing cases
        passing_cases = [tc for tc in test_cases if tc['passed']]
        failing_cases = [tc for tc in test_cases if not tc['passed']]

        if not failing_cases:
            return ConstraintInferenceResult(constraints=[])

        # Try to find patterns in failing cases
        # Example: For numeric inputs, find range constraints
        for i, _ in enumerate(failing_cases[0]['inputs']):
            input_values = []

            # Collect all input values at position i
            for tc in test_cases:
                if i < len(tc['inputs']):
                    val = tc['inputs'][i]
                    # Handle string representations of numbers
                    if isinstance(val, str) and val.replace('-', '').replace('.', '').isdigit():
                        try:
                            val = float(val) if '.' in val else int(val)
                        except ValueError:
                            continue
                    if isinstance(val, (int, float)):
                        input_values.append((val, tc['passed']))

            if input_values:
                # Find range constraints
                passing_vals = [v for v, passed in input_values if passed]
                failing_vals = [v for v, passed in input_values if not passed]

                if passing_vals and failing_vals:
                    # Check if there's a clear boundary
                    min_passing = min(passing_vals) if passing_vals else float('inf')
                    max_passing = max(passing_vals) if passing_vals else float('-inf')
                    min_failing = min(failing_vals) if failing_vals else float('inf')
                    max_failing = max(failing_vals) if failing_vals else float('-inf')

                    # Generate constraints based on patterns
                    var_name = f"<term>" if i == 0 else f"<term_{i + 1}>"

                    # All failures are below passing range
                    if max_failing < min_passing:
                        constraints.append(f"int({var_name}) >= {int(min_passing)}")
                    # All failures are above passing range
                    elif min_failing > max_passing:
                        constraints.append(f"int({var_name}) <= {int(max_passing)}")
                    # Check for specific values that always fail
                    elif all(v == 0 for v in failing_vals) and 0 not in passing_vals:
                        constraints.append(f"int({var_name}) != 0")

        reasoning = f"Found {len(constraints)} constraints based on {len(failing_cases)} failing cases"
        return ConstraintInferenceResult(
            constraints=constraints,
            confidence=0.8 if constraints else 0.3,
            reasoning=reasoning
        )


class PythonScriptModel(ConstraintInferenceModel):
    """Model that calls an external Python script for constraint inference."""

    def __init__(self, script_path: str):
        self.script_path = script_path

    def infer_constraints(self, inference_input: InferenceInput) -> ConstraintInferenceResult:
        """Call external script with test results."""
        try:
            # Prepare input as JSON
            input_json = json.dumps(inference_input)

            # Call the script
            result = subprocess.run(
                ['python', self.script_path],
                input=input_json,
                capture_output=True,
                text=True,
                check=True
            )

            # Parse output
            output = json.loads(result.stdout)

            # Validate constraints
            valid_constraints = [
                c for c in output.get('constraints', [])
                if self.validate_constraint(c)
            ]

            return ConstraintInferenceResult(
                constraints=valid_constraints,
                confidence=output.get('confidence', 1.0),
                reasoning=output.get('reasoning', '')
            )
        except Exception as e:
            print(f"Error calling Python script: {e}")
            return ConstraintInferenceResult(constraints=[])


class LLMAPIModel(ConstraintInferenceModel):
    """Model that uses an LLM API for constraint inference."""

    def __init__(self, api_key: str, model: str = "gpt-4", api_url: str = None):
        self.api_key = api_key
        self.model = model
        self.api_url = api_url or "https://api.openai.com/v1/chat/completions"

    def infer_constraints(self, inference_input: InferenceInput) -> ConstraintInferenceResult:
        """Use LLM to infer constraints from test results."""

        # Prepare prompt
        prompt = self._create_prompt(inference_input)

        try:
            # Call LLM API
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            data = {
                "model": self.model,
                "messages": [
                    {"role": "system",
                     "content": "You are an expert at inferring constraints from test results. Return only valid Python expressions that can be used as Fandango grammar constraints."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3,
                "response_format": {"type": "json_object"}
            }

            response = requests.post(self.api_url, headers=headers, json=data)
            response.raise_for_status()

            result = response.json()
            content = json.loads(result['choices'][0]['message']['content'])

            # Validate constraints
            valid_constraints = [
                c for c in content.get('constraints', [])
                if self.validate_constraint(c)
            ]

            return ConstraintInferenceResult(
                constraints=valid_constraints,
                confidence=content.get('confidence', 0.9),
                reasoning=content.get('reasoning', '')
            )

        except Exception as e:
            print(f"Error calling LLM API: {e}")
            return ConstraintInferenceResult(constraints=[])

    def _create_prompt(self, inference_input: InferenceInput) -> str:
        """Create a prompt for the LLM."""
        test_summary = []
        for tc in inference_input['test_cases'][:20]:  # Limit to first 20 cases
            status = "PASS" if tc['passed'] else "FAIL"
            test_summary.append(f"{status}: inputs={tc['inputs']}, output={tc['output']}")

        prompt = f"""
Analyze these test results for the {inference_input['property_name']} property of function {inference_input['function_name']}:

Test Results:
{chr(10).join(test_summary)}

Current constraints: {inference_input['current_constraints'] or 'None'}
Iteration: {inference_input['iteration']}

Based on the failing test cases, infer constraints that would exclude the failing inputs while keeping the passing ones.
Use variable names like <term>, <term_2>, etc. for referencing input positions.
Return a JSON object with:
- "constraints": list of Python expressions (e.g., ["int(<term>) > 0", "int(<term_2>) != int(<term>)"])
- "confidence": float between 0 and 1
- "reasoning": brief explanation

Only return syntactically valid Python expressions that can be evaluated.
"""
        return prompt


class MockLLMModel(ConstraintInferenceModel):
    """Mock LLM model for testing without API calls."""

    def infer_constraints(self, inference_input: InferenceInput) -> ConstraintInferenceResult:
        """Simulate LLM constraint inference."""
        # Simple mock logic: if we see failures with 0, exclude it
        constraints = []

        for tc in inference_input['test_cases']:
            if not tc['passed']:
                for i, val in enumerate(tc['inputs']):
                    if str(val) == '0':
                        var_name = "<term>" if i == 0 else f"<term_{i + 1}>"
                        constraint = f"int({var_name}) != 0"
                        if constraint not in constraints:
                            constraints.append(constraint)

        return ConstraintInferenceResult(
            constraints=constraints,
            confidence=0.85,
            reasoning="Mock inference: excluding zero values that caused failures"
        )