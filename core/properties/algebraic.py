from core.function_under_test import FunctionUnderTest
from core.properties.property_test import PropertyTest, TestResult


class CommutativityTest(PropertyTest):
    """Test if f(a,b) = f(b,a)"""

    def __init__(self):
        super().__init__(
            name="Commutativity",
            input_arity=2,
            function_arity=2,
            description="Tests if f(a,b) equals f(b,a)",
            category="Algebraic"
        )

    def test(self, function: FunctionUnderTest, inputs: tuple) -> TestResult:
        a, b = inputs[:2]
        r1 = function.call(a, b)
        r2 = function.call(b, a)
        if function.compare_results(r1, r2):
            return True, f"{function.func.__name__}(a,b) == {function.func.__name__}(b,a)"
        else:
            return False, {
                f"{function.func.__name__}({a},{b})": r1,
                f"{function.func.__name__}({b},{a})": f"{r2}\n"
            }

class AssociativityTest(PropertyTest):
    """Test if f(a, f(b, c)) = f(f(a, b), c)"""

    def __init__(self):
        super().__init__(
            name="Associativity",
            input_arity=3,
            function_arity=2,
            description="Tests if f(a, f(b, c)) equals f(f(a, b), c)",
            category="Algebraic"
        )

    def test(self, function: FunctionUnderTest, inputs: tuple) -> TestResult:
        a, b, c = inputs[:3]
        r1 = function.call(a, function.call(b, c))
        r2 = function.call(function.call(a, b), c)

        if function.compare_results(r1, r2):
            return True, (f"{function.func.__name__}(a,{function.func.__name__}(b,c)) "
                          f"== {function.func.__name__}({function.func.__name__}(a,b),c)")
        else:
            return False, {
                f"{function.func.__name__}({a},{function.func.__name__}({b},{c}))": r1,
                f"{function.func.__name__}({function.func.__name__}({a},{b}),{c})": f"{r2}\n"
            }

class IdempotenceTest(PropertyTest):
    """Test if f(f(x)) = f(x)"""

    def __init__(self):
        super().__init__(
            name="Idempotence",
            input_arity=1,
            function_arity=1,
            description="Tests if f(f(x)) equals f(x)",
            category="Algebraic"
        )

    def test(self, function: FunctionUnderTest, inputs: tuple) -> TestResult:
        a = inputs[0]
        r1 = function.call(a)
        r2 = function.call(r1)
        if function.compare_results(r1, r2):
            return True, f"{function.func.__name__}({function.func.__name__}(a)) == {function.func.__name__}(a)"
        else:
            return False, {
                f"{function.func.__name__}({a})": r1,
                f"{function.func.__name__}({function.func.__name__}({a}))": f"{r2}\n",
            }


class LeftIdempotenceTest(PropertyTest):
    """Test if f(a, f(a,b)) = f(a,b) - the left argument dominates when repeated"""

    def __init__(self):
        super().__init__(
            name="Left Idempotence",
            input_arity=2,
            function_arity=2,
            description="Tests if f(a, f(a,b)) equals f(a,b) - left argument idempotence",
            category="Algebraic"
        )

    def test(self, function: FunctionUnderTest, inputs: tuple) -> TestResult:
        a, b = inputs[:2]
        r1 = function.call(a, b)
        r2 = function.call(a, r1)

        if function.compare_results(r1, r2):
            return True, f"{function.func.__name__}(a,b) == {function.func.__name__}(a,{function.func.__name__}(a,b))"
        else:
            return False, {
                f"{function.func.__name__}({a},{b})": r1,
                f"{function.func.__name__}({a},{function.func.__name__}({a},{b}))": f"{r2}\n",
            }


class RightIdempotenceTest(PropertyTest):
    """Test if f(f(a,b), b) = f(a,b) - the right argument dominates when repeated"""

    def __init__(self):
        super().__init__(
            name="Right Idempotence",
            input_arity=2,
            function_arity=2,
            description="Tests if f(f(a,b), b) equals f(a,b) - right argument idempotence",
            category="Algebraic"
        )

    def test(self, function: FunctionUnderTest, inputs: tuple) -> TestResult:
        a, b = inputs[:2]
        r1 = function.call(a, b)
        r2 = function.call(r1, b)

        if function.compare_results(r1, r2):
            return True, f"{function.func.__name__}(a,b) == {function.func.__name__}({function.func.__name__}(a,b),b)"
        else:
            return False, {
                f"{function.func.__name__}({a},{b})": r1,
                f"{function.func.__name__}({function.func.__name__}({a},{b}),{b})": f"{r2}\n",
            }


class FullIdempotenceTest(PropertyTest):
    """Test if f(f(a,b), f(a,b)) = f(a,b) - complete idempotence"""

    def __init__(self):
        super().__init__(
            name="Full Idempotence",
            input_arity=2,
            function_arity=2,
            description="Tests if f(f(a,b), f(a,b)) equals f(a,b) - complete idempotence",
            category="Algebraic"
        )

    def test(self, function: FunctionUnderTest, inputs: tuple) -> TestResult:
        a, b = inputs[:2]
        r1 = function.call(a, b)
        r2 = function.call(r1, r1)

        if function.compare_results(r1, r2):
            return True, f"{function.func.__name__}(a,b) == {function.func.__name__}({function.func.__name__}(a,b),{function.func.__name__}(a,b))"
        else:
            return False, {
                f"{function.func.__name__}({a},{b})": r1,
                f"{function.func.__name__}({function.func.__name__}({a},{b}),{function.func.__name__}({a},{b}))": f"{r2}\n",
            }
