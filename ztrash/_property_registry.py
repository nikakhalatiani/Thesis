# from core.function_under_test import CombinedFunctionUnderTest
# from core.properties.property_test import PropertyTest
#
#
# class PropertyRegistry:
#     """Registry for managing property tests, organized by categories."""
#
#     def __init__(self):
#         # Mapping from property name to a list of test variants with that name
#         # A single name may correspond to multiple PropertyTest objects variations
#         self._tests: dict[str, list[PropertyTest]] = {}
#         self._categories: dict[str, list[PropertyTest]] = {}
#
#     def register(self, test: PropertyTest) -> 'PropertyRegistry':
#         """Register a property test. Multiple variants can share the same name."""
#         if test.name not in self._tests:
#             self._tests[test.name] = []
#         # Check if this variation is already registered
#         for existing_test in self._tests[test.name]:
#             if existing_test == test:
#                 # This variation is already registered, skip adding it again
#                 return self
#         self._tests[test.name].append(test)
#
#         # Organize by category
#         category = test.category or "Uncategorized"
#         if category not in self._categories:
#             # Register a new category if it doesn't exist
#             self._categories[category] = []
#         self._categories[category].append(test)
#
#         return self
#
#     def get_by_name(self, name: str) -> list[PropertyTest]:
#         """Return all property tests registered under the given name.
#
#         A single property name may correspond to multiple variants,
#         so a list is always returned.
#         """
#         if name not in self._tests:
#             raise KeyError(f"Property test '{name}' not found")
#         return list(self._tests[name])
#
#     def get_by_category(self, category: str) -> list[PropertyTest]:
#         """Get all property tests in a category."""
#         return self._categories.get(category, [])
#
#     def get_applicable_tests(self, candidate: CombinedFunctionUnderTest) -> list[PropertyTest]:
#         """Get all tests applicable to the given function."""
#         applicable: list[PropertyTest] = []
#         for tests in self._tests.values():
#             for test in tests:
#                 if test.is_applicable(candidate):
#                     applicable.append(test)
#         return applicable
#
#     def list_categories(self) -> list[str]:
#         """List all available categories."""
#         return list(self._categories.keys())
#
#     def get_all(self) -> list[PropertyTest]:
#         """Return a flat list of all registered property tests."""
#         all_tests: list[PropertyTest] = []
#         for tests in self._tests.values():
#             all_tests.extend(tests)
#         return all_tests