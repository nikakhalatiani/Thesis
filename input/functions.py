class Functions:
    @staticmethod
    def add(x, y):
        return x + y

    @staticmethod
    def multiply(x, y):
        return x * y

    @staticmethod
    def subtract(x, y):
        return x - y

    # @staticmethod
    # def divide(x, y):
    #     if y == 0:
    #         raise ZeroDivisionError("division by zero")
    #     return x / y

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