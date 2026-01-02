"""
Demo script to test blackbox decorator manually.
Run this to generate examples and see signature evolution.
"""

from blackbox_python_sdk import blackbox
from pydantic import BaseModel

# Version 1: Simple Pydantic models
print("=" * 60)
print("PHASE 1: Creating examples with initial signature")
print("=" * 60)

class QueryInput(BaseModel):
    customer_query: str
    context: str

class ResponseOutput(BaseModel):
    response: str
    tone: str

@blackbox
def generate_response(query: QueryInput) -> ResponseOutput:
    """Generate customer support responses - Version 1."""
    return ResponseOutput(
        response=f"Thank you for contacting us about: {query.customer_query}",
        tone="helpful"
    )

# Call it a few times to create examples
print("\nCalling generate_response 3 times...")
result1 = generate_response(QueryInput(customer_query="I can't log in", context="Premium user"))
print(f"Example 1: {result1.response}")

result2 = generate_response(QueryInput(customer_query="Where is my order?", context="Order #12345"))
print(f"Example 2: {result2.response}")

result3 = generate_response(QueryInput(customer_query="How do I reset my password?", context="Free tier user"))
print(f"Example 3: {result3.response}")

print("\n" + "=" * 60)
print("PHASE 2: Evolving signature - adding max_tokens parameter")
print("=" * 60)

# Version 2: Add field to input model (signature change!)
class QueryInputV2(BaseModel):
    customer_query: str
    context: str
    max_tokens: int = 100  # NEW FIELD

class ResponseOutputV2(BaseModel):
    response: str
    tone: str
    tokens_used: int  # NEW FIELD

@blackbox
def generate_response(query: QueryInputV2) -> ResponseOutputV2:
    """Generate customer support responses - Version 2 with max_tokens."""
    response_text = f"Thank you for contacting us about: {query.customer_query}"
    # Simulate token limit affecting response
    if len(response_text) > query.max_tokens:
        response_text = response_text[:query.max_tokens] + "..."

    return ResponseOutputV2(
        response=response_text,
        tone="helpful",
        tokens_used=len(response_text)
    )

# Call it with new signature
print("\nCalling generate_response 2 times with new signature...")
result4 = generate_response(QueryInputV2(customer_query="I need a refund", context="Enterprise customer", max_tokens=50))
print(f"Example 4: {result4}")

result5 = generate_response(QueryInputV2(customer_query="Product not working", context="Standard user"))
print(f"Example 5: {result5}")

print("\n" + "=" * 60)
print("PHASE 3: Further evolution - adding next_steps field")
print("=" * 60)

# Version 3: Add field to output model (another signature change!)
class ResponseOutputV3(BaseModel):
    response: str
    tone: str
    tokens_used: int
    next_steps: list[str]  # NEW FIELD

@blackbox
def generate_response(query: QueryInputV2) -> ResponseOutputV3:
    """Generate customer support responses - Version 3 with action items."""
    response_text = f"Thank you for contacting us about: {query.customer_query}"
    if len(response_text) > query.max_tokens:
        response_text = response_text[:query.max_tokens] + "..."

    return ResponseOutputV3(
        response=response_text,
        tone="helpful",
        tokens_used=len(response_text),
        next_steps=["Check documentation", "Contact support if issue persists"]
    )

# Call it with newest signature
print("\nCalling generate_response 2 times with newest signature...")
result6 = generate_response(QueryInputV2(customer_query="Account suspended", context="VIP customer", max_tokens=150))
print(f"Example 6: {result6}")

result7 = generate_response(QueryInputV2(customer_query="Billing question", context="New user"))
print(f"Example 7: {result7}")

print("\n" + "=" * 60)
print("PHASE 4: Mixed types - Pydantic models + native types")
print("=" * 60)

# Version 4: Mix Pydantic model with native type parameters (signature change!)
class ResponseOutputV4(BaseModel):
    response: str
    tone: str
    tokens_used: int
    next_steps: list[str]
    confidence_score: float  # NEW FIELD

@blackbox
def generate_response(
    query: QueryInputV2,           # Pydantic model parameter
    urgency_level: str,            # Native type parameter
    max_retries: int = 3           # Native type parameter with default
) -> ResponseOutputV4:
    """Generate customer support responses - Version 4 with urgency and retry params."""
    response_text = f"[{urgency_level.upper()}] Thank you for contacting us about: {query.customer_query}"
    if len(response_text) > query.max_tokens:
        response_text = response_text[:query.max_tokens] + "..."

    return ResponseOutputV4(
        response=response_text,
        tone="helpful" if urgency_level != "critical" else "urgent",
        tokens_used=len(response_text),
        next_steps=["Check documentation", "Contact support if issue persists"],
        confidence_score=0.95
    )

# Call it with mixed types
print("\nCalling generate_response 2 times with mixed types...")
result8 = generate_response(
    QueryInputV2(customer_query="System down", context="Production environment", max_tokens=150),
    urgency_level="critical",
    max_retries=5
)
print(f"Example 8: {result8}")

result9 = generate_response(
    QueryInputV2(customer_query="Feature request", context="Free user"),
    urgency_level="low"
)
print(f"Example 9: {result9}")

print("\n" + "=" * 60)
print("COMPLETE! Examples captured across 4 signature versions")
print("=" * 60)
print("\nNow you can use the CLI to view examples and signatures:")
print("\n  blackbox list")
print("  blackbox examples generate_response")
print("  blackbox signatures generate_response")
print("  blackbox compare generate_response")
print()
