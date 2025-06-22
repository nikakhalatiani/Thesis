"""Enhanced main script demonstrating adaptive constraint inference."""

from typing import Any, Optional
import inspect
import importlib.util
import os

from core.properties import create_minimal_registry
from input.input_parser import InputParser
from config.property_inference_config import PropertyInferenceConfig
from core.function_under_test import (
    FunctionUnderTest,
    CombinedFunctionUnderTest,
    ComparisonStrategy,
)
from core.property_inference_engine import PropertyInferenceEngine
from config.grammar_config import GrammarConfig
from core.constraint_inference_engine import (
    ConstraintInferenceEngine,
    GeminiModel,
    SimpleNumericModel,
    MockModel
)
from core.properties.algebraic import CommutativityTest


def load_user_module(path: str):
    """Load a Python module from a file path."""
    try:
        spec = importlib.util.spec_from_file_location("user_defined_functions", path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load module from {path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception as e:
        raise ImportError(f"Failed to load module from {path}: {e}") from e


def extract_overrides(module) -> dict[str, dict[str, Any]]:
    """Extract function-specific overrides from module attributes."""
    overrides = {
        'converter': {},
        'grammar': {},
        'parser': {},
        'comparator': {}
    }

    for name, value in vars(module).items():
        if name.startswith("converter_"):
            overrides['converter'][name[len("converter_"):]] = value
        elif name.startswith("grammar_"):
            overrides['grammar'][name[len("grammar_"):]] = value
        elif name.startswith("parser_"):
            overrides['parser'][name[len("parser_"):]] = value
        elif name.startswith("comparator_"):
            overrides['comparator'][name[len("comparator_"):]] = value

    return overrides


def process_grammar_override(func_name: str, value: Any, default_grammar) -> GrammarConfig:
    """Process grammar override specification into GrammarConfig."""
    if isinstance(value, GrammarConfig):
        return value
    elif isinstance(value, str):
        return GrammarConfig(value)
    elif isinstance(value, (list, tuple)):
        try:
            if value and isinstance(value[0], str) and value[0].endswith(".fan"):
                return GrammarConfig(value[0], extra_constraints=value[1:])
            else:
                return GrammarConfig(default_grammar.path, extra_constraints=value)
        except Exception as e:
            raise ValueError(f"Invalid grammar spec for {func_name}: {value}") from e
    else:
        raise ValueError(f"Unsupported grammar type for {func_name}: {type(value)}")


def process_parser_override(func_name: str, value: Any) -> InputParser:
    """Process parser override specification into InputParser."""
    if isinstance(value, InputParser):
        return value
    elif isinstance(value, str):
        val = value.strip()
        if val.startswith("<") and val.endswith(">"):
            return InputParser.for_nonterminal(val)
        else:
            raise ValueError(f"String parser spec must be nonterminal like '<number>' for {func_name}: {value}")
    elif isinstance(value, list):
        if all(isinstance(v, str) for v in value):
            return InputParser.for_grammar_pattern(*value)
        else:
            raise ValueError(f"List parser spec must contain only strings for {func_name}: {value}")
    else:
        raise ValueError(f"Invalid parser spec for {func_name}: {value}")


def create_constraint_model(model_type: str = "simple", api_key: Optional[str] = None):
    """Create constraint inference model based on type specification."""
    if model_type.lower() == "gemini":
        if not api_key:
            raise ValueError("API key required for Gemini model")
        return GeminiModel(api_key)
    elif model_type.lower() == "simple":
        return SimpleNumericModel()
    elif model_type.lower() == "mock":
        return MockModel()
    else:
        raise ValueError(f"Unknown model type: {model_type}")


def create_constraint_engine(model, strategy: str = "replace"):
    """Create constraint inference engine with specified strategy."""
    return ConstraintInferenceEngine(model, strategy)


def print_adaptive_results(results: dict):
    """Print detailed results from adaptive feedback analysis."""
    print("\n" + "=" * 80)
    print("🎯 ADAPTIVE CONSTRAINT INFERENCE RESULTS")
    print("=" * 80)

    for function_name, function_results in results.items():
        print(f"\n📊 Function: {function_name}")
        print("-" * 60)

        for property_name, adaptive_result in function_results.items():
            final_result = adaptive_result["final_result"]
            constraints_history = adaptive_result["constraints_history"]
            iterations = adaptive_result["iterations"]
            converged = adaptive_result["converged"]

            # Status indicator
            if converged and final_result["holds"]:
                status = "✅ PASSED"
            elif converged:
                status = "🟡 CONVERGED"
            else:
                status = "🔴 FAILED"

            success_rate = (
                final_result["stats"]["success_count"] / final_result["stats"]["total_count"] * 100
                if final_result["stats"]["total_count"] > 0 else 0
            )

            print(f"\n{status} {property_name}")
            print(f"   Iterations: {iterations}")
            print(f"   Final success rate: {success_rate:.1f}%")
            print(f"   Tests run: {final_result['stats']['total_count']}")

            # Show constraint evolution
            if constraints_history:
                print(f"   Constraint evolution:")
                for i, constraints in enumerate(constraints_history, 1):
                    print(f"     Iteration {i}: {len(constraints)} constraints")
                    for constraint in constraints:
                        print(f"       • {constraint}")

            # Show final constraints
            final_grammar = adaptive_result["final_grammar"]
            if final_grammar.extra_constraints:
                print(f"   Final constraints ({len(final_grammar.extra_constraints)}):")
                for constraint in final_grammar.extra_constraints:
                    print(f"     • {constraint}")

            # Show counterexamples if any
            if not final_result["holds"] and final_result["counterexamples"]:
                print(f"   Remaining counterexamples:")
                for ex in final_result["counterexamples"][:3]:  # Show first 3
                    print(f"     • {ex.strip()}")
                if len(final_result["counterexamples"]) > 3:
                    print(f"     ... and {len(final_result['counterexamples']) - 3} more")


def main(user_funcs_path: str = "input/user_input.py",
         class_name: Optional[str] = None,
         model_type: str = "simple",
         api_key: Optional[str] = None,
         adaptive_mode: bool = True,
         max_attempts: int = 5,
         constraint_strategy: str = "replace"):
    """
    Main function with enhanced adaptive feedback capabilities.

    Args:
        user_funcs_path: Path to user-defined functions
        class_name: Specific class to test (optional)
        model_type: Type of constraint model ("simple", "gemini", "mock")
        api_key: API key for external models (required for Gemini)
        adaptive_mode: Whether to use adaptive feedback
        max_attempts: Maximum iterations for adaptive feedback
        constraint_strategy: Strategy for applying constraints ("replace", "append", "merge")
    """

    print("🚀 Starting Property-Based Testing with Adaptive Feedback")
    print(f"📁 Loading functions from: {user_funcs_path}")
    print(f"🤖 Model type: {model_type}")
    print(f"🔄 Adaptive mode: {'ON' if adaptive_mode else 'OFF'}")
    print(f"🎯 Constraint strategy: {constraint_strategy}")

    # Initialize registry and configuration
    registry = create_minimal_registry()
    default_parser = InputParser.for_numbers()

    config = (PropertyInferenceConfig(registry)
              .set_default_grammar("grammars/test.fan")
              .set_default_parser(default_parser)
              .set_comparison_strategy(ComparisonStrategy.FIRST_COMPATIBLE)
              .set_use_input_cache(True)
              .set_example_count(100)
              .set_max_counterexamples(100))

    # Load user module
    try:
        module = load_user_module(user_funcs_path)
        print(f"✅ Successfully loaded module from {user_funcs_path}")
    except Exception as e:
        print(f"❌ Failed to load module: {e}")
        return

    # Extract classes and functions
    if class_name:
        if not hasattr(module, class_name):
            print(f"❌ Class '{class_name}' not found in module")
            return
        classes = [getattr(module, class_name)]
    else:
        classes = [
            obj for obj in vars(module).values()
            if inspect.isclass(obj) and obj.__module__ == module.__name__
        ]

    if not classes:
        print("❌ No classes found in module")
        return

    print(f"📦 Found {len(classes)} class(es) to analyze")

    # Process overrides and register functions
    overrides = extract_overrides(module)
    function_count = 0

    for cls in classes:
        class_name = cls.__name__
        print(f"🔍 Processing class: {class_name}")

        for func_name, func in inspect.getmembers(cls, inspect.isfunction):
            print(f"  📝 Registering function: {func_name}")

            # Extract overrides
            comp = overrides['comparator'].get(func_name) or getattr(func, "__comparator__", None)
            conv = overrides['converter'].get(func_name) or getattr(func, "__converter__", None)
            gram = overrides['grammar'].get(func_name) or getattr(func, "__grammar__", None)
            pars = overrides['parser'].get(func_name) or getattr(func, "__parser__", None)

            # Process overrides
            if gram and not isinstance(gram, GrammarConfig):
                gram = process_grammar_override(func_name, gram, config.default_grammar)

            if pars and not isinstance(pars, InputParser):
                pars = process_parser_override(func_name, pars)

            # Create and register function under test
            fut = FunctionUnderTest(func, arg_converter=conv, result_comparator=comp)
            config.add_function(fut, grammar=gram, parser=pars)
            function_count += 1

    print(f"✅ Registered {function_count} function(s) for testing")

    if function_count == 0:
        print("❌ No functions registered for testing")
        return

    # Initialize property inference engine
    engine = PropertyInferenceEngine(config)

    if adaptive_mode:
        # Create constraint inference model
        try:
            constraint_model = create_constraint_model(model_type, api_key)
            constraint_engine = create_constraint_engine(constraint_model, constraint_strategy)
            print(f"✅ Initialized {model_type} constraint model with {constraint_strategy} strategy")
        except Exception as e:
            print(f"❌ Failed to initialize constraint model: {e}")
            return

        # Run adaptive analysis
        print("\n🔄 Starting adaptive analysis...")

        # Focus on commutativity as specified
        commutativity_test = CommutativityTest()
        target_properties = [commutativity_test]

        try:
            adaptive_results = engine.run_adaptive_analysis(
                target_properties=target_properties,
                engine=constraint_engine,
                max_attempts=max_attempts
            )

            print_adaptive_results(adaptive_results)

        except Exception as e:
            print(f"❌ Error during adaptive analysis: {e}")
            import traceback
            traceback.print_exc()

    else:
        # Run standard analysis
        print("\n🔍 Running standard property inference...")
        results = engine.run()

        print("\n📊 Standard Analysis Results:")
        print("=" * 50)

        for func_name, result in results.items():
            print(f"\n📊 Results for {func_name}:")
            for prop, outcome in result["outcomes"].items():
                holds = outcome["holds"]
                tests_run = outcome["stats"]["total_count"]
                confidence = (outcome["stats"]["success_count"] / tests_run * 100) if tests_run > 0 else 0.0
                status = "🟢" if holds else "🔴"
                decision = (
                    f"{status} {prop} "
                    f"(Confidence: {confidence:.1f}%; Tests: {tests_run})"
                )
                print(f"  {decision}")

                if outcome["counterexamples"] and not holds:
                    print("    Counterexamples:")
                    for ex in outcome["counterexamples"][:3]:
                        print(f"      • {ex.strip()}")
                    if len(outcome["counterexamples"]) > 3:
                        print(f"      ... and {len(outcome['counterexamples']) - 3} more")

    print("\n🎉 Analysis complete!")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Property-based testing with adaptive feedback")
    parser.add_argument("--file", default="input/user_input.py",
                        help="Path to user functions file")
    parser.add_argument("--class", dest="class_name",
                        help="Specific class name to test")
    parser.add_argument("--model", choices=["simple", "gemini", "mock"], default="simple",
                        help="Constraint inference model type")
    parser.add_argument("--api-key",
                        help="API key for external models")
    parser.add_argument("--no-adaptive", action="store_true",
                        help="Disable adaptive feedback mode")
    parser.add_argument("--max-attempts", type=int, default=5,
                        help="Maximum adaptive feedback iterations")
    parser.add_argument("--strategy", choices=["replace", "append", "merge"], default="replace",
                        help="Constraint application strategy")

    args = parser.parse_args()

    # Auto-detect API key from environment if not provided
    if args.model == "gemini" and not args.api_key:
        import os

        args.api_key = os.getenv("GEMINI_API_KEY")
        if not args.api_key:
            print("❌ Gemini API key required. Set GEMINI_API_KEY environment variable or use --api-key")
            exit(1)

    main(
        user_funcs_path=args.file,
        class_name=args.class_name,
        model_type=args.model,
        api_key=args.api_key,
        adaptive_mode=not args.no_adaptive,
        max_attempts=args.max_attempts,
        constraint_strategy=args.strategy
    )