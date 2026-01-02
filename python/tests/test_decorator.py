"""
Tests for the decorator module.
"""

import shutil
from pathlib import Path
import pytest
from pydantic import BaseModel

from blackbox_python_sdk import blackbox, BlackboxFunction
from blackbox_python_sdk.storage import load_examples, get_all_signatures, DEFAULT_STORAGE_DIR


# Test models
class TestInput(BaseModel):
    query: str
    context: str


class TestOutput(BaseModel):
    response: str
    tone: str


class TestInputV2(BaseModel):
    query: str
    context: str
    max_length: int | None = None


class TestOutputV2(BaseModel):
    response: str
    tone: str
    confidence: float


@pytest.fixture(autouse=True)
def cleanup_blackbox():
    """Clean up .blackbox directory before and after each test."""
    blackbox_path = Path(DEFAULT_STORAGE_DIR)

    # Clean up before test
    if blackbox_path.exists():
        shutil.rmtree(blackbox_path)

    yield

    # Clean up after test
    if blackbox_path.exists():
        shutil.rmtree(blackbox_path)


def test_decorator_without_arguments():
    """Test @blackbox decorator without arguments."""

    @blackbox
    def test_function(input: TestInput) -> TestOutput:
        return TestOutput(response="test response", tone="neutral")

    # Should be wrapped
    assert isinstance(test_function, BlackboxFunction)
    assert test_function.function_name.endswith("test_function")


def test_sync_function_call():
    """Test calling a decorated sync function."""

    @blackbox
    def test_function(input: TestInput) -> TestOutput:
        return TestOutput(response=f"Response to: {input.query}", tone="neutral")

    # Call the function
    input_data = TestInput(query="test query", context="test context")
    output = test_function(input_data)

    # Verify output
    assert isinstance(output, TestOutput)
    assert output.response == "Response to: test query"
    assert output.tone == "neutral"


@pytest.mark.asyncio
async def test_async_function_call():
    """Test calling a decorated async function."""

    @blackbox
    async def test_function(input: TestInput) -> TestOutput:
        return TestOutput(response=f"Response to: {input.query}", tone="neutral")

    # Call the async function
    input_data = TestInput(query="test query", context="test context")
    output = await test_function(input_data)

    # Verify output
    assert isinstance(output, TestOutput)
    assert output.response == "Response to: test query"
    assert output.tone == "neutral"


def test_example_captured_sync():
    """Test that examples are captured for sync functions."""

    @blackbox
    def test_function(input: TestInput) -> TestOutput:
        return TestOutput(response="test response", tone="neutral")

    # Call the function
    input_data = TestInput(query="test query", context="test context")
    test_function(input_data)

    # Verify example was saved
    examples = load_examples(test_function.function_name)
    assert len(examples) == 1
    # Input is now structured as {parameter_name: value}
    assert examples[0].input["input"]["query"] == "test query"
    assert examples[0].output["response"] == "test response"


@pytest.mark.asyncio
async def test_example_captured_async():
    """Test that examples are captured for async functions."""

    @blackbox
    async def test_function(input: TestInput) -> TestOutput:
        return TestOutput(response="test response", tone="neutral")

    # Call the async function
    input_data = TestInput(query="test query", context="test context")
    await test_function(input_data)

    # Verify example was saved
    examples = load_examples(test_function.function_name)
    assert len(examples) == 1
    # Input is now structured as {parameter_name: value}
    assert examples[0].input["input"]["query"] == "test query"


def test_multiple_calls_create_multiple_examples():
    """Test that multiple calls create multiple examples."""

    @blackbox
    def test_function(input: TestInput) -> TestOutput:
        return TestOutput(response=f"Response {input.query}", tone="neutral")

    # Call multiple times
    for i in range(3):
        input_data = TestInput(query=f"query {i}", context="context")
        test_function(input_data)

    # Verify all examples were saved
    examples = load_examples(test_function.function_name)
    assert len(examples) == 3
    # Input is now structured as {parameter_name: value}
    assert examples[0].input["input"]["query"] == "query 0"
    assert examples[1].input["input"]["query"] == "query 1"
    assert examples[2].input["input"]["query"] == "query 2"


def test_example_ids_are_unique():
    """Test that each example gets a unique ID."""

    @blackbox
    def test_function(input: TestInput) -> TestOutput:
        return TestOutput(response="test response", tone="neutral")

    # Call multiple times
    for i in range(3):
        input_data = TestInput(query=f"query {i}", context="context")
        test_function(input_data)

    # Verify all IDs are unique
    examples = load_examples(test_function.function_name)
    ids = [ex.id for ex in examples]
    assert len(ids) == len(set(ids))  # All unique


def test_signature_change_creates_new_signature():
    """Test that changing function signature creates new signature."""

    # First function with original signature
    @blackbox
    def test_function_v1(input: TestInput) -> TestOutput:
        return TestOutput(response="test response", tone="neutral")

    # Second function with different signature
    @blackbox
    def test_function_v2(input: TestInputV2) -> TestOutputV2:
        return TestOutputV2(response="test response", tone="neutral", confidence=0.9)

    # Verify two different signatures were created
    signatures_v1 = get_all_signatures(test_function_v1.function_name)
    signatures_v2 = get_all_signatures(test_function_v2.function_name)

    assert len(signatures_v1) == 1
    assert len(signatures_v2) == 1
    assert signatures_v1[0].signature_hash != signatures_v2[0].signature_hash


def test_timestamps_are_set():
    """Test that examples have timestamps."""

    @blackbox
    def test_function(input: TestInput) -> TestOutput:
        return TestOutput(response="test response", tone="neutral")

    # Call the function
    input_data = TestInput(query="test query", context="test context")
    test_function(input_data)

    # Verify timestamp is set
    examples = load_examples(test_function.function_name)
    assert examples[0].timestamp is not None


def test_function_metadata_preserved():
    """Test that function metadata is preserved."""

    @blackbox
    def test_function(input: TestInput) -> TestOutput:
        """This is a test function."""
        return TestOutput(response="test response", tone="neutral")

    # Verify function metadata
    assert test_function.__name__ == "test_function"
    assert "test function" in test_function.__doc__.lower()


def test_examples_reference_correct_signature():
    """Test that examples reference the correct signature hash."""

    @blackbox
    def test_function(input: TestInput) -> TestOutput:
        return TestOutput(response="test response", tone="neutral")

    # Call the function
    input_data = TestInput(query="test query", context="test context")
    test_function(input_data)

    # Verify example has correct signature_hash
    examples = load_examples(test_function.function_name)
    assert examples[0].signature_hash == test_function.signature_hash


def test_directory_structure_created():
    """Test that correct directory structure is created."""

    @blackbox
    def test_function(input: TestInput) -> TestOutput:
        return TestOutput(response="test response", tone="neutral")

    # Call the function to create directories
    input_data = TestInput(query="test query", context="test context")
    test_function(input_data)

    # Verify directory structure
    func_dir = Path(DEFAULT_STORAGE_DIR) / test_function.function_name
    assert func_dir.exists()
    assert (func_dir / "examples").exists()
    assert (func_dir / "signatures").exists()
