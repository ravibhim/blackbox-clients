"""
Tests for the storage module.
"""

import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import pytest

from blackbox_python_sdk.models import Example, Signature
from blackbox_python_sdk import storage


@pytest.fixture
def temp_storage_dir():
    """Create a temporary directory for storage tests."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


def test_ensure_function_dir_creates_structure(temp_storage_dir):
    """Test that ensure_function_dir creates the correct directory structure."""
    func_dir = storage.ensure_function_dir("test_function", temp_storage_dir)

    assert func_dir.exists()
    assert (func_dir / "examples").exists()
    assert (func_dir / "signatures").exists()


def test_save_and_load_example(temp_storage_dir):
    """Test saving and loading an example."""
    example = Example(
        id="ex001",
        signature_hash="abc123def456",
        timestamp=datetime(2025, 12, 4, 10, 30, 0),
        input={"query": "test query"},
        output={"response": "test response"},
    )

    # Save example
    saved_path = storage.save_example("test_function", example, temp_storage_dir)

    # Verify file was created
    assert saved_path.exists()
    assert saved_path.name == "ex001_abc123def456.yaml"

    # Load examples
    loaded_examples = storage.load_examples("test_function", base_dir=temp_storage_dir)

    assert len(loaded_examples) == 1
    loaded = loaded_examples[0]
    assert loaded.id == example.id
    assert loaded.signature_hash == example.signature_hash
    assert loaded.timestamp == example.timestamp
    assert loaded.input == example.input
    assert loaded.output == example.output


def test_load_examples_by_signature_hash(temp_storage_dir):
    """Test loading examples filtered by signature hash."""
    # Create examples for different signatures
    ex1 = Example(
        id="ex001",
        signature_hash="hash1",
        timestamp=datetime.now(),
        input={},
        output={},
    )
    ex2 = Example(
        id="ex002",
        signature_hash="hash2",
        timestamp=datetime.now(),
        input={},
        output={},
    )
    ex3 = Example(
        id="ex003",
        signature_hash="hash1",
        timestamp=datetime.now(),
        input={},
        output={},
    )

    storage.save_example("test_function", ex1, temp_storage_dir)
    storage.save_example("test_function", ex2, temp_storage_dir)
    storage.save_example("test_function", ex3, temp_storage_dir)

    # Load hash1 examples only
    hash1_examples = storage.load_examples(
        "test_function", signature_hash="hash1", base_dir=temp_storage_dir
    )
    assert len(hash1_examples) == 2
    assert all(ex.signature_hash == "hash1" for ex in hash1_examples)

    # Load hash2 examples only
    hash2_examples = storage.load_examples(
        "test_function", signature_hash="hash2", base_dir=temp_storage_dir
    )
    assert len(hash2_examples) == 1
    assert hash2_examples[0].signature_hash == "hash2"

    # Load all examples
    all_examples = storage.load_examples("test_function", base_dir=temp_storage_dir)
    assert len(all_examples) == 3


def test_load_examples_empty(temp_storage_dir):
    """Test loading examples when none exist."""
    examples = storage.load_examples("nonexistent_function", base_dir=temp_storage_dir)
    assert examples == []


def test_save_and_load_signature(temp_storage_dir):
    """Test saving and loading a signature."""
    signature = Signature(
        signature_hash="abc123",
        input_schema={"type": "object", "properties": {"query": {"type": "string"}}},
        output_schema={
            "type": "object",
            "properties": {"response": {"type": "string"}},
        },
        created_at=datetime(2025, 12, 4, 9, 0, 0),
    )

    # Save signature
    saved_path = storage.save_signature("test_function", signature, temp_storage_dir)

    # Verify file was created
    assert saved_path.exists()
    assert saved_path.name == "abc123.yaml"

    # Load signature
    loaded_signature = storage.load_signature(
        "test_function", "abc123", base_dir=temp_storage_dir
    )

    assert loaded_signature is not None
    assert loaded_signature.signature_hash == signature.signature_hash
    assert loaded_signature.input_schema == signature.input_schema
    assert loaded_signature.output_schema == signature.output_schema
    assert loaded_signature.created_at == signature.created_at


def test_load_signature_nonexistent(temp_storage_dir):
    """Test loading a signature that doesn't exist."""
    signature = storage.load_signature(
        "test_function", "nonexistent_hash", base_dir=temp_storage_dir
    )
    assert signature is None


def test_get_example_count(temp_storage_dir):
    """Test getting the count of examples for a signature."""
    # Create some examples
    for i in range(3):
        ex = Example(
            id=f"ex{i:03d}",
            signature_hash="hash1",
            timestamp=datetime.now(),
            input={},
            output={},
        )
        storage.save_example("test_function", ex, temp_storage_dir)

    for i in range(2):
        ex = Example(
            id=f"ex{i+3:03d}",
            signature_hash="hash2",
            timestamp=datetime.now(),
            input={},
            output={},
        )
        storage.save_example("test_function", ex, temp_storage_dir)

    # Check counts
    hash1_count = storage.get_example_count("test_function", "hash1", temp_storage_dir)
    assert hash1_count == 3

    hash2_count = storage.get_example_count("test_function", "hash2", temp_storage_dir)
    assert hash2_count == 2


