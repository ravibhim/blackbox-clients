"""
Tests for scoped function names in blackbox package.

Verifies that:
- Function names include module and qualname
- Storage directories use scoped names
- Signatures and examples store scoped names
- Collisions are prevented between functions with same name
"""

import shutil
from pathlib import Path
import pytest

from blackbox_python_sdk.decorator import blackbox
from blackbox_python_sdk.storage import (
    DEFAULT_STORAGE_DIR,
    get_function_dir,
    get_all_signatures,
    load_examples,
    load_signature
)


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


def test_module_level_function_scoping():
    """Test that module-level functions get scoped names."""
    @blackbox
    def process_data(input: str) -> str:
        """Process some data."""
        return f"processed: {input}"

    # Call the function to trigger capture
    result = process_data("test")

    # Expected scoped name includes <locals> since it's defined inside test function
    # In production, a true module-level function would be: module.function_name
    expected_name = f"{__name__}.test_module_level_function_scoping.<locals>.process_data"

    # Verify directory exists with scoped name
    func_dir = get_function_dir(expected_name)
    assert func_dir.exists(), f"Expected directory {func_dir} to exist"

    # Verify signature contains scoped name
    signatures = get_all_signatures(expected_name)
    assert len(signatures) > 0, "Expected at least one signature"
    assert signatures[0].function_name == expected_name


def test_class_method_scoping():
    """Test that class methods get scoped names with class name."""
    class CustomerService:
        @blackbox
        def generate_response(self, query: str) -> dict:
            """Generate customer service response."""
            return {"response": "Hello customer"}

    # Create instance and call method
    service = CustomerService()
    result = service.generate_response("help")

    # Expected scoped name includes <locals> for class defined in test function
    expected_name = f"{__name__}.test_class_method_scoping.<locals>.CustomerService.generate_response"

    # Verify directory exists with scoped name
    func_dir = get_function_dir(expected_name)
    assert func_dir.exists(), f"Expected directory {func_dir} to exist"

    # Verify signature contains scoped name
    signatures = get_all_signatures(expected_name)
    assert len(signatures) > 0
    assert signatures[0].function_name == expected_name

    # Verify examples contain scoped name
    examples = load_examples(expected_name)
    assert len(examples) > 0
    assert examples[0].function_name == expected_name


def test_collision_prevention():
    """Test that functions with same name but different scopes don't collide."""
    class CustomerService:
        @blackbox
        def generate_response(self, query: str) -> dict:
            """Generate customer service response."""
            return {"response": "customer"}

    class SalesService:
        @blackbox
        def generate_response(self, query: str) -> dict:
            """Generate sales response."""
            return {"response": "sales"}

    # Call both methods
    customer_service = CustomerService()
    sales_service = SalesService()

    customer_result = customer_service.generate_response("help")
    sales_result = sales_service.generate_response("buy")

    # Expected scoped names include <locals> for classes defined in test
    customer_name = f"{__name__}.test_collision_prevention.<locals>.CustomerService.generate_response"
    sales_name = f"{__name__}.test_collision_prevention.<locals>.SalesService.generate_response"

    # Verify both directories exist separately
    customer_dir = get_function_dir(customer_name)
    sales_dir = get_function_dir(sales_name)

    assert customer_dir.exists(), f"Expected {customer_dir} to exist"
    assert sales_dir.exists(), f"Expected {sales_dir} to exist"
    assert customer_dir != sales_dir, "Directories should be different"

    # Verify each has its own signatures
    customer_sigs = get_all_signatures(customer_name)
    sales_sigs = get_all_signatures(sales_name)

    assert len(customer_sigs) > 0
    assert len(sales_sigs) > 0
    assert customer_sigs[0].function_name == customer_name
    assert sales_sigs[0].function_name == sales_name

    # Verify each has its own examples
    customer_examples = load_examples(customer_name)
    sales_examples = load_examples(sales_name)

    assert len(customer_examples) > 0
    assert len(sales_examples) > 0
    assert customer_examples[0].function_name == customer_name
    assert sales_examples[0].function_name == sales_name


