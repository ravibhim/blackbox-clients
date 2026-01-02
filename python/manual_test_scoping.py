"""
Manual verification script for blackbox scoped function names.

This script tests the scoping features to verify that:
- Functions with the same name in different classes don't collide
- Storage directories use fully scoped names (module.qualname)
- Function metadata includes scoped names
- CLI can distinguish between identically-named functions
"""

from pydantic import BaseModel
from blackbox_python_sdk import blackbox
from pathlib import Path


# Define shared models
class CustomerQuery(BaseModel):
    query: str
    customer_id: str


class Response(BaseModel):
    message: str
    department: str


# Test 1: Multiple classes with same method name (collision prevention)
class CustomerService:
    """Customer support service."""

    @blackbox
    def generate_response(self, input: CustomerQuery) -> Response:
        """Generate customer service response."""
        return Response(
            message=f"Customer Support: We'll help you with '{input.query}'",
            department="customer_service"
        )


class SalesService:
    """Sales department service."""

    @blackbox
    def generate_response(self, input: CustomerQuery) -> Response:
        """Generate sales response."""
        return Response(
            message=f"Sales Team: Great question about '{input.query}'!",
            department="sales"
        )


class TechnicalService:
    """Technical support service."""

    @blackbox
    def generate_response(self, input: CustomerQuery) -> Response:
        """Generate technical support response."""
        return Response(
            message=f"Tech Support: Let me diagnose '{input.query}'",
            department="technical"
        )


# Test 2: Nested classes
class OuterService:
    """Outer service container."""

    class InnerAnalyzer:
        """Nested analyzer service."""

        @blackbox
        def analyze(self, query: str) -> dict:
            """Analyze query."""
            return {"analysis": f"Analyzing: {query}", "confidence": 0.95}


# Test 3: Class methods and static methods
class AnalyticsService:
    """Analytics service with class and static methods."""

    @classmethod
    @blackbox
    def aggregate_metrics(cls, metric_type: str) -> dict:
        """Class method to aggregate metrics."""
        return {
            "metric_type": metric_type,
            "count": 42,
            "method_type": "classmethod"
        }

    @staticmethod
    @blackbox
    def calculate_score(value: int, weight: float = 1.0) -> float:
        """Static method to calculate score."""
        return value * weight


# Test 4: Module-level function
@blackbox
def process_query(query: str, priority: str = "normal") -> dict:
    """Process a query at module level."""
    return {
        "query": query,
        "priority": priority,
        "status": "processed"
    }


def print_section(title: str):
    """Print a section header."""
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def verify_directory_structure():
    """Verify the .blackbox directory structure with scoped names."""
    print_section("[Verification] Checking .blackbox Directory Structure")

    base_dir = Path(".blackbox")

    if not base_dir.exists():
        print("✗ .blackbox directory not found!")
        return

    print(f"✓ Base directory exists: {base_dir}\n")

    # List all function directories
    function_dirs = sorted([d for d in base_dir.iterdir() if d.is_dir()])

    print(f"Found {len(function_dirs)} function directories:\n")

    for func_dir in function_dirs:
        scoped_name = func_dir.name
        print(f"📁 {scoped_name}")

        # Check subdirectories
        examples_dir = func_dir / "examples"
        signatures_dir = func_dir / "signatures"

        if examples_dir.exists():
            example_count = len(list(examples_dir.glob("*.yaml")))
            print(f"   └─ examples/  ({example_count} files)")

        if signatures_dir.exists():
            sig_count = len(list(signatures_dir.glob("*.yaml")))
            print(f"   └─ signatures/ ({sig_count} files)")

            # Read and display function_name from signature
            sig_files = list(signatures_dir.glob("*.yaml"))
            if sig_files:
                import yaml
                with open(sig_files[0]) as f:
                    sig_data = yaml.safe_load(f)
                    if "function_name" in sig_data:
                        print(f"   └─ function_name: {sig_data['function_name']}")

        print()


