# """
# Formatting utilities for test results and evaluation outcomes.
# """
#
# from core.library.property_test import PropertyTest, TestResult
#
#
# class TestResultFormatter:
#     """Formats test results for display and analysis."""
#
#     @staticmethod
#     def format_property_result(
#             prop: PropertyTest,
#             outcome: TestResult,
#             constraints_history: list[list[str]] = None
#     ) -> dict[str, any]:
#         """Format a single property test result.
#
#         Args:
#             prop: The property that was tested
#             outcome: The test result
#             constraints_history: History of constraint evolution during testing
#
#         Returns:
#             Formatted result dictionary
#         """
#         holds = outcome["holds"]
#         tests_run = outcome["stats"]["total_count"]
#         success_count = outcome["stats"]["success_count"]
#         confidence = (success_count / tests_run * 100) if tests_run > 0 else 0.0
#
#         return {
#             "property_name": str(prop),
#             "holds": holds,
#             "confidence": confidence,
#             "tests_run": tests_run,
#             "success_count": success_count,
#             "status_emoji": "🟢" if holds else "🔴",
#             "constraints_history": constraints_history or [],
#             "messages": outcome["successes"] if holds else outcome["counterexamples"]
#         }
#
#     @staticmethod
#     def format_constraints_evolution(constraints_history: list[list[str]]) -> list[str]:
#         """Format constraint evolution history for display.
#
#         Args:
#             constraints_history: List of constraint lists from each iteration
#
#         Returns:
#             List of formatted strings describing the evolution
#         """
#         if not constraints_history:
#             return ["🔄 No constraint evolution (property held on first attempt)"]
#
#         lines = [f"🔄 Constraint evolution ({len(constraints_history)} iterations):"]
#         for i, constraints in enumerate(constraints_history, 1):
#             if constraints:
#                 lines.append(f"\tIteration {i}: {', '.join(constraints)}")
#             else:
#                 lines.append(f"\tIteration {i}: No new constraints inferred")
#
#         return lines
#
#     @staticmethod
#     def group_results_by_category(
#             results: dict[PropertyTest, TestResult]
#     ) -> dict[str, list[tuple[PropertyTest, TestResult]]]:
#         """Group test results by property category.
#
#         Args:
#             results: Dictionary of property test results
#
#         Returns:
#             Dictionary mapping categories to lists of (property, result) tuples
#         """
#         by_category = {}
#
#         for prop, outcome in results.items():
#             category = getattr(prop, 'category', 'Properties') or 'Properties'
#             if category not in by_category:
#                 by_category[category] = []
#             by_category[category].append((prop, outcome))
#
#         return by_category
#
#     @staticmethod
#     def calculate_summary_statistics(
#             results: dict[PropertyTest, TestResult]
#     ) -> dict[str, any]:
#         """Calculate summary statistics for a set of test results.
#
#         Args:
#             results: Dictionary of property test results
#
#         Returns:
#             Dictionary containing summary statistics
#         """
#         if not results:
#             return {
#                 "total_properties": 0,
#                 "properties_holding": 0,
#                 "properties_failing": 0,
#                 "success_rate": 0.0,
#                 "total_tests_run": 0,
#                 "average_confidence": 0.0
#             }
#
#         total_properties = len(results)
#         properties_holding = sum(1 for result in results.values() if result["holds"])
#         properties_failing = total_properties - properties_holding
#         success_rate = (properties_holding / total_properties * 100) if total_properties > 0 else 0.0
#
#         total_tests_run = sum(result["stats"]["total_count"] for result in results.values())
#         total_successes = sum(result["stats"]["success_count"] for result in results.values())
#         average_confidence = (total_successes / total_tests_run * 100) if total_tests_run > 0 else 0.0
#
#         return {
#             "total_properties": total_properties,
#             "properties_holding": properties_holding,
#             "properties_failing": properties_failing,
#             "success_rate": success_rate,
#             "total_tests_run": total_tests_run,
#             "average_confidence": average_confidence
#         }