# PInT: Property Inference Toolkit

PInT is a research prototype implementing the ideas from the thesis *"Inferring Properties from Input‑Output Behavior"*. The toolkit automatically generates test inputs, runs user-supplied functions, and infers which mathematical properties hold based solely on observed behavior. It is built around grammar‑based fuzzing, a library of property patterns, and an optional feedback loop that refines input constraints.

## Architecture Overview

The codebase mirrors the architecture described in the thesis.

### Generation Component
*Path: [`core/generation/`](core/generation)*

This module is responsible for preparing test inputs. `InputGenerator` builds grammars and produces examples using Fandango:
```python
class InputGenerator:
    """Handles generation of test inputs using grammars and Fandango."""
```
User modules can specify overrides for converters, grammars or parsers via helpers in `user_module_loader.py`.

### Execution Component
*Paths: [`core/property_inference_engine.py`](core/property_inference_engine.py), [`core/evaluation/`](core/evaluation), [`util/function_under_test.py`](util/function_under_test.py)*

`PropertyInferenceEngine` orchestrates the workflow by combining input generation, property evaluation and constraint inference:
```python
class PropertyInferenceEngine:
    """
    Orchestrates the property inference process using generation, evaluation, and correlation modules.
    This engine coordinates:
    1. Input generation using grammar-based fuzzing
    2. Property evaluation against functions under test
    3. Constraint inference and feedback loops for improved testing
```
Execution of user functions is handled through the `FunctionUnderTest` abstraction, which converts arguments and compares results.

### Library of Property Patterns
*Path: [`core/evaluation/library/`](core/evaluation/library)*

The library is organized into structural, compositional and behavioral tests. Registries defined in `__init__.py` group these patterns for different use cases:
```python
def create_symmetry_registry() -> PropertyRegistry:
    """Registry for testing argument order and position relationships."""
    registry = PropertyRegistry()
    # Basic commutativity for binary functions
    registry.register(CommutativityTest())
```
`PropertyRegistry` stores tests by name and category for easy retrieval.

### Constraint Refinement
*Path: [`core/correlation/`](core/correlation)*

When feedback is enabled, failing traces are analyzed to propose new grammar constraints. `ConstraintInferenceEngine` delegates to models such as `LocalModel` that use a language model service. Prompts are built by `PromptBuilder`:
```python
class PromptBuilder:
    """Builder for creating constraint inference prompts."""
```
The engine applies newly inferred constraints in a loop until the property holds or the attempt limit is reached.

## Setup and Usage

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Make the CLI executable:
   ```bash
    chmod +x ./pint
   ```
3. Run the command line tool:
   ```bash
   ./pint -f input/calculator.py
   ```
   The CLI allows selecting registries, properties, and enabling advanced feedback iterations.

## Contributing

Contributions are welcome in the form of additional property tests or improvements to the inference engine. Please open an issue or pull request to discuss proposed changes.
