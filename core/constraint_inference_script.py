#!/usr/bin/env python3
"""
External constraint inference script for use with PythonScriptModel.

This script reads test results from stdin as JSON and outputs constraints
as JSON to stdout.

Usage: python constraint_inference_script.py < test_results.json
"""

import sys
import json
from typing import Any, Dict, List, Tuple


def analyze_numeric_patterns(test_cases: List[Dict[str, Any]]) -> List[str]:
    """Analyze numeric patterns in test cases to infer constraints."""
    constraints = []

    # Separate passing and failing cases
    passing = [tc for tc in test_cases if tc['passed']]
    failing = [tc for tc in test_cases if not tc['passed']]

    if not failing:
        return constraints

    # Analyze each input position
    num_inputs = len(failing[0]['inputs']) if failing else 0

    for pos in range(num_inputs):
        # Collect values at this position
        passing_vals = []
        failing_vals = []

        for tc in passing:
            try:
                val = float(tc['inputs'][pos])
                passing_vals.append(val)
            except (ValueError, TypeError, IndexError):
                pass

        for tc in failing:
            try:
                val = float(tc['inputs'][pos])
                failing_vals.append(val)
            except (ValueError, TypeError, IndexError):
                pass

        if not failing_vals:
            continue

        var_name = "<term>" if pos == 0 else f"<term_{pos + 1}>"

        # Check for specific patterns

        # Pattern 1: All failures are zero
        if all(v == 0 for v in failing_vals) and 0 not in passing_vals:
            constraints.append(f"int({var_name}) != 0")

        # Pattern 2: All failures are negative
        elif all(v < 0 for v in failing_vals) and passing_vals:
            if all(v >= 0 for v in passing_vals):
                constraints.append(f"int({var_name}) >= 0")

        # Pattern 3: Range constraints
        elif passing_vals and failing_vals:
            # Check if failures are all outside a range
            if passing_vals:
                p_min, p_max = min(passing_vals), max(passing_vals)

                # All failures below range
                if all(v < p_min for v in failing_vals):
                    constraints.append(f"int({var_name}) >= {int(p_min)}")

                # All failures above range
                elif all(v > p_max for v in failing_vals):
                    constraints.append(f"int({var_name}) <= {int(p_max)}")

                # Failures at both extremes, passing in middle
                elif any(v < p_min for v in failing_vals) and any(v > p_max for v in failing_vals):
                    constraints.append(f"int({var_name}) >= {int(p_min)}")
                    constraints.append(f"int({var_name}) <= {int(p_max)}")

    return constraints


def analyze_relationship_patterns(test_cases: List[Dict[str, Any]]) -> List[str]:
    """Analyze relationships between inputs."""
    constraints = []

    failing = [tc for tc in test_cases if not tc['passed']]
    passing = [tc for tc in test_cases if tc['passed']]

    if len(failing) == 0 or len(failing[0]['inputs']) < 2:
        return constraints

    # Check for patterns where inputs are equal (often breaks properties)
    equal_failing = 0
    equal_passing = 0

    for tc in failing:
        try:
            if len(tc['inputs']) >= 2:
                val1 = float(tc['inputs'][0])
                val2 = float(tc['inputs'][1])
                if val1 == val2:
                    equal_failing += 1
        except (ValueError, TypeError):
            pass

    for tc in passing:
        try:
            if len(tc['inputs']) >= 2:
                val1 = float(tc['inputs'][0])
                val2 = float(tc['inputs'][1])
                if val1 == val2:
                    equal_passing += 1
        except (ValueError, TypeError):
            pass

    # If many failures have equal inputs but passing cases don't
    if equal_failing > len(failing) * 0.8 and equal_passing < len(passing) * 0.2:
        constraints.append("int(<term>) != int(<term_2>)")

    return constraints


def infer_constraints_from_property(
        property_name: str,
        test_cases: List[Dict[str, Any]]
) -> List[str]:
    """Infer constraints based on the property being tested."""
    constraints = []

    # Property-specific inference
    if property_name == "Commutativity":
        # For commutativity failures, often one operand being zero breaks it
        for tc in test_cases:
            if not tc['passed'] and len(tc['inputs']) >= 2:
                # Check if the issue is with zero
                if '0' in [str(inp) for inp in tc['inputs']]:
                    # Might need non-zero constraints
                    constraints.extend(analyze_numeric_patterns(test_cases))
                    break

    elif property_name == "Associativity":
        # Associativity often fails with overflow or special values
        constraints.extend(analyze_numeric_patterns(test_cases))

        # Add range constraints to prevent overflow
        failing_vals = []
        for tc in test_cases:
            if not tc['passed']:
                for inp in tc['inputs']:
                    try:
                        failing_vals.append(abs(float(inp)))
                    except (ValueError, TypeError):
                        pass

        if failing_vals and max(failing_vals) > 1000:
            # Large values might cause overflow
            constraints.append("abs(int(<term>)) <= 1000")

    elif "Identity" in property_name:
        # Identity element tests need specific value constraints
        constraints.extend(analyze_numeric_patterns(test_cases))

    return constraints


def main():
    """Main entry point for the script."""
    try:
        # Read input from stdin
        input_data = json.loads(sys.stdin.read())

        # Extract relevant information
        function_name = input_data.get('function_name', 'unknown')
        property_name = input_data.get('property_name', 'unknown')
        test_cases = input_data.get('test_cases', [])
        current_constraints = input_data.get('current_constraints', [])
        iteration = input_data.get('iteration', 1)

        # Infer constraints using multiple strategies
        all_constraints = []

        # Strategy 1: Numeric pattern analysis
        all_constraints.extend(analyze_numeric_patterns(test_cases))

        # Strategy 2: Relationship analysis
        all_constraints.extend(analyze_relationship_patterns(test_cases))

        # Strategy 3: Property-specific analysis
        all_constraints.extend(infer_constraints_from_property(property_name, test_cases))

        # Remove duplicates and filter out already applied constraints
        unique_constraints = []
        for c in all_constraints:
            if c not in unique_constraints and c not in current_constraints:
                unique_constraints.append(c)

        # Calculate confidence based on evidence
        confidence = 0.5
        if unique_constraints:
            # Higher confidence if we found clear patterns
            num_failing = sum(1 for tc in test_cases if not tc['passed'])
            if num_failing > 0:
                confidence = min(0.9, 0.5 + (len(unique_constraints) / num_failing) * 0.4)

        # Prepare reasoning
        reasoning_parts = []
        if any('!= 0' in c for c in unique_constraints):
            reasoning_parts.append("Found division by zero or zero-value issues")
        if any('>=' in c or '<=' in c for c in unique_constraints):
            reasoning_parts.append("Found range constraints")
        if any('!=' in c and '<term>' in c and '<term_2>' in c for c in unique_constraints):
            reasoning_parts.append("Found relationship constraints between inputs")

        reasoning = "; ".join(reasoning_parts) if reasoning_parts else "Applied pattern matching"

        # Output result
        result = {
            "constraints": unique_constraints,
            "confidence": confidence,
            "reasoning": reasoning
        }

        print(json.dumps(result, indent=2))

    except Exception as e:
        # On error, return empty constraints
        error_result = {
            "constraints": [],
            "confidence": 0.0,
            "reasoning": f"Error in constraint inference: {str(e)}"
        }
        print(json.dumps(error_result, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()