def test_nested_class_scoping():
    """Test that nested classes get proper scoped names."""
    class OuterService:
        class InnerAnalyzer:
            @blackbox
            def analyze(self, data: str) -> dict:
                """Analyze data."""
                return {"result": "analyzed"}

    # Create instance and call method
    analyzer = OuterService.InnerAnalyzer()
    result = analyzer.analyze("test data")

    # Expected scoped name includes <locals> and both class names
    expected_name = f"{__name__}.test_nested_class_scoping.<locals>.OuterService.InnerAnalyzer.analyze"

    # Verify directory exists
    func_dir = get_function_dir(expected_name)
    assert func_dir.exists(), f"Expected directory {func_dir} to exist"

    # Verify signature
    signatures = get_all_signatures(expected_name)
    assert len(signatures) > 0
    assert signatures[0].function_name == expected_name


def test_storage_directory_structure():
    """Test that storage uses flat directories with dots."""
    class MyService:
        @blackbox
        def my_method(self, x: int) -> int:
            return x * 2

    service = MyService()
    service.my_method(5)

    # Expected directory name with dots (includes <locals>)
    expected_name = f"{__name__}.test_storage_directory_structure.<locals>.MyService.my_method"
    expected_path = Path(DEFAULT_STORAGE_DIR) / expected_name

    # Verify flat structure (not hierarchical)
    assert expected_path.exists()
    assert expected_path.is_dir()

    # Verify subdirectories exist
    assert (expected_path / "signatures").exists()
    assert (expected_path / "examples").exists()


def test_signature_metadata_includes_function_name():
    """Test that signature YAML files include function_name field."""
    @blackbox
    def test_func(x: int) -> int:
        """Test function."""
        return x + 1

    test_func(42)

    expected_name = f"{__name__}.test_signature_metadata_includes_function_name.<locals>.test_func"

    # Load signature
    signatures = get_all_signatures(expected_name)
    assert len(signatures) > 0

    sig = signatures[0]

    # Verify function_name is stored
    assert sig.function_name == expected_name

    # Verify it's in the YAML file
    sig_file = Path(DEFAULT_STORAGE_DIR) / expected_name / "signatures" / f"{sig.signature_hash}.yaml"
    assert sig_file.exists()

    import yaml
    with open(sig_file) as f:
        data = yaml.safe_load(f)
        assert "function_name" in data
        assert data["function_name"] == expected_name


def test_example_metadata_includes_function_name():
    """Test that example YAML files include function_name field."""
    @blackbox
    def another_func(x: str) -> str:
        """Another function."""
        return x.upper()

    another_func("hello")

    expected_name = f"{__name__}.test_example_metadata_includes_function_name.<locals>.another_func"

    # Load examples
    examples = load_examples(expected_name)
    assert len(examples) > 0

    example = examples[0]

    # Verify function_name is stored
    assert example.function_name == expected_name

    # Verify it's in the YAML file
    example_dir = Path(DEFAULT_STORAGE_DIR) / expected_name / "examples"
    example_files = list(example_dir.glob("*.yaml"))
    assert len(example_files) > 0

    import yaml
    with open(example_files[0]) as f:
        data = yaml.safe_load(f)
        assert "function_name" in data
        assert data["function_name"] == expected_name


def test_module_level_collision_prevention():
    """Test that module-level functions in different modules would have different scopes."""
    # This test verifies the naming scheme would prevent collisions
    # even though we're in the same module for testing purposes

    @blackbox
    def process(data: str) -> str:
        return f"v1: {data}"

    # Simulate what would happen with same function name in different module
    # by checking the scoped name format
    result = process("test")

    expected_name = f"{__name__}.test_module_level_collision_prevention.<locals>.process"

    # Verify the function name includes module
    func_dir = get_function_dir(expected_name)
    assert func_dir.exists()

    # If this were in a different module (e.g., "other_module.process"),
    # it would create a different directory, preventing collisions
    other_module_name = "other_module.process"
    other_dir = get_function_dir(other_module_name)

    # These should be different paths
    assert func_dir != other_dir
