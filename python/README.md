# Blackbox Python SDK

Automatic evolution tracking for AI functions. Capture examples as you develop.

## Installation

```bash
pip install git+https://github.com/ravibhim/blackbox-clients.git#subdirectory=python
```

## Quick Start

```python
import blackbox

# Initialize with your project key
blackbox.init(key="bbc_proj_your_key_here")

# Decorate your function
@blackbox
async def generate_response(query: str, context: str) -> dict:
    """Your AI function."""
    result = await llm.generate(prompt=f"{query}\n{context}")
    return {"response": result.text, "tone": result.tone}

# Use normally - examples captured automatically
result = await generate_response("How do I reset my password?", "Premium user")
```

When you change the function signature (add params, change types), a new signature version is created automatically.

## Sync and Async

Both work identically - the decorator auto-detects function type:

```python
@blackbox
def sync_function(x: str) -> dict: ...

@blackbox
async def async_function(x: str) -> dict: ...
```

