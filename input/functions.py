from input.function_metadata import grammar

# --- Optional helpers and aliases ------------------------------------------

def comparator_abs(x, y):
    # “equal up to absolute‐value”
    return abs(x) == abs(y)

# alias the generic test to just the one function that needs it:
comparator_subtract = comparator_abs


def converter_int(x):
    # parse every argument as int
    return int(x)

converter_add = converter_int
converter_multiply = converter_int
converter_subtract = converter_int
converter_divide = converter_int


# --- functions under test ---------------------------------------------

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
            raise ZeroDivisionError("Denominator cannot be zero")
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
    #
    # @staticmethod
    # def project(x):
    #     return x