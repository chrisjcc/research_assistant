# Type Checking & Validation Guide

This guide covers how to use the type system, protocols, and validation utilities in the research assistant.

## Table of Contents

1. [Setup & Configuration](#setup--configuration)
2. [Using Type Hints](#using-type-hints)
3. [Protocol-Based Programming](#protocol-based-programming)
4. [Runtime Validation](#runtime-validation)
5. [Pydantic Integration](#pydantic-integration)
6. [Running Type Checkers](#running-type-checkers)

---

## Setup & Configuration

### Install Type Checking Tools

```bash
# Install mypy and pyright
pip install mypy pyright

# Install type stubs for external libraries
pip install types-requests types-PyYAML
```

### Marker File

The `src/research_assistant/py.typed` file indicates this package supports type checking (PEP 561).

---

## Using Type Hints

### Basic Type Hints

```python
from typing import List, Dict, Optional

def process_analysts(
    analysts: List[Analyst],
    max_count: int,
    config: Optional[Dict[str, Any]] = None
) -> List[str]:
    """Process analysts with full type hints."""
    names: List[str] = []
    for analyst in analysts:
        names.append(analyst.name)
    return names[:max_count]
```

### Generic Types

```python
from typing import TypeVar, Generic, List

T = TypeVar('T')

class Cache(Generic[T]):
    """Generic cache class."""
    
    def __init__(self) -> None:
        self._data: Dict[str, T] = {}
    
    def get(self, key: str) -> Optional[T]:
        return self._data.get(key)
    
    def set(self, key: str, value: T) -> None:
        self._data[key] = value
```

### Type Aliases

```python
from research_assistant.types import StateDict, MessageList

def update_state(
    current: StateDict,
    updates: StateDict
) -> StateDict:
    """Update state with type aliases."""
    return {**current, **updates}
```

---

## Protocol-Based Programming

### Using Protocols

Protocols enable structural subtyping (duck typing with type safety).

```python
from research_assistant.types import LLMProvider, SearchProvider

def generate_text(llm: LLMProvider, prompt: str) -> str:
    """Works with any LLM that implements the protocol."""
    messages = [HumanMessage(content=prompt)]
    response = llm.invoke(messages)
    return response.content

# Any class with invoke() and with_structured_output() works
class MyCustomLLM:
    def invoke(self, messages):
        return "response"
    
    def with_structured_output(self, schema):
        return self

# Type checker accepts this
my_llm: LLMProvider = MyCustomLLM()
result = generate_text(my_llm, "Hello")
```

### Implementing Protocols

```python
from research_assistant.types import CacheProvider

class RedisCache:
    """Implements CacheProvider protocol."""
    
    def get(self, key: str) -> Optional[Any]:
        return self.redis_client.get(key)
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        self.redis_client.set(key, value, ex=ttl)
    
    def delete(self, key: str) -> None:
        self.redis_client.delete(key)
    
    def clear(self) -> None:
        self.redis_client.flushdb()

# Type checker knows this implements CacheProvider
cache: CacheProvider = RedisCache()
```

### Protocol Checking

```python
from research_assistant.types import implements_protocol, ensure_protocol

# Runtime check
if implements_protocol(my_obj, LLMProvider):
    print("Object implements LLMProvider")

# Raise if not implemented
ensure_protocol(my_obj, LLMProvider, "LLM instance")
```

---

## Runtime Validation

### Function Argument Validation

```python
from research_assistant.types import validate_function_args

@validate_function_args
def create_report(
    topic: str,
    max_analysts: int,
    config: Dict[str, Any]
) -> str:
    """Arguments are validated at runtime."""
    return f"Report on {topic}"

# This raises TypeError
create_report("AI", "not an int", {})  # TypeError: max_analysts must be int
```

### Type Validation

```python
from research_assistant.types import validate_type

def process(data: Any) -> None:
    # Validate type at runtime
    validate_type(data, List[str], "data")
    # Now we know data is List[str]
    for item in data:
        print(item.upper())
```

### Custom Validators

```python
from research_assistant.types import (
    validate_non_empty_string,
    validate_positive_number,
    validate_range
)

def create_user(name: str, age: int, score: float) -> None:
    validate_non_empty_string(name, "name")
    validate_positive_number(age, "age")
    validate_range(score, min_val=0.0, max_val=100.0, "score")
```

### Composite Validators

```python
from research_assistant.types import TypeValidator

validator = TypeValidator()

# Add custom rules
validator.add_rule(
    "valid_topic",
    lambda x: isinstance(x, str) and len(x) >= 3,
    "Topic must be string with at least 3 characters"
)

validator.add_rule(
    "analyst_count",
    lambda x: isinstance(x, int) and 1 <= x <= 10,
    "Analyst count must be between 1 and 10"
)

# Use validators
validator.validate("AI Safety", "valid_topic")  # OK
validator.validate(15, "analyst_count")  # Raises ValueError
```

---

## Pydantic Integration

### Model Validation

```python
from research_assistant.types import validate_pydantic_model
from research_assistant.core.schemas import Analyst

# Validate dictionary against model
analyst_data = {
    "name": "Dr. Smith",
    "role": "Researcher",
    "affiliation": "MIT",
    "description": "AI safety expert"
}

analyst = validate_pydantic_model(analyst_data, Analyst)
# Returns validated Analyst instance or raises ValidationError
```

### Decorator-Based Validation

```python
from research_assistant.types import validate_input_model, validate_output_model
from research_assistant.core.schemas import Analyst

@validate_input_model(Analyst, param_name="analyst")
def process_analyst(analyst: Dict[str, Any]) -> str:
    """Input is validated and converted to Analyst."""
    return analyst.name  # analyst is now Analyst instance

@validate_output_model(Analyst)
def create_analyst() -> Dict[str, Any]:
    """Output is validated against Analyst schema."""
    return {
        "name": "Alice",
        "role": "Researcher",
        "affiliation": "Stanford",
        "description": "NLP researcher"
    }
```

### Custom Pydantic Validators

```python
from pydantic import BaseModel, field_validator
from research_assistant.types import StringValidator, NumberValidator

class ResearchConfig(BaseModel):
    topic: str
    max_analysts: int
    temperature: float
    
    # Use pre-built validators
    @field_validator("topic")
    @classmethod
    def validate_topic(cls, v: str) -> str:
        return StringValidator.non_empty()(v)
    
    @field_validator("max_analysts")
    @classmethod
    def validate_analysts(cls, v: int) -> int:
        return NumberValidator.in_range(1, 10)(v)
    
    @field_validator("temperature")
    @classmethod
    def validate_temperature(cls, v: float) -> float:
        return NumberValidator.in_range(0.0, 2.0)(v)
```

---

## Running Type Checkers

### MyPy

```bash
# Check entire package
mypy src/research_assistant

# Check specific module
mypy src/research_assistant/core/schemas.py

# Generate HTML report
mypy --html-report mypy-report src/research_assistant

# Strict mode
mypy --strict src/research_assistant
```

### Pyright

```bash
# Check entire package
pyright src/research_assistant

# Watch mode
pyright --watch src/research_assistant
```

### Pre-commit Hook

Add to `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
        args: [--strict]
```

### Makefile Targets

```bash
# Run type checking
make typecheck

# Generate coverage report
make type-coverage

# Install type checking tools
make type-install
```

### CI/CD Integration

Type checking runs automatically on push/PR via GitHub Actions (see `.github/workflows/type-check.yml`).

---

## Best Practices

### 1. Always Use Type Hints

```python
# Good
def process_data(data: List[str], limit: int) -> List[str]:
    return data[:limit]

# Bad
def process_data(data, limit):
    return data[:limit]
```

### 2. Use Protocols for Interfaces

```python
# Good - flexible, testable
def search(provider: SearchProvider, query: str) -> List[Dict]:
    return provider.search(query)

# Less flexible - tied to specific class
def search(provider: TavilySearch, query: str) -> List[Dict]:
    return provider.search(query)
```

### 3. Validate at Boundaries

```python
# Validate inputs from external sources
@validate_input_model(Analyst)
def api_create_analyst(data: dict) -> Analyst:
    """Validate data from API request."""
    return data  # Already validated by decorator

# Validate internal functions with type hints only
def internal_process(analyst: Analyst) -> str:
    """Trust internal types."""
    return analyst.name
```

### 4. Use Type Aliases for Clarity

```python
# Clear and reusable
AnalystDict = Dict[str, Analyst]
SearchResultList = List[Dict[str, Any]]

def organize_analysts(analysts: AnalystList) -> AnalystDict:
    return {a.name: a for a in analysts}
```

### 5. Handle Optional Types Properly

```python
# Good - explicit handling
def get_config(key: str) -> Optional[str]:
    return config.get(key)

value = get_config("api_key")
if value is not None:
    # Type checker knows value is str here
    process_api_key(value)
else:
    handle_missing_key()
```

### 6. Use Generic Types Appropriately

```python
from typing import TypeVar, List, Callable

T = TypeVar('T')

def first(items: List[T]) -> Optional[T]:
    """Generic function preserves type."""
    return items[0] if items else None

# Type checker knows result is List[Analyst]
analysts: List[Analyst] = get_analysts()
first_analyst: Optional[Analyst] = first(analysts)
```

---

## Common Patterns

### Pattern 1: Validated Factory Functions

```python
from research_assistant.types import validate_output_model
from research_assistant.core.schemas import Analyst

@validate_output_model(Analyst)
def create_analyst_from_api(api_data: dict) -> dict:
    """Factory with automatic validation."""
    return {
        "name": api_data["full_name"],
        "role": api_data["job_title"],
        "affiliation": api_data["organization"],
        "description": api_data["bio"]
    }
```

### Pattern 2: Protocol-Based Dependency Injection

```python
from research_assistant.types import LLMProvider, SearchProvider

class ResearchOrchestrator:
    """Uses protocols for flexible dependencies."""
    
    def __init__(
        self,
        llm: LLMProvider,
        search: SearchProvider
    ) -> None:
        self.llm = llm
        self.search = search
    
    def research(self, topic: str) -> str:
        # Works with any compatible implementation
        results = self.search.search(topic)
        formatted = self.search.format_results(results)
        return self.llm.invoke([HumanMessage(content=formatted)])
```

### Pattern 3: Type-Safe Configuration

```python
from typing import Literal
from pydantic import BaseModel

OutputFormat = Literal["markdown", "json", "html"]

class OutputConfig(BaseModel):
    format: OutputFormat  # Type checker enforces valid values
    save_to_file: bool
    output_dir: str

# Type checker catches invalid format
config = OutputConfig(
    format="pdf",  # Error: invalid literal
    save_to_file=True,
    output_dir="./output"
)
```

### Pattern 4: Type Guards

```python
from typing import TypeGuard

def is_analyst_list(obj: Any) -> TypeGuard[List[Analyst]]:
    """Type guard for analyst lists."""
    return (
        isinstance(obj, list) and
        all(isinstance(item, Analyst) for item in obj)
    )

def process(data: Any) -> None:
    if is_analyst_list(data):
        # Type checker knows data is List[Analyst]
        for analyst in data:
            print(analyst.name)
```

### Pattern 5: Overloaded Functions

```python
from typing import overload, Union

@overload
def get_analysts(count: int) -> List[Analyst]: ...

@overload
def get_analysts(names: List[str]) -> List[Analyst]: ...

def get_analysts(
    count_or_names: Union[int, List[str]]
) -> List[Analyst]:
    """Type checker understands both signatures."""
    if isinstance(count_or_names, int):
        return fetch_n_analysts(count_or_names)
    else:
        return fetch_analysts_by_name(count_or_names)
```

---

## Troubleshooting

### Issue: "Module has no attribute" errors

**Solution:** Add type ignore comment or install type stubs
```python
from external_lib import something  # type: ignore[import]
```

### Issue: "Incompatible types" for valid code

**Solution:** Use cast or assert for type narrowing
```python
from typing import cast

value = get_value()  # Returns Any
typed_value = cast(str, value)  # Tell type checker it's str

# Or use assert
assert isinstance(value, str)
# Now type checker knows value is str
```

### Issue: Protocol not recognized

**Solution:** Ensure protocol is @runtime_checkable
```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class MyProtocol(Protocol):
    def method(self) -> str: ...
```

### Issue: Generic types too complex

**Solution:** Use type aliases
```python
# Complex
def process(
    data: Dict[str, List[Tuple[str, int]]]
) -> List[Dict[str, Any]]:
    pass

# Simplified
DataMap = Dict[str, List[Tuple[str, int]]]
ResultList = List[Dict[str, Any]]

def process(data: DataMap) -> ResultList:
    pass
```

---

## Type Checking Checklist

- [ ] All functions have type hints for parameters and return values
- [ ] Public APIs use protocols instead of concrete classes where appropriate
- [ ] Input validation at system boundaries (API, file I/O, user input)
- [ ] Pydantic models for complex data structures
- [ ] Type aliases for commonly used complex types
- [ ] `py.typed` marker file present
- [ ] MyPy passes with no errors in strict mode
- [ ] CI/CD includes type checking step
- [ ] Type stubs installed for external libraries

---

## Resources

- [PEP 484 - Type Hints](https://peps.python.org/pep-0484/)
- [PEP 544 - Protocols](https://peps.python.org/pep-0544/)
- [PEP 561 - Distributing Type Information](https://peps.python.org/pep-0561/)
- [MyPy Documentation](https://mypy.readthedocs.io/)
- [Pyright Documentation](https://github.com/microsoft/pyright)
- [Pydantic Documentation](https://docs.pydantic.dev/)
