"""
Tests for the signature module.
"""

import tempfile
import shutil
from datetime import datetime
import pytest
from pydantic import BaseModel

from blackbox_python_sdk.signature import (
    SignatureManager,
    SignatureError,
)


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
    max_length: int | None = None  # Added optional field


class TestOutputV2(BaseModel):
    response: str
    tone: str
    confidence: float  # Added field


@pytest.fixture
def temp_storage_dir():
    """Create a temporary directory for storage tests."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


def test_extract_signature_sync_function():
    """Test signature extraction from a sync function with Pydantic parameter."""

    def test_function(input: TestInput) -> TestOutput:
        return TestOutput(response="test", tone="neutral")

    manager = SignatureManager()
    input_schema, output_schema = manager.extract_signature(test_function)

    # Verify schemas are dicts
    assert isinstance(input_schema, dict)
    assert isinstance(output_schema, dict)

    # Verify input schema has "input" parameter
    assert "properties" in input_schema
    assert "input" in input_schema["properties"]
    # Verify the Pydantic model was properly converted
    assert "properties" in input_schema["properties"]["input"]
    assert "query" in input_schema["properties"]["input"]["properties"]
    assert "context" in input_schema["properties"]["input"]["properties"]

    # Verify output schema structure (Pydantic model)
    assert "properties" in output_schema
    assert "response" in output_schema["properties"]
    assert "tone" in output_schema["properties"]


def test_extract_signature_async_function():
    """Test signature extraction from an async function."""

    async def test_function(input: TestInput) -> TestOutput:
        return TestOutput(response="test", tone="neutral")

    manager = SignatureManager()
    input_schema, output_schema = manager.extract_signature(test_function)

    # Should work the same as sync functions
    assert isinstance(input_schema, dict)
    assert isinstance(output_schema, dict)
    assert "properties" in input_schema
    assert "properties" in output_schema


def test_extract_signature_multiple_params():
    """Test signature extraction from function with multiple parameters."""

    def test_function(query: str, context: str, max_tokens: int = 100) -> dict:
        return {"response": "test"}

    manager = SignatureManager()
    input_schema, output_schema = manager.extract_signature(test_function)

    # Verify input has all three parameters
    assert "properties" in input_schema
    assert "query" in input_schema["properties"]
    assert "context" in input_schema["properties"]
    assert "max_tokens" in input_schema["properties"]

    # Verify query and context are required, max_tokens is optional
    assert "required" in input_schema
    assert "query" in input_schema["required"]
    assert "context" in input_schema["required"]
    assert "max_tokens" not in input_schema["required"]

    # Verify types
    assert input_schema["properties"]["query"]["type"] == "string"
    assert input_schema["properties"]["context"]["type"] == "string"
    assert input_schema["properties"]["max_tokens"]["type"] == "integer"

    # Verify output is dict (wrapped in object)
    assert output_schema["type"] == "object"


def test_extract_signature_non_pydantic_types():
    """Test that non-Pydantic types (primitives, dicts, lists) work."""

    def test_function(data: dict, items: list[str]) -> str:
        return "test"

    manager = SignatureManager()
    input_schema, output_schema = manager.extract_signature(test_function)

    # Verify dict and list parameters
    assert input_schema["properties"]["data"]["type"] == "object"
    assert input_schema["properties"]["items"]["type"] == "array"
    assert input_schema["properties"]["items"]["items"]["type"] == "string"

    # Verify string output (wrapped in object)
    assert "properties" in output_schema
    assert "result" in output_schema["properties"]
    assert output_schema["properties"]["result"]["type"] == "string"


def test_compute_signature_hash_stable():
    """Test that hash computation is stable (same input → same hash)."""

    def test_function(input: TestInput) -> TestOutput:
        return TestOutput(response="test", tone="neutral")

    manager = SignatureManager()
    input_schema, output_schema = manager.extract_signature(test_function)

    # Compute hash multiple times
    hash1 = manager.compute_hash(input_schema, output_schema)
    hash2 = manager.compute_hash(input_schema, output_schema)
    hash3 = manager.compute_hash(input_schema, output_schema)

    assert hash1 == hash2 == hash3
    assert isinstance(hash1, str)
    assert len(hash1) == 64  # Full SHA-256 hash (64 hex characters)


def test_compute_signature_hash_changes_with_schema():
    """Test that hash changes when schema changes."""

    def test_function_v1(input: TestInput) -> TestOutput:
        return TestOutput(response="test", tone="neutral")

    def test_function_v2(input: TestInputV2) -> TestOutputV2:
        return TestOutputV2(response="test", tone="neutral", confidence=0.9)

    manager = SignatureManager()
    input_schema_v1, output_schema_v1 = manager.extract_signature(test_function_v1)
    input_schema_v2, output_schema_v2 = manager.extract_signature(test_function_v2)

    hash_v1 = manager.compute_hash(input_schema_v1, output_schema_v1)
    hash_v2 = manager.compute_hash(input_schema_v2, output_schema_v2)

    assert hash_v1 != hash_v2


def test_detect_signature_change_first_time(temp_storage_dir):
    """Test detecting signature change for first time (new signature)."""
    manager = SignatureManager(base_dir=temp_storage_dir)

    # Check a hash that doesn't exist yet
    is_new = manager.detect_signature_change("test_function", "newhash123")

    assert is_new is True


def test_detect_signature_change_existing(temp_storage_dir):
    """Test that existing signature is detected."""
    from blackbox.models import Signature
    from blackbox.storage import save_signature

    def test_function(input: TestInput) -> TestOutput:
        return TestOutput(response="test", tone="neutral")

    manager = SignatureManager(base_dir=temp_storage_dir)
    input_schema, output_schema = manager.extract_signature(test_function)
    sig_hash = manager.compute_hash(input_schema, output_schema)

    # Create and save signature
    signature = Signature(
        signature_hash=sig_hash,
        input_schema=input_schema,
        output_schema=output_schema,
        created_at=datetime.now()
    )
    save_signature("test_function", signature, temp_storage_dir)

    # Check if it's detected as existing
    is_new = manager.detect_signature_change("test_function", sig_hash)

    assert is_new is False


def test_get_or_create_signature_first_time(temp_storage_dir):
    """Test getting or creating signature for the first time."""

    def test_function(input: TestInput) -> TestOutput:
        return TestOutput(response="test", tone="neutral")

    manager = SignatureManager(base_dir=temp_storage_dir)
    signature, is_new = manager.get_or_create(
        test_function, "test_function"
    )

    assert is_new is True
    assert signature.input_schema is not None
    assert signature.output_schema is not None
    assert signature.signature_hash is not None


def test_get_or_create_signature_existing(temp_storage_dir):
    """Test getting signature when it already exists."""

    def test_function(input: TestInput) -> TestOutput:
        return TestOutput(response="test", tone="neutral")

    manager = SignatureManager(base_dir=temp_storage_dir)

    # Create first time
    sig1, is_new1 = manager.get_or_create(
        test_function, "test_function"
    )

    # Get second time (same signature)
    sig2, is_new2 = manager.get_or_create(
        test_function, "test_function"
    )

    assert is_new1 is True
    assert is_new2 is False
    assert sig1.signature_hash == sig2.signature_hash


def test_get_or_create_signature_change(temp_storage_dir):
    """Test creating new signature when function signature changes."""

    def test_function_v1(input: TestInput) -> TestOutput:
        return TestOutput(response="test", tone="neutral")

    def test_function_v2(input: TestInputV2) -> TestOutputV2:
        return TestOutputV2(response="test", tone="neutral", confidence=0.9)

    manager = SignatureManager(base_dir=temp_storage_dir)

    # Create first signature
    sig1, is_new1 = manager.get_or_create(
        test_function_v1, "test_function"
    )

    # Create second signature (different)
    sig2, is_new2 = manager.get_or_create(
        test_function_v2, "test_function"
    )

    assert is_new1 is True
    assert is_new2 is True
    assert sig1.signature_hash != sig2.signature_hash


def test_signature_persists_to_storage(temp_storage_dir):
    """Test that signatures are actually saved to storage."""
    from blackbox.storage import load_signature, get_all_signatures

    def test_function(input: TestInput) -> TestOutput:
        return TestOutput(response="test", tone="neutral")

    manager = SignatureManager(base_dir=temp_storage_dir)
    signature, is_new = manager.get_or_create(test_function, "test_function")

    # Load from storage using the hash
    loaded_sig = load_signature("test_function", signature.signature_hash, temp_storage_dir)
    assert loaded_sig is not None
    assert loaded_sig.signature_hash == signature.signature_hash

    # Check it appears in all signatures
    all_sigs = get_all_signatures("test_function", temp_storage_dir)
    assert len(all_sigs) == 1
    assert all_sigs[0].signature_hash == signature.signature_hash


def test_multiple_signatures_stored(temp_storage_dir):
    """Test that multiple different signatures can be stored."""

    def test_function_v1(input: TestInput) -> TestOutput:
        return TestOutput(response="test", tone="neutral")

    def test_function_v2(input: TestInputV2) -> TestOutputV2:
        return TestOutputV2(response="test", tone="neutral", confidence=0.9)

    manager = SignatureManager(base_dir=temp_storage_dir)

    # Create two different signatures
    sig1, _ = manager.get_or_create(test_function_v1, "test_function")
    sig2, _ = manager.get_or_create(test_function_v2, "test_function")

    # Check both are stored
    from blackbox.storage import get_all_signatures
    all_sigs = get_all_signatures("test_function", temp_storage_dir)
    assert len(all_sigs) == 2

    hashes = {sig.signature_hash for sig in all_sigs}
    assert sig1.signature_hash in hashes
    assert sig2.signature_hash in hashes


def test_function_name_defaults_to_func_name(temp_storage_dir):
    """Test that function_name defaults to func.__name__."""

    def my_custom_function(input: TestInput) -> TestOutput:
        return TestOutput(response="test", tone="neutral")

    manager = SignatureManager(base_dir=temp_storage_dir)
    signature, is_new = manager.get_or_create(
        my_custom_function, None
    )

    # Should use function name
    from blackbox.storage import get_all_signatures

    signatures = get_all_signatures("my_custom_function", temp_storage_dir)
    assert len(signatures) == 1
    assert signatures[0].signature_hash == signature.signature_hash
