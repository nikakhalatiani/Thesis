class FunctionUnderTest:
    def __init__(self, func, arg_converter=None, result_comparator=None):
        self.func = func
        self.arg_converter = arg_converter or (lambda x: x)  # Default: no conversion
        self.result_comparator = result_comparator or (lambda x, y: x == y)  # Default: equality

    def call(self, *args):
        """
          Calls the function under test with the provided arguments after applying the argument converter.

          Args:
              *args: The arguments to pass to the function under test.

          Returns:
              The result of calling the function under test with the converted arguments.

          Notes:
              - The `arg_converter` is applied to each argument before passing them to the function.
              - If no `arg_converter` is provided during initialization, the arguments are passed as-is.
        """
        converted_args = [self.arg_converter(arg) for arg in args]
        return self.func(*converted_args)

    def compare_results(self, result1, result2):
        return self.result_comparator(result1, result2)