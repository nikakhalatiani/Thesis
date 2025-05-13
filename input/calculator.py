from input.function_metadata import grammar

import sys
import math
# --- Optional helpers and aliases ------------------------------------------

def comparator_abs(x, y):
    return abs(x) == abs(y)

def comparator_close(x, y):
    return math.isclose(x, y)

comparator_subtract = comparator_abs
comparator_divide = comparator_close
comparator_multiply = comparator_close


def converter_int(x):
    return int(x)

def converter_float(x):
    return float(x)


# converter_add = converter_int
# converter_multiply = converter_int
# converter_subtract = converter_int
# converter_divide = converter_int

# converter_add = converter_float
# converter_multiply = converter_float
# converter_subtract = converter_float
# converter_divide = converter_float


# --- Functions under test ---------------------------------------------

class Calculator:
    @staticmethod
    def subtract(x, y):
        return x - y

    @staticmethod
    def multiply(x, y):
        return x * y

    @staticmethod
    def add(x, y):
        return x + y

    @staticmethod
    @grammar("./grammars/test.fan")
    def divide(x, y):
        if y == 0:
            return sys.maxsize
        return x / y


    # @staticmethod
    # def first(x, y):
    #     """Returns the first argument. Idempotent for right idempotency: f(a, b) = f(f(a, b), a)."""
    #     return x
    #
    # @staticmethod
    # def second(x, y):
    #     """Returns the second argument. Idempotent for left idempotency: f(a, b) = f(b, f(a, b))."""
    #     return y
    #
    # @staticmethod
    # def max(x, y):
    #     """Returns the maximum of two arguments. Idempotent for all three: right, left, and full idempotency."""
    #     return x if x >= y else y

    # # TODO modify framework to run on not just two args
    # @staticmethod
    # def project(x):
    #     return x