def test_get_example_count_empty(temp_storage_dir):
    """Test getting example count when no examples exist."""
    count = storage.get_example_count("nonexistent", "hash1", temp_storage_dir)
    assert count == 0


def test_get_all_signatures(temp_storage_dir):
    """Test getting all signatures for a function."""
    # Create signatures with different timestamps
    sig1 = Signature(
        signature_hash="hash1",
        input_schema={},
        output_schema={},
        created_at=datetime(2025, 12, 4, 9, 0, 0),
    )
    sig2 = Signature(
        signature_hash="hash2",
        input_schema={},
        output_schema={},
        created_at=datetime(2025, 12, 4, 10, 0, 0),
    )
    sig3 = Signature(
        signature_hash="hash3",
        input_schema={},
        output_schema={},
        created_at=datetime(2025, 12, 4, 11, 0, 0),
    )

    storage.save_signature("test_function", sig1, temp_storage_dir)
    storage.save_signature("test_function", sig2, temp_storage_dir)
    storage.save_signature("test_function", sig3, temp_storage_dir)

    # Get all signatures
    signatures = storage.get_all_signatures("test_function", temp_storage_dir)

    assert len(signatures) == 3
    # Should be sorted by created_at (newest first)
    assert signatures[0].signature_hash == "hash3"
    assert signatures[1].signature_hash == "hash2"
    assert signatures[2].signature_hash == "hash1"


def test_get_all_signatures_empty(temp_storage_dir):
    """Test getting all signatures when none exist."""
    signatures = storage.get_all_signatures("nonexistent", temp_storage_dir)
    assert signatures == []


def test_get_latest_signature(temp_storage_dir):
    """Test getting the latest signature."""
    # Create signatures with different timestamps
    sig1 = Signature(
        signature_hash="hash1",
        input_schema={},
        output_schema={},
        created_at=datetime(2025, 12, 4, 9, 0, 0),
    )
    sig2 = Signature(
        signature_hash="hash2",
        input_schema={},
        output_schema={},
        created_at=datetime(2025, 12, 4, 10, 0, 0),
    )
    sig3 = Signature(
        signature_hash="hash3",
        input_schema={},
        output_schema={},
        created_at=datetime(2025, 12, 4, 11, 0, 0),
    )

    storage.save_signature("test_function", sig1, temp_storage_dir)
    storage.save_signature("test_function", sig2, temp_storage_dir)
    storage.save_signature("test_function", sig3, temp_storage_dir)

    # Get latest signature
    latest = storage.get_latest_signature("test_function", temp_storage_dir)

    assert latest is not None
    assert latest.signature_hash == "hash3"  # Most recent


def test_get_latest_signature_empty(temp_storage_dir):
    """Test getting latest signature when none exist."""
    latest = storage.get_latest_signature("nonexistent", temp_storage_dir)
    assert latest is None


def test_yaml_file_format(temp_storage_dir):
    """Test that YAML files are human-readable with proper formatting."""
    example = Example(
        id="ex001",
        signature_hash="abc123",
        timestamp=datetime(2025, 12, 4, 10, 30, 0),
        input={"customer_query": "I can't log in", "context": "Premium user"},
        output={
            "response": "I understand you're having trouble logging in.\nLet me help you resolve this.",
            "tone": "empathetic",
        },
    )

    saved_path = storage.save_example("test_function", example, temp_storage_dir)

    # Read the raw YAML file
    with open(saved_path, "r") as f:
        content = f.read()

    # Verify YAML structure
    assert "id: ex001" in content
    assert "signature_hash: abc123" in content
    assert "input:" in content
    assert "customer_query:" in content
    assert "output:" in content
    assert "response:" in content
    assert "tone: empathetic" in content


def test_multiple_functions_isolated(temp_storage_dir):
    """Test that different functions have isolated storage."""
    ex1 = Example(
        id="ex001", signature_hash="hash1", timestamp=datetime.now(), input={}, output={}
    )
    ex2 = Example(
        id="ex002", signature_hash="hash1", timestamp=datetime.now(), input={}, output={}
    )

    storage.save_example("function1", ex1, temp_storage_dir)
    storage.save_example("function2", ex2, temp_storage_dir)

    # Load examples for each function
    func1_examples = storage.load_examples("function1", base_dir=temp_storage_dir)
    func2_examples = storage.load_examples("function2", base_dir=temp_storage_dir)

    assert len(func1_examples) == 1
    assert len(func2_examples) == 1
    assert func1_examples[0].id == "ex001"
    assert func2_examples[0].id == "ex002"
