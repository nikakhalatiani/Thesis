"""Enhanced property inference engine with rich context and better feedback loop."""

from fandango import Fandango
from fandango.language.tree import DerivationTree
from typing import TypedDict, Optional, List, Tuple, Dict, Any
from itertools import product

from config.property_inference_config import PropertyInferenceConfig
from core.function_under_test import CombinedFunctionUnderTest
from config.grammar_config import GrammarConfig
from core.properties.property_test import PropertyTest, TestResult
from core.constraint_inference_engine import ConstraintInferenceEngine, InferenceContext


class InferenceResult(TypedDict):
    """Mapping of property labels to their test outcomes."""
    outcomes: Dict[PropertyTest, TestResult]


class AdaptiveFeedbackResult(TypedDict):
    """Result of adaptive feedback process."""
    final_result: TestResult
    constraints_history: List[List[str]]
    iterations: int
    converged: bool
    final_grammar: GrammarConfig


class PropertyInferenceEngine:
    """Enhanced property inference engine with adaptive feedback capabilities."""

    def __init__(self, config: PropertyInferenceConfig) -> None:
        self.config: PropertyInferenceConfig = config
        # Cache generated input sets for function combinations
        self._input_cache: Dict[Tuple[str, ...], Optional[List[tuple]]] = {}

    def _get_inputs_for_combination(self, funcs: tuple) -> Optional[List[tuple]]:
        """Return cached inputs for ``funcs`` or generate and cache them."""
        combination_key = tuple(fut.func.__name__ for fut in funcs)
        if self.config.use_input_cache and combination_key in self._input_cache:
            cached = self._input_cache[combination_key]
            return list(cached) if cached is not None else None

        base = None
        combined_constraints: set[str] = set()

        for fut in funcs:
            fg = self.config.function_to_grammar.get(
                fut.func.__name__, self.config.default_grammar
            )
            if base is None:
                base = fg
            elif fg.path != base.path:
                print(
                    f"⚠️ Cannot combine grammars with different spec paths: "
                    f"{base.path} vs {fg.path}. Skipping combination: "
                    f"{', '.join(f.func.__name__ for f in funcs)}."
                )
                if self.config.use_input_cache:
                    self._input_cache[combination_key] = None
                return None
            if fg.extra_constraints:
                combined_constraints.update(fg.extra_constraints)

        grammar = GrammarConfig(
            base.path,
            list(combined_constraints) if combined_constraints else None,
        )

        unique_parsers = {
            self.config.function_to_parser.get(
                fut.func.__name__, self.config.default_parser
            )
            for fut in funcs
        }

        if len(unique_parsers) == 1:
            parser = unique_parsers.pop()
        else:
            print(
                f"⚠️ Cannot combine different parsers for functions: "
                f"{', '.join(fut.func.__name__ for fut in funcs)}. "
                f"Skipping combination."
            )
            if self.config.use_input_cache:
                self._input_cache[combination_key] = None
            return None

        fan, examples = self._generate_examples(grammar, self.config.example_count)
        input_sets = [parser.parse(fan, tree) for tree in examples]
        input_sets = [i for i in input_sets if i is not None]

        if self.config.use_input_cache:
            self._input_cache[combination_key] = input_sets
        return list(input_sets)

    @staticmethod
    def _generate_examples(grammar: GrammarConfig, num_examples: int) -> Tuple[Fandango, List[DerivationTree]]:
        """Generate examples using Fandango grammar with constraints."""
        path_to_grammar: str = grammar.path
        extra_constraints: Optional[List[str]] = grammar.extra_constraints

        with open(path_to_grammar) as spec_file:
            fan: Fandango = Fandango(spec_file)

            fuzz_kwargs = {
                "desired_solutions": int(num_examples),
                "population_size": int(num_examples * 2)
            }

            if extra_constraints:
                fuzz_kwargs["extra_constraints"] = extra_constraints

            try:
                examples: List[DerivationTree] = fan.fuzz(**fuzz_kwargs)
                if not examples:
                    print(f"⚠️ No examples generated with constraints: {extra_constraints}")
                    # Fallback: try without constraints
                    examples = fan.fuzz(
                        desired_solutions=int(num_examples),
                        population_size=int(num_examples * 2)
                    )
            except Exception as e:
                print(f"⚠️ Error generating examples with constraints {extra_constraints}: {e}")
                # Fallback: try without constraints
                examples = fan.fuzz(
                    desired_solutions=int(num_examples),
                    population_size=int(num_examples * 2)
                )

        return fan, examples

    @staticmethod
    def _test_property(property_test: PropertyTest,
                      function: CombinedFunctionUnderTest,
                      input_sets: List[tuple],
                      max_counterexamples: int) -> TestResult:
        """Execute property test and return structured result."""
        result = property_test.test(function, input_sets, max_counterexamples)

        return TestResult(
            holds=result['holds'],
            counterexamples=result['counterexamples'][:max_counterexamples],
            stats=result['stats'],
            cases=result.get('cases', []),
        )

    def run_with_feedback(
            self,
            prop: PropertyTest,
            fut: CombinedFunctionUnderTest,
            grammar: GrammarConfig,
            engine: ConstraintInferenceEngine,
            max_attempts: int = 5,
            min_success_rate: float = 0.95
    ) -> AdaptiveFeedbackResult:
        """
        Run property test with adaptive constraint feedback.

        Args:
            prop: Property test to run
            fut: Function under test
            grammar: Initial grammar configuration
            engine: Constraint inference engine
            max_attempts: Maximum number of iterations
            min_success_rate: Minimum success rate to consider convergence

        Returns:
            AdaptiveFeedbackResult containing the final result and iteration history
        """
        constraints_history: List[List[str]] = []
        current_grammar = grammar
        attempts = 0
        last_result: Optional[TestResult] = None

        # Set up base constraints that should be preserved
        engine.set_base_constraints(grammar.extra_constraints or [])

        print(f"🔄 Starting adaptive feedback for {prop.name} on {fut.names()[0]}")
        print(f"📊 Target success rate: {min_success_rate:.1%}, Max attempts: {max_attempts}")

        # Show initial constraints
        if grammar.extra_constraints:
            print(f"🔧 Base constraints: {grammar.extra_constraints}")

        while attempts < max_attempts:
            attempts += 1
            print(f"\n🔄 Iteration {attempts}/{max_attempts}")

            # Create inference context with rich information
            context = InferenceContext(
                property_test=prop,
                function_under_test=fut,
                grammar=current_grammar,
                previous_constraints=[c for sublist in constraints_history for c in sublist],
                iteration=attempts
            )

            # Generate inputs with current grammar
            parser = self.config.function_to_parser.get(
                fut.funcs[0].func.__name__, self.config.default_parser
            )

            try:
                fan, examples = self._generate_examples(current_grammar, self.config.example_count)
                input_sets = [parser.parse(fan, t) for t in examples]
                input_sets = [i for i in input_sets if i is not None]

                if not input_sets:
                    print("⚠️ No valid inputs generated, stopping feedback loop")
                    break

                print(f"📦 Generated {len(input_sets)} valid input sets")

            except Exception as e:
                print(f"❌ Error generating inputs: {e}")
                break

            # Run property test
            result = self._test_property(prop, fut, input_sets, self.config.max_counterexamples)
            last_result = result

            success_rate = result["stats"]["success_count"] / result["stats"]["total_count"] if result["stats"]["total_count"] > 0 else 0

            print(f"📈 Success rate: {success_rate:.1%} ({result['stats']['success_count']}/{result['stats']['total_count']})")

            # Check for convergence
            if result["holds"] or success_rate >= min_success_rate:
                print(f"✅ Converged! Property {'holds' if result['holds'] else f'achieves {success_rate:.1%} success rate'}")
                return AdaptiveFeedbackResult(
                    final_result=result,
                    constraints_history=constraints_history,
                    iterations=attempts,
                    converged=True,
                    final_grammar=current_grammar
                )

            # Infer new constraints
            print("🤖 Inferring new constraints from test results...")
            new_constraints = engine.infer(result.get("cases", []), context)

            if not new_constraints:
                print("⚠️ No new constraints inferred, stopping feedback loop")
                break

            print(f"🎯 Inferred complete constraint set ({len(new_constraints)} constraints):")
            for i, constraint in enumerate(new_constraints, 1):
                print(f"   {i}. {constraint}")

            constraints_history.append(new_constraints)

            # Apply constraints to grammar (replaces previous dynamic constraints)
            try:
                current_grammar = engine.apply_constraints(current_grammar, new_constraints)
                total_constraints = len(current_grammar.extra_constraints or [])
                base_count = len(engine.base_constraints)
                dynamic_count = total_constraints - base_count
                print(f"📝 Updated grammar: {base_count} base + {dynamic_count} dynamic = {total_constraints} total constraints")
            except Exception as e:
                print(f"❌ Error applying constraints: {e}")
                break

        # Max attempts reached without convergence
        print(f"⏱️ Reached maximum attempts ({max_attempts}) without full convergence")

        return AdaptiveFeedbackResult(
            final_result=last_result or TestResult(
                holds=False,
                counterexamples=["No tests completed"],
                stats={"total_count": 0, "success_count": 0},
                cases=[]
            ),
            constraints_history=constraints_history,
            iterations=attempts,
            converged=False,
            final_grammar=current_grammar
        )

    def run_adaptive_analysis(
            self,
            target_properties: Optional[List[PropertyTest]] = None,
            engine: Optional[ConstraintInferenceEngine] = None,
            max_attempts: int = 5
    ) -> Dict[str, Dict[str, AdaptiveFeedbackResult]]:
        """
        Run adaptive analysis on multiple functions and properties.

        Args:
            target_properties: Specific properties to test (defaults to all)
            engine: Constraint inference engine (required for adaptive feedback)
            max_attempts: Maximum attempts per property-function combination

        Returns:
            Nested dictionary: {function_name: {property_name: AdaptiveFeedbackResult}}
        """
        if not engine:
            raise ValueError("ConstraintInferenceEngine is required for adaptive analysis")

        results: Dict[str, Dict[str, AdaptiveFeedbackResult]] = {}

        properties_to_test = target_properties or self.config.properties_to_test or self.config.registry.get_all()

        print(f"🚀 Starting adaptive analysis for {len(properties_to_test)} properties")

        for prop in properties_to_test:
            if prop.num_functions != 1:
                print(f"⚠️ Skipping multi-function property: {prop.name}")
                continue

            for fut in self.config.functions_under_test:
                combined = CombinedFunctionUnderTest((fut,), self.config.comparison_strategy)

                if not prop.is_applicable(combined):
                    continue

                grammar = self.config.function_to_grammar.get(
                    fut.func.__name__, self.config.default_grammar
                )

                function_name = fut.func.__name__
                property_name = prop.name

                print(f"\n🔍 Testing {property_name} on {function_name}")

                try:
                    feedback_result = self.run_with_feedback(
                        prop, combined, grammar, engine, max_attempts
                    )

                    if function_name not in results:
                        results[function_name] = {}
                    results[function_name][property_name] = feedback_result

                except Exception as e:
                    print(f"❌ Error in adaptive analysis for {function_name}.{property_name}: {e}")

        return results

    def run(self) -> Dict[str, InferenceResult]:
        """Run standard property inference without adaptive feedback."""
        results: Dict[str, InferenceResult] = {}

        properties_to_test: List[PropertyTest] = (
                self.config.properties_to_test or self.config.registry.get_all())

        for prop in properties_to_test:
            n: int = prop.num_functions

            for funcs in product(self.config.functions_under_test, repeat=n):
                combined = CombinedFunctionUnderTest(funcs, self.config.comparison_strategy)

                if not prop.is_applicable(combined):
                    continue

                input_sets = self._get_inputs_for_combination(funcs)
                if not input_sets:
                    continue

                outcome = self._test_property(prop, combined, input_sets, self.config.max_counterexamples)

                key = f"combination ({combined.names()})"

                if key not in results:
                    results[key] = InferenceResult(outcomes={})

                results[key]["outcomes"][prop] = outcome

        return results