# Testing

## Quick Start

```bash
# Run all integration tests
make test-integration

# Run with coverage report
pytest tests/integration --cov=src/research_assistant --cov-report=html
```

## Test Results

| Status | Count | Percentage |
|--------|-------|------------|
| ✅ Passed | 24 | 82.8% |
| ⏭️ Skipped | 4 | 13.8% |
| 🔄 XFailed | 1 | 3.4% |
| ❌ Failed | 0 | 0% |
| **Total** | **29** | **100%** |

**Code Coverage**: 41.75% (target: 40%)

## Latest Test Run

```
========================================================
24 passed, 4 skipped, 1 xfailed in 16.50s
Coverage: 41.75% ✅
========================================================
```

### Skipped Tests

These tests are intentionally skipped:

1. `test_research_graph_missing_analysts` - Feature not implemented
2. `test_interview_with_real_llm` - Requires API key for VCR re-recording
3. `test_complete_workflow_with_real_apis` - Requires API keys
4. `test_research_sections_aggregation` - Complex parallel execution mocking

### Expected Failures (XFail)

1. `test_interview_graph_llm_failure` - Known LangGraph exception handling difference

## Test Categories

### Core Functionality (9 tests) ✅
- Interview graph construction and execution
- Research graph orchestration
- Multi-turn conversation handling
- Parallel interview execution

### Error Handling (3 tests) ✅
- LLM failure scenarios
- Search failure handling
- State recovery

### Performance (2 tests) ✅
- Execution time validation
- Parallel processing efficiency

### State Management (2 tests) ✅
- Checkpoint persistence
- Error recovery

### Edge Cases (3 tests) ✅
- Empty search results
- Short interviews
- Single analyst scenarios

### Regression Tests (2 tests) ✅
- Source deduplication
- Empty transcript handling

## Coverage by Module

| Module | Coverage | Files |
|--------|----------|-------|
| `prompts/` | 67-87% | ✅ Excellent |
| `tools/search.py` | 78% | ✅ Excellent |
| `graphs/` | 45-72% | ✅ Good |
| `nodes/` | 51-60% | ✅ Good |
| `core/schemas.py` | 62% | ✅ Good |
| `utils/` | 13-37% | ⚠️ Needs improvement |

## Running Specific Tests

```bash
# Run specific test class
pytest tests/integration/test_graph_execution.py::TestInterviewGraphIntegration -v

# Run tests matching pattern
pytest tests/integration -k "interview" -v

# Run with verbose output
pytest tests/integration -vv -s
```

## Contributing

When adding new features:

1. ✅ Write integration tests
2. ✅ Ensure all tests pass
3. ✅ Maintain coverage above 40%
4. ✅ Document skipped tests with clear reasons

## Troubleshooting

**ModuleNotFoundError**: `pip install -e .`  
**Coverage warning**: Tests pass, just increase coverage or lower threshold  
**VCR errors**: Delete `tests/cassettes/*.yaml` and re-record with API key

---

For detailed test documentation, see [docs/testing.md](docs/testing.md).
