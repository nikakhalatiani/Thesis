from fandango import FandangoParseError

class InputParser:
    def __init__(self, extraction_strategy):
        """
        extraction_strategy: A function that takes a parse tree and returns inputs
        """
        self.extraction_strategy = extraction_strategy

    def parse(self, fan, fuzzed_string):
        try:
            for tree in fan.parse(fuzzed_string):
                return self.extraction_strategy(tree)
        except FandangoParseError as e:
            print(f"❌ Parsing failed at position {e.position} in '{fuzzed_string}'")
        return None