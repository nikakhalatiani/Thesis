from fandango import Fandango

def all_terms_nonzero(example: str) -> bool:
    try:
        terms = example.split(",")
        return all(int(term) != 0 for term in terms)
    except ValueError:
        return False

def test_constraints(max_attempts=100):
    with open("./grammars/test.fan", "r") as f:
        fan = Fandango(f)

    for attempt in range(1, max_attempts + 1):
        print(f"\nAttempt {attempt} of {max_attempts}...\n")

        examples = fan.fuzz(
            desired_solutions=200,
            population_size=220
        )

        for i, example in enumerate(examples, 1):
            example_str = example.to_string()
            print(f"{i:3}: {example_str}")
            if not all_terms_nonzero(example_str):
                print(f"\nDetected 0 inside example: {example_str}")
                print(f"\nConstraint violation detected on attempt {attempt}!")
                return

        print(f"\nNo violations found in attempt {attempt}, trying again...")

    print(f"\nReached {max_attempts} attempts with no violations.")

if __name__ == "__main__":
    test_constraints()