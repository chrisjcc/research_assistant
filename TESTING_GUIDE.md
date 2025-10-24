# Testing Guide

Comprehensive guide for testing the Research Assistant application.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Test Structure](#test-structure)
3. [Running Tests](#running-tests)
4. [Writing Tests](#writing-tests)
5. [Test Fixtures](#test-fixtures)
6. [Mocking Strategies](#mocking-strategies)
7. [Coverage](#coverage)
8. [CI/CD Integration](#cicd-integration)

---

## Quick Start

```bash
# Install test dependencies
pip install -e ".[dev]"

# Run all tests
make test

# Run with coverage
make test-cov

# Run only unit tests
make test-unit

# Run only integration tests
make test-integration
```

---

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures and configuration
├── unit/                    # Unit tests (fast, isolated)
│   ├── test_schemas.py     # Pydantic model tests
│   ├── test_nodes.py       # Node function tests
│   ├── test_state.py       # State management tests
│   ├── test_tools.py       # Tool tests
│   └── test_utils.py       # Utility function tests
├── integration/             # Integration tests (slower)
│   ├── test_graph_execution.py  # Graph workflow tests
│   ├── test_end_to_end.py       # Complete workflow tests
│   └── test_api_integration.py  # External API tests
├── cassettes/               # VCR.py recordings
└── fixtures/                # Sample data files
```

---

## Running Tests

### Basic Commands

```bash
# All tests
pytest tests/

# Specific test file
pytest tests/unit/test_schemas.py

# Specific test class
pytest tests/unit/test_schemas.py::TestAnalyst

# Specific test function
pytest tests/unit/test_schemas.py::TestAnalyst::test_create_valid_analyst

# With verbose output
pytest tests/ -v

# With very verbose output
pytest tests/ -vv
```

### Using Markers

```bash
# Run only unit tests
pytest tests/ -m unit

# Run only integration tests
pytest tests/ -m integration

# Skip slow tests
pytest tests/ -m "not slow"

# Run tests requiring API
pytest tests/ -m requires_api
```

### Using Makefile

```bash
# Run all tests
make test

# Unit tests only
make test-unit

# Integration tests only
make test-integration

# Fast tests (exclude slow)
make test-fast

# With coverage
make test-cov

# Watch mode (requires pytest-watch)
make test-watch

# Test specific file
make test-file FILE=tests/unit/test_schemas.py

# Test by pattern
make test-match PATTERN=test_analyst

# Test by marker
make test-marker MARKER=unit
```

---

## Writing Tests

### Unit Test Example

```python
import pytest
from research_assistant.core.schemas import Analyst

class TestAnalyst:
    """Test suite for Analyst model."""
    
    def test_create_valid_analyst(self):
        """Test creating a valid analyst."""
        analyst = Analyst(
            name="Dr. Test",
            role="Researcher",
            affiliation="University",
            description="Test description here"
        )
        
        assert analyst.name == "Dr. Test"
        assert analyst.role == "Researcher"
    
    def test_invalid_analyst_name(self):
        """Test validation fails for invalid name."""
        with pytest.raises(ValidationError):
            Analyst(
                name="",  # Invalid
                role="Researcher",
                affiliation="University",
                description="Description"
            )
```

### Integration Test Example

```python
import pytest

@pytest.mark.integration
class TestInterviewWorkflow:
    """Integration tests for interview workflow."""
    
    def test_complete_interview(
        self,
        sample_analyst,
        mock_llm,
        mock_web_search
    ):
        """Test complete interview execution."""
        graph = build_interview_graph(
            llm=mock_llm,
            web_search_tool=mock_web_search
        )
        
        initial_state = {
            "analyst": sample_analyst,
            "messages": [HumanMessage(content="Start")],
            "max_num_turns": 2
        }
        
        result = graph.invoke(initial_state)
        
        assert "sections" in result
        assert len(result["sections"]) > 0
```

### Parametrized Tests

```python
@pytest.mark.parametrize("input,expected", [
    ("test", True),
    ("", False),
    (None, False),
])
def test_validation(input, expected):
    """Test validation with various inputs."""
    result = validate_input(input)
    assert result == expected
```

---

## Test Fixtures

### Using Built-in Fixtures

```python
def test_with_sample_analyst(sample_analyst):
    """Use the sample_analyst fixture."""
    assert sample_analyst.name == "Dr. Alice Smith"

def test_with_mock_llm(mock_llm):
    """Use the mock_llm fixture."""
    response = mock_llm.invoke([])
    assert response is not None
```

### Creating Custom Fixtures

```python
# In conftest.py
@pytest.fixture
def custom_config():
    """Provide custom configuration."""
    return {
        "max_analysts": 5,
        "detailed_prompts": True
    }

# In test file
def test_with_custom_config(custom_config):
    """Use custom configuration."""
    assert custom_config["max_analysts"] == 5
```

### Fixture Scopes

```python
@pytest.fixture(scope="session")
def expensive_setup():
    """Run once per test session."""
    # Expensive setup
    yield resource
    # Cleanup

@pytest.fixture(scope="module")
def module_setup():
    """Run once per test module."""
    pass

@pytest.fixture(scope="function")  # Default
def function_setup():
    """Run before each test function."""
    pass
```

---

## Mocking Strategies

### Mocking LLM Responses

```python
from unittest.mock import Mock

# Simple mock
mock_llm = Mock()
mock_llm.invoke.return_value = AIMessage(content="Response")

# Custom response factory
@pytest.fixture
def mock_llm_with_response():
    def _create(response_text):
        mock = Mock()
        mock.invoke.return_value = AIMessage(content=response_text)
        return mock
    return _create

def test_with_custom_response(mock_llm_with_response):
    llm = mock_llm_with_response("Custom answer")
    result = llm.invoke([])
    assert result.content == "Custom answer"
```

### Mocking Search Tools

```python
@pytest.fixture
def mock_web_search():
    mock = Mock()
    mock.search.return_value = [
        {"url": "https://example.com", "content": "Test content"}
    ]
    mock.format_results.return_value = "<Document>Formatted</Document>"
    return mock
```

### Using Patch

```python
from unittest.mock import patch

def test_with_patch():
    with patch('module.function') as mock_func:
        mock_func.return_value = "mocked"
        result = call_code_that_uses_function()
        assert result == "mocked"
        assert mock_func.called

# As decorator
@patch('module.function')
def test_with_decorator(mock_func):
    mock_func.return_value = "mocked"
    # test code
```

---

## Coverage

### Viewing Coverage

```bash
# Generate coverage report
pytest tests/ --cov=src/research_assistant --cov-report=html

# Open in browser
open htmlcov/index.html

# Terminal report
pytest tests/ --cov=src/research_assistant --cov-report=term-missing
```

### Coverage Configuration

```ini
# pytest.ini
[coverage:run]
source = src/research_assistant
omit =
    */tests/*
    */__pycache__/*

[coverage:report]
precision = 2
fail_under = 80
show_missing = True
```

### Improving Coverage

1. **Identify uncovered code**:
   ```bash
   pytest --cov=src/research_assistant --cov-report=term-missing
   ```

2. **Focus on critical paths**:
   - Core business logic
   - Error handling
   - Edge cases

3. **Don't chase 100%**:
   - Some code is hard to test (UI, external APIs)
   - Focus on meaningful coverage
   - 80%+ is a good target

---

## VCR for API Testing

### Recording API Calls

```python
import vcr

my_vcr = vcr.VCR(
    cassette_library_dir='tests/cassettes',
    record_mode='once'
)

@my_vcr.use_cassette('test_api_call.yaml')
def test_with_real_api():
    """Test with real API (recorded)."""
    # First run: records actual API call
    # Subsequent runs: replays from cassette
    result = make_api_call()
    assert result is not None
```

### VCR Modes

- `once`: Record once, replay forever
- `new_episodes`: Record new, replay existing
- `all`: Always record (refresh cassettes)
- `none`: Never record, only replay

---

## Best Practices

### 1. Test Organization

```python
class TestFeature:
    """Group related tests together."""
    
    def test_happy_path(self):
        """Test normal operation."""
        pass
    
    def test_error_handling(self):
        """Test error conditions."""
        pass
    
    def test_edge_cases(self):
        """Test boundary conditions."""
        pass
```

### 2. Test Names

```python
# Good: Descriptive names
def test_analyst_creation_with_valid_data():
    pass

def test_analyst_creation_fails_with_empty_name():
    pass

# Bad: Vague names
def test_analyst():
    pass

def test_case1():
    pass
```

### 3. Arrange-Act-Assert

```python
def test_something():
    # Arrange: Set up test data
    analyst = create_test_analyst()
    
    # Act: Execute the code under test
    result = process_analyst(analyst)
    
    # Assert: Verify the outcome
    assert result.status == "success"
```

### 4. One Assertion Per Test (when possible)

```python
# Good
def test_analyst_has_correct_name():
    analyst = create_analyst()
    assert analyst.name == "Dr. Test"

def test_analyst_has_correct_role():
    analyst = create_analyst()
    assert analyst.role == "Researcher"

# Acceptable for related assertions
def test_analyst_properties():
    analyst = create_analyst()
    assert analyst.name == "Dr. Test"
    assert analyst.role == "Researcher"
    assert analyst.affiliation == "University"
```

### 5. Use Fixtures for Setup

```python
# Good: DRY with fixtures
@pytest.fixture
def configured_graph(mock_llm):
    return build_graph(llm=mock_llm)

def test_graph_execution(configured_graph):
    result = configured_graph.invoke(state)
    assert result is not None

# Bad: Repeated setup
def test_graph_execution():
    mock_llm = Mock()
    graph = build_graph(llm=mock_llm)
    result = graph.invoke(state)
    assert result is not None
```

---

## CI/CD Integration

### GitHub Actions

Tests run automatically on push/PR:

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
      - name: Run tests
        run: |
          pip install -e ".[dev]"
          pytest tests/ --cov=src/research_assistant
```

### Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: pytest-unit
        name: pytest-unit
        entry: pytest tests/unit/
        language: system
        pass_filenames: false
        always_run: true
```

---

## Debugging Tests

### Running with Debugger

```bash
# Run with pdb on failure
pytest tests/ --pdb

# Drop into pdb on error
pytest tests/ -x --pdb

# Use breakpoint() in code
def test_something():
    data = prepare_data()
    breakpoint()  # Debugger will stop here
    result = process(data)
```

### Verbose Output

```bash
# Show print statements
pytest tests/ -s

# Very verbose
pytest tests/ -vv

# Show locals on failure
pytest tests/ -l
```

### Test Specific Scenarios

```bash
# Run last failed tests
pytest --lf

# Run failed first
pytest --ff

# Stop on first failure
pytest -x

# Stop after N failures
pytest --maxfail=3
```

---

## Performance Testing

### Timing Tests

```python
import time

@pytest.mark.slow
def test_performance():
    """Test completes within time limit."""
    start = time.time()
    
    result = expensive_operation()
    
    duration = time.time() - start
    assert duration < 5.0  # Must complete in under 5 seconds
```

### Using pytest-benchmark

```python
def test_benchmark(benchmark):
    """Benchmark function performance."""
    result = benchmark(function_to_test, arg1, arg2)
    assert result is not None
```

---

## Common Patterns

### Testing Exceptions

```python
import pytest

def test_raises_value_error():
    """Test that ValueError is raised."""
    with pytest.raises(ValueError):
        risky_function()

def test_raises_with_match():
    """Test exception message."""
    with pytest.raises(ValueError, match="Invalid input"):
        risky_function()

def test_exception_details():
    """Inspect exception details."""
    with pytest.raises(ValueError) as exc_info:
        risky_function()
    
    assert "Invalid" in str(exc_info.value)
```

### Testing Async Code

```python
import pytest

@pytest.mark.asyncio
async def test_async_function():
    """Test async function."""
    result = await async_function()
    assert result is not None
```

### Testing Warnings

```python
import warnings
import pytest

def test_warning_raised():
    """Test that warning is raised."""
    with pytest.warns(UserWarning):
        function_that_warns()
```

### Testing Logging

```python
import logging

def test_logging(caplog):
    """Test logging output."""
    with caplog.at_level(logging.INFO):
        function_that_logs()
    
    assert "Expected message" in caplog.text
```

### Testing File Operations

```python
def test_file_creation(tmp_path):
    """Test file creation."""
    output_file = tmp_path / "test.txt"
    
    write_file(output_file, "content")
    
    assert output_file.exists()
    assert output_file.read_text() == "content"
```

---

## Test Data Management

### Inline Data

```python
def test_with_inline_data():
    """Small test data inline."""
    data = {
        "name": "Test",
        "value": 42
    }
    result = process(data)
    assert result is not None
```

### Fixture Files

```python
# tests/fixtures/sample_data.json
# Store larger test data in files

@pytest.fixture
def sample_data():
    """Load sample data from file."""
    import json
    from pathlib import Path
    
    fixture_path = Path(__file__).parent / "fixtures" / "sample_data.json"
    return json.loads(fixture_path.read_text())
```

### Factory Fixtures

```python
@pytest.fixture
def analyst_factory():
    """Factory for creating test analysts."""
    def _create(name="Dr. Test", role="Researcher"):
        return Analyst(
            name=name,
            role=role,
            affiliation="University",
            description="Test analyst description"
        )
    return _create

def test_with_factory(analyst_factory):
    """Create multiple analysts easily."""
    analyst1 = analyst_factory(name="Alice")
    analyst2 = analyst_factory(name="Bob")
    assert analyst1.name != analyst2.name
```

---

## Troubleshooting

### Tests Pass Locally But Fail in CI

**Common causes:**
- Environment differences
- Missing dependencies
- Timezone issues
- File path issues
- Race conditions

**Solutions:**
```bash
# Run in same Python version as CI
tox -e py311

# Check environment variables
env | grep TEST

# Use absolute paths or Path objects
from pathlib import Path
```

### Flaky Tests

**Identify:**
```bash
# Run test multiple times
pytest tests/test_flaky.py --count=10
```

**Fix:**
- Add proper waits/timeouts
- Mock time-dependent code
- Use fixtures to reset state
- Isolate tests better

### Slow Tests

**Identify:**
```bash
# Show slowest tests
pytest --durations=10
```

**Fix:**
- Mark as @pytest.mark.slow
- Use smaller test data
- Mock expensive operations
- Run in parallel: `pytest -n auto` (requires pytest-xdist)

---

## Test Checklist

When adding a new feature, ensure:

- [ ] Unit tests for core logic
- [ ] Integration tests for workflows
- [ ] Edge cases covered
- [ ] Error handling tested
- [ ] Documentation updated
- [ ] Coverage >80% for new code
- [ ] Tests pass locally
- [ ] Tests pass in CI

---

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest Best Practices](https://docs.pytest.org/en/stable/goodpractices.html)
- [VCR.py Documentation](https://vcrpy.readthedocs.io/)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)
- [Python Testing Best Practices](https://realpython.com/pytest-python-testing/)

---

## Quick Reference

### Common Pytest Commands

```bash
pytest                          # Run all tests
pytest -v                       # Verbose
pytest -s                       # Show print statements
pytest -x                       # Stop on first failure
pytest --lf                     # Run last failed
pytest --ff                     # Run failed first
pytest -k "test_name"          # Run tests matching pattern
pytest -m unit                  # Run tests with marker
pytest --pdb                    # Drop into debugger on failure
pytest --durations=10          # Show slowest tests
pytest --cov                    # Run with coverage
pytest tests/unit/             # Run specific directory
pytest tests/test_file.py      # Run specific file
pytest tests/test_file.py::TestClass::test_method  # Specific test
```

### Common Assertions

```python
assert value                    # Truthy
assert not value                # Falsy
assert a == b                   # Equality
assert a != b                   # Inequality
assert a > b                    # Greater than
assert a in b                   # Membership
assert isinstance(a, Type)      # Type checking
```

### Common Fixtures

```python
tmp_path                        # Temporary directory (function scope)
tmp_path_factory               # Temporary directory (session scope)
monkeypatch                    # Monkey patching
caplog                         # Capture log output
capsys                         # Capture stdout/stderr
request                        # Request context
```

---

## Example Test Suite

```python
"""Complete example test suite."""

import pytest
from research_assistant.core.schemas import Analyst

class TestAnalystCreation:
    """Test analyst creation."""
    
    def test_valid_creation(self):
        """Test creating valid analyst."""
        analyst = Analyst(
            name="Dr. Test",
            role="Researcher",
            affiliation="University",
            description="Test description here"
        )
        assert analyst.name == "Dr. Test"
    
    @pytest.mark.parametrize("name,valid", [
        ("Dr. Test", True),
        ("", False),
        ("A", False),
    ])
    def test_name_validation(self, name, valid):
        """Test name validation."""
        if valid:
            analyst = Analyst(
                name=name,
                role="Researcher",
                affiliation="Uni",
                description="Description"
            )
            assert analyst.name == name
        else:
            with pytest.raises(ValidationError):
                Analyst(
                    name=name,
                    role="Researcher",
                    affiliation="Uni",
                    description="Description"
                )
    
    def test_with_fixture(self, sample_analyst):
        """Test using fixture."""
        assert sample_analyst.name == "Dr. Alice Smith"

@pytest.mark.integration
class TestWorkflow:
    """Integration test for workflow."""
    
    def test_complete_flow(self, mock_llm, sample_analyst):
        """Test complete workflow."""
        # Setup
        graph = build_graph(llm=mock_llm)
        
        # Execute
        result = graph.invoke({
            "analyst": sample_analyst,
            "messages": []
        })
        
        # Verify
        assert "sections" in result
        assert len(result["sections"]) > 0
```

This testing infrastructure provides comprehensive coverage and makes it easy to maintain high code quality! 🎯
