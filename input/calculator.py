import math


# --- Comparators for result comparison -------------------------------------
# Use absolute comparison for integer-like operations,
# and math.isclose for floating-point operations.
def comparator_exact(x, y):
    return x == y


def comparator_abs(x, y):
    return abs(x) == abs(y)


def comparator_close(x, y):
    return math.isclose(x, y, rel_tol=1e-9, abs_tol=1e-9)


# Aliases for clarity
# comparator_add = comparator_close
# comparator_subtract = comparator_close
# comparator_multiply = comparator_close
# comparator_divide = comparator_close
# comparator_power = comparator_close
# comparator_sqrt = comparator_close

# --- Converters for argument preprocessing --------------------------------
# Convert input strings/nodes to the appropriate Python types.
def converter_int(x):
    return int(x)


def converter_float(x):
    return float(x)


def converter_str(x):
    return str(x)


# Use float conversion by default for all operations.
# converter_add = converter_float
# converter_subtract = converter_float
# converter_multiply = converter_float
# converter_divide = converter_float
# converter_power = converter_float
# converter_sqrt = converter_float

# --- Grammar constraints ---------------------------------------------------
# Prevent division by zero in generated expressions
grammar_divide = ["int(<term>) != 0"]
grammar_modulo = ["int(<term>) != 0"]

# Prevent negative inputs for square root
grammar_sqrt = ["int(<term>) >= 0"]

# Example: enforce non-negative integers for factorial grammar
grammar_factorial = ["int(<term>) >= 0", "int(<term>) <= 10"]  # limit to avoid huge
grammar_power = ["int(<term>) >= 0", "int(<term>) <= 4"]  # limit to avoid huge results


# --- Calculator with realistic operations -------------------------------
class Calculator:
    """
    A simple calculator with common arithmetic and utility functions.

    Available operations:
      - add, subtract, multiply, divide
      - power (x ** y), sqrt(x)
      - modulo, factorial, negate
      - min, max
    """

    @staticmethod
    def add(x, y):
        """Return x + y."""
        return x + y

    @staticmethod
    def subtract(x, y):
        """Return x - y."""
        return x - y

    # @staticmethod
    # def multiply(x, y):
    #     """Return x * y."""
    #     return x * y

    # @staticmethod
    # def divide(x, y):
    #     """Return x / y, raising ZeroDivisionError for y == 0."""
    #     if y == 0:
    #         raise ZeroDivisionError("Division by zero")
    #     return x / y

    # @staticmethod
    # def power(x, y):
    #     """Return x ** y."""
    #     try:
    #         return x ** y
    #     except OverflowError:
    #         # Cap extremely large results
    #         print("Warning: result overflowed")
    #         return math.inf
    #
    # @staticmethod
    # def sqrt(x):
    #     """Return the square root of x, raising ValueError if x < 0."""
    #     if x < 0:
    #         raise ValueError("Square root of negative number")
    #     return math.sqrt(x)
    #
    # @staticmethod
    # def modulo(x, y):
    #     """Return x % y, raising ZeroDivisionError for y == 0."""
    #     if y == 0:
    #         raise ZeroDivisionError("Modulo by zero")
    #     return x % y

    # @staticmethod
    # def factorial(n):
    #     """Return n! for integer n >= 0. Raises ValueError otherwise."""
    #     if not isinstance(n, int) or n < 0:
    #         raise ValueError("Factorial undefined for negative or non-integers")
    #     # Limit to 10! to avoid huge outputs
    #     if n > 10:
    #         raise ValueError("Input too large for safe factorial calculation")
    #     return math.factorial(n)
    #
    # @staticmethod
    # def negate(x):
    #     """Return the negation of x."""
    #     return -x

    # @staticmethod
    # def constant(x):
    #     # Constant function: both monotonically increasing and decreasing
    #     return 42
    #
    # @staticmethod
    # def zigzag(x):
    #     # Neither increasing nor decreasing (example: alternates)
    #     return (-1) ** x * x  # e.g., 0 → 0, 1 → -1, 2 → 2, 3 → -3, ...
    #
    # @staticmethod
    # def linear_increasing(x):
    #     # Strictly increasing
    #     return x + 1
    #
    # @staticmethod
    # def linear_decreasing(x):
    #     # Strictly decreasing
    #     return -x

    # @staticmethod
    # def minimum(x, y):
    #     """Return the smaller of x and y."""
    #     return x if x <= y else y
    #
    # @staticmethod
    # def maximum(x, y):
    #     """Return the larger of x and y."""
    #     return x if x >= y else y
