from fandango import Fandango

def test_last_name_startswith_S():
    # Load the grammar
    with open("./grammars/persons-faker.fan", "r") as f:
        fan = Fandango(f)

    constraint = "<last_name>.startswith('S')"
    print(f"🔍 Testing extra constraint: {constraint}")

    # Generate examples
    examples = fan.fuzz(
        desired_solutions=200,
        extra_constraints=[constraint]
    )

    print("\n📦 Generated Examples:")
    for i, example in enumerate(examples, 1):
        example_str = str(example)
        print(f"{i:3}: {example_str}")

        try:
            person_part, age_part = example_str.split(",")
            first_name, last_name = person_part.split(" ")

            if not last_name.startswith('S'):
                print(f"❌ Constraint violated! Last name '{last_name}' does not start with 'S' in: {example_str}")
                return
        except ValueError:
            print(f"⚠️ Could not parse example correctly: {example_str}")
            return

    print("\n✅ No violations found. Extra constraint seems to work!")

if __name__ == "__main__":
    test_last_name_startswith_S()
