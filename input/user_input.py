import math


# --- Converters and Parser Configurations -----------------------------------

def converter_intset(value):
    """Convert a string like "{1,2}" or iterable to a Python set of ints."""
    if isinstance(value, set):
        return value
    if isinstance(value, (list, tuple, frozenset)):
        elements = value
    elif isinstance(value, str):
        text = value.strip()
        if text.startswith('{') and text.endswith('}'):
            inner = text[1:-1].strip()
            elements = [] if not inner else [e.strip() for e in inner.split(',')]
        elif not text:
            elements = []
        else:
            elements = [text]
    else:
        elements = [value]

    result = set()
    for elem in elements:
        try:
            elem = int(elem)
        except (ValueError, TypeError):
            pass
        result.add(elem)
    return result


# Converter list for operations
converter_add_to_set = [converter_intset, int]
converter_remove_from_set = [converter_intset, int]
converter_union_sets = [converter_intset, converter_intset]

# Grammar and parser overrides
grammar_add_to_set = "grammars/set_and_element.fan"
parser_add_to_set = ["<set>", "<number_to_add>"]

grammar_remove_from_set = ["grammars/set_and_element.fan"]
parser_remove_from_set = ["<set>", "<number_to_add>"]

grammar_union_sets = "grammars/int_sets.fan"
parser_union_sets = "<set>"


# --- Comparators -----------------------------------------------------------
def comparator_exact(x, y):
    return x == y


def comparator_abs(x, y):
    return abs(x) == abs(y)


def comparator_close(x, y):
    return math.isclose(x, y, rel_tol=1e-9, abs_tol=1e-9)

comparator_multiply = comparator_close
comparator_divide = comparator_close


# --- Argument Converters --------------------------------------------------
def converter_int(x):
    return int(x)


def converter_float(x):
    return float(x)


def converter_str(x):
    return str(x)


# --- Grammar Constraints --------------------------------------------------
# Prevent division or modulo by zero
grammar_divide = ["int(<term>) != 0"]
grammar_modulo = ["int(<term>) != 0"]

# Prevent negative inputs
grammar_sqrt = ["int(<term>) >= 0"]


# --- Use Case Classes -----------------------------------------------------
class SetOperations:
    """Simple set-based operations for testing."""
    #
    # @staticmethod
    # def add_to_set(s, x):
    #     """Return a new set with x added to s."""
    #     if not isinstance(s, set):
    #         s = {s}
    #     result = set(s)
    #     result.add(x)
    #     return result
#
#     @staticmethod
#     def remove_from_set(s, x):
#         """Return a new set with x removed from s."""
#         if not isinstance(s, set):
#             s = {s}
#         result = set(s)
#         result.discard(x)
#         return result
#
#     @staticmethod
#     def union_sets(a, b):
#         """Return the union of a and b."""
#         if not isinstance(a, set):
#             a = {a}
#         if not isinstance(b, set):
#             b = {b}
#         return a | b
#
#
# class Calculator:
#     """
#     A simple calculator with common arithmetic and utility functions.
#
#     Available operations:
#       - add, subtract, multiply, divide
#       - power (x ** y), sqrt(x)
#       - modulo, negate
#       - minimum, maximum
#     """
#
    # @staticmethod
    # def add(x, y):
    #     """Return x + y."""
    #     return x + y
    #
    @staticmethod
    def subtract(x, y):
        """Return x - y."""
        return x - y

#     @staticmethod
#     def multiply(x, y):
#         """Return x * y."""
#         return x * y
#
    # @staticmethod
    # def divide(x, y):
    #     """Return x / y, raising ZeroDivisionError for y == 0."""
    #     if y == 0:
    #         raise ZeroDivisionError("Division by zero")
    #     return x / y

#     @staticmethod
#     def sqrt(x):
#         """Return the square root of x, raising ValueError if x < 0."""
#         if x < 0:
#             raise ValueError("Square root of negative number")
#         return math.sqrt(x)
#
#     @staticmethod
#     def modulo(x, y):
#         """Return x % y, raising ZeroDivisionError for y == 0."""
#         if y == 0:
#             raise ZeroDivisionError("Modulo by zero")
#         return x % y
#
#     @staticmethod
#     def negate(x):
#         """Return the negation of x."""
#         return -x
#
#     @staticmethod
#     def minimum(x, y):
#         """Return the smaller of x and y."""
#         return x if x <= y else y
#
#     @staticmethod
#     def maximum(x, y):
#         """Return the larger of x and y."""
#         return x if x >= y else y
#
#
# class DataChecksum:
#     """Checksum utilities for validating data integrity."""
#
#     @staticmethod
#     def simple_checksum_working(data):
#         """Working injective checksum using hash of the string representation"""
#         if isinstance(data, int):
#             data = str(data)
#         # Python's hash is designed to be collision-resistant
#         # For testing purposes, this should be injective on small domains
#         return hash(data)
#
#     @staticmethod
#     def simple_checksum_broken(data):
#         """Broken non-injective checksum - different inputs can produce same output"""
#         if isinstance(data, int):
#             data = str(data)
#         # Force collisions by reducing range
#         return hash(data) % 1000

#
# class CompositionTestFunctions:
#     """Functions designed to test composition properties."""
#
#     @staticmethod
#     def conditional_identity(x):
#         """
#         Acts as identity for even numbers, but transforms odd numbers.
#         This will pass left composition with even_doubler but fail right composition.
#         """
#         if x % 2 == 0:  # Even numbers pass through unchanged
#             return x
#         else:  # Odd numbers get transformed
#             return x + 1
#
#     @staticmethod
#     def even_doubler(x):
#         """
#         Doubles the input, always producing an even number.
#         """
#         return x * 2
