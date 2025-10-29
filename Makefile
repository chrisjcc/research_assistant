.PHONY: install test lint format clean \
        test-unit test-watch test-cov test-integration test-all \
        debug pdb last-failed single-test \
        run-gradio run-streamlit help

# 🧭 Help
help: ## Show available make targets and their descriptions
	@echo ""
	@echo "Available make targets:"
	@echo "-----------------------"
	@grep -E '^[a-zA-Z_-]+:.*?##' Makefile | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""

# 📘 General Commands
install: ## Install package with dev and UI dependencies
	uv pip install -e ".[dev,ui]"

clean: ## Remove caches, coverage reports, and temporary files
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .coverage htmlcov/

# 🧪 Testing Commands
test: ## Run all tests with coverage
	pytest tests/ -v --cov=src/research_assistant

test-cov: ## Generate detailed coverage report (HTML + terminal) and enforce thresholds
	pytest tests/ --cov=src/research_assistant \
	              --cov-config=coverage.toml \
	              --cov-report=term-missing \
	              --cov-report=html \
	              -v
	@python scripts/check_coverage.py

test-unit: ## Run only unit tests (fast subset)
	pytest tests/unit -v --cov=src/research_assistant --cov-config=coverage.toml

test-integration: ## Run only integration tests
	pytest tests/integration -v --cov=src/research_assistant --cov-config=coverage.toml

test-all: ## Run all tests including slow or long-running ones (used for CI)
	pytest tests -v -m "not skip"

# 🧰 Debugging & TDD Utilities
test-watch: ## Run tests in watch mode with desktop notifications on failure
	ptw --onfail "notify-send 'Test Failed'" tests/

pdb: ## Drop into debugger on first failure
	pytest --pdb

last-failed: ## Re-run only the last failed test
	pytest --lf

single-test: ## Run a specific test case (edit path or override with TEST=<path>)
	pytest $(TEST)

# ✅ Code Quality
lint: ## Run static analysis using Ruff and MyPy
	ruff check src/
	mypy src/

format: ## Auto-format source and test files using Ruff
	ruff format src/ tests/

# 💻 App Launchers
run-gradio: ## Launch Gradio Web UI
	python app/gradio_app.py

run-streamlit: ## Launch Streamlit Web UI
	streamlit run app/streamlit_app.py