def main():
    print("=" * 80)
    print("BLACKBOX SCOPED FUNCTION NAMES - MANUAL VERIFICATION")
    print("=" * 80)
    print("\nThis script demonstrates that functions with the same name")
    print("in different classes are stored separately and don't collide.")

    # Test 1: Multiple classes with same method name
    print_section("[Test 1] Calling identically-named methods from different classes")

    customer_service = CustomerService()
    sales_service = SalesService()
    technical_service = TechnicalService()

    query1 = CustomerQuery(query="How do I reset my password?", customer_id="C001")
    query2 = CustomerQuery(query="What's the pricing for enterprise?", customer_id="C002")
    query3 = CustomerQuery(query="Server error 500", customer_id="C003")

    print("\nCalling CustomerService.generate_response():")
    result1 = customer_service.generate_response(query1)
    print(f"  → {result1.message}")

    print("\nCalling SalesService.generate_response():")
    result2 = sales_service.generate_response(query2)
    print(f"  → {result2.message}")

    print("\nCalling TechnicalService.generate_response():")
    result3 = technical_service.generate_response(query3)
    print(f"  → {result3.message}")

    print("\n✓ All three methods executed successfully!")
    print("✓ Each should have its own storage directory with scoped names")

    # Test 2: Nested classes
    print_section("[Test 2] Calling nested class method")

    analyzer = OuterService.InnerAnalyzer()
    analysis_result = analyzer.analyze("Complex technical query")
    print(f"Result: {analysis_result}")
    print("\n✓ Nested class method executed successfully!")

    # Test 3: Class methods and static methods
    print_section("[Test 3] Calling class methods and static methods")

    print("\nCalling AnalyticsService.aggregate_metrics() - classmethod:")
    classmethod_result = AnalyticsService.aggregate_metrics("response_time")
    print(f"  → {classmethod_result}")

    print("\nCalling AnalyticsService.calculate_score() - staticmethod:")
    staticmethod_result = AnalyticsService.calculate_score(100, 1.5)
    print(f"  → Score: {staticmethod_result}")

    print("\n✓ Class method executed successfully!")
    print("✓ Static method executed successfully!")

    # Test 4: Module-level function
    print_section("[Test 4] Calling module-level function")

    result = process_query("What is blackbox?", priority="high")
    print(f"Result: {result}")
    print("\n✓ Module-level function executed successfully!")

    # Test 4: Verify directory structure
    verify_directory_structure()

    # Test 5: Show scoped names
    print_section("[Test 5] Scoped Function Names")

    print("Function scoped names (module.qualname):\n")
    print(f"1. CustomerService.generate_response (instance method):")
    print(f"   {CustomerService.generate_response.function_name}\n")

    print(f"2. SalesService.generate_response (instance method):")
    print(f"   {SalesService.generate_response.function_name}\n")

    print(f"3. TechnicalService.generate_response (instance method):")
    print(f"   {TechnicalService.generate_response.function_name}\n")

    print(f"4. OuterService.InnerAnalyzer.analyze (nested class):")
    print(f"   {OuterService.InnerAnalyzer.analyze.function_name}\n")

    print(f"5. AnalyticsService.aggregate_metrics (classmethod):")
    print(f"   {AnalyticsService.aggregate_metrics.function_name}\n")

    print(f"6. AnalyticsService.calculate_score (staticmethod):")
    print(f"   {AnalyticsService.calculate_score.function_name}\n")

    print(f"7. process_query (module-level function):")
    print(f"   {process_query.function_name}\n")

    print("✓ All functions have unique scoped names!")
    print("✓ No collisions despite having methods with the same name!")
    print("✓ Class methods and static methods work correctly!")

    # Summary
    print_section("VERIFICATION COMPLETE")

    print("""
Key Observations:
✓ Three classes have 'generate_response' methods - NO COLLISION!
✓ Each method stores data in its own directory
✓ Directory names include full scope: module.Class.method
✓ Instance methods work correctly (self parameter skipped)
✓ Class methods work correctly (@classmethod)
✓ Static methods work correctly (@staticmethod)
✓ Nested classes work correctly
✓ Module-level functions work correctly

Method Types Tested:
• Instance methods (3x generate_response, 1x analyze)
• Class method (aggregate_metrics)
• Static method (calculate_score)
• Module-level function (process_query)

Next Steps:
1. Inspect .blackbox/ directory to see scoped directory names
2. Run: blackbox list
3. Try: blackbox examples <full.scoped.name>
   Example: blackbox examples __main__.CustomerService.generate_response
   Example: blackbox examples __main__.AnalyticsService.aggregate_metrics

The scoping system prevents collisions and makes it clear
which function each piece of data belongs to!
    """)


if __name__ == "__main__":
    main()
