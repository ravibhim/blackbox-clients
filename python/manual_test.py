"""
Manual verification script for the @blackbox decorator.

This script tests the decorator with real functions and verifies that:
- Examples are saved to .blackbox/
- YAML files are created correctly
- show_examples() and show_signatures() methods work
"""

from pydantic import BaseModel
from blackbox_python_sdk import blackbox


# Define input/output models
class QueryInput(BaseModel):
    customer_query: str
    context: str


class QueryOutput(BaseModel):
    response: str
    tone: str


# Define a decorated function
@blackbox
def generate_response(input: QueryInput) -> QueryOutput:
    """Generate a customer support response."""
    return QueryOutput(
        response=f"Thank you for your query: {input.customer_query}",
        tone="helpful"
    )


def main():
    print("=" * 80)
    print("BLACKBOX DECORATOR - MANUAL VERIFICATION")
    print("=" * 80)

    # Test 1: Call the function multiple times
    print("\n[Test 1] Calling decorated function 3 times...")
    for i in range(3):
        input_data = QueryInput(
            customer_query=f"How do I solve problem {i}?",
            context="customer support"
        )
        output = generate_response(input_data)
        print(f"  Call {i+1}: {output.response}")

    print("\n✓ Function calls completed")

    # Test 2: Show examples
    print("\n" + "=" * 80)
    print("[Test 2] Displaying captured examples...")
    print("=" * 80)
    generate_response.show_examples()

    # Test 3: Show signatures
    print("\n" + "=" * 80)
    print("[Test 3] Displaying function signatures...")
    print("=" * 80)
    generate_response.show_signatures()

    # Test 4: Verify .blackbox directory structure
    print("\n" + "=" * 80)
    print("[Test 4] Verifying .blackbox directory structure...")
    print("=" * 80)

    import os
    from pathlib import Path

    base_dir = ".blackbox"
    func_dir = Path(base_dir) / "generate_response"

    if func_dir.exists():
        print(f"✓ Function directory exists: {func_dir}")

        examples_dir = func_dir / "examples"
        signatures_dir = func_dir / "signatures"

        if examples_dir.exists():
            example_files = list(examples_dir.glob("*.yaml"))
            print(f"✓ Examples directory exists with {len(example_files)} files")
            for f in example_files[:3]:
                print(f"  - {f.name}")

        if signatures_dir.exists():
            signature_files = list(signatures_dir.glob("*.yaml"))
            print(f"✓ Signatures directory exists with {len(signature_files)} files")
            for f in signature_files:
                print(f"  - {f.name}")
    else:
        print(f"✗ Function directory not found: {func_dir}")

    print("\n" + "=" * 80)
    print("MANUAL VERIFICATION COMPLETE")
    print("=" * 80)
    print("\nNext steps:")
    print("1. Inspect .blackbox/generate_response/ directory")
    print("2. Open example YAML files to verify format")
    print("3. Verify signature hash is consistent across files")


if __name__ == "__main__":
    main()
