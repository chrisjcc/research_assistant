.PHONY: install test lint format clean \
        test-unit test-watch test-cov test-integration test-all

# 🧩 Installation
install:
	uv pip install -e ".[dev,ui]"

# 🧪 Core Testing
test:
	pytest tests/ -v --cov=src/research_assistant

# 📊 Test Coverage
test-cov:
	pytest tests/ --cov=src/research_assistant \
	              --cov-config=coverage.toml \
	              --cov-report=term-missing \
	              --cov-report=html \
	              -v
	@python scripts/check_coverage.py



# 🚀 Usage Examples:
# make test-unit          # Run only unit tests
# make test-watch          # Watch mode for TDD
# make test-all            # All tests including slow ones
# make test-integration    # Integration tests only
# make test-cov            # Full coverage report (HTML + terminal)
# pytest --pdb             # Drop into debugger on failure
# pytest --lf              # Run last failed test
# pytest tests/unit/test_schemas.py::TestAnalyst::test_create_valid_analyst -vv

# Unit tests only (fast subset)
test-unit:
	pytest tests/unit -v

# Integration tests only
test-integration:
	pytest tests/integration -v

# All tests, including slow ones (can be used for CI)
test-all:
	pytest tests -v -m "not skip"

# Watch mode (TDD)
test-watch:
	ptw --onfail "notify-send 'Test Failed'" tests/

# ✅ Linting & Formatting
lint:
	ruff check src/
	mypy src/

format:
	ruff format src/ tests/

# 🧹 Cleanup
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .coverage htmlcov/

# 💻 App Launchers
run-gradio:
	python app/gradio_app.py

run-streamlit:
	streamlit run app/streamlit_app.py
