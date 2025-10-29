# CI/CD Workflows Documentation

This document describes all GitHub Actions workflows configured for the Research Assistant project.

## Table of Contents

- [Workflows Overview](#workflows-overview)
- [Setup Requirements](#setup-requirements)
- [Workflow Details](#workflow-details)
- [Secrets Configuration](#secrets-configuration)
- [Best Practices](#best-practices)

## Workflows Overview

| Workflow | Trigger | Purpose | Duration |
|----------|---------|---------|----------|
| `tests.yml` | Push/PR to main/develop | Run tests, linting, type checks | ~5-10 min |
| `security.yml` | Push/PR/Schedule | Security scanning | ~5-15 min |
| `release.yml` | Tag push or manual | Create releases, publish packages | ~10-20 min |
| `pr.yml` | Pull request | PR validation and automation | ~2-5 min |

## Setup Requirements

### Required Secrets

Configure these secrets in your GitHub repository settings (`Settings > Secrets and variables > Actions`):

#### For Testing
- `CODECOV_TOKEN`: Token for Codecov coverage reporting (optional)

#### For Releases
- `PYPI_API_TOKEN`: PyPI API token for publishing packages
- `TEST_PYPI_API_TOKEN`: TestPyPI API token for pre-release testing
- `DOCKER_USERNAME`: Docker Hub username
- `DOCKER_PASSWORD`: Docker Hub password/token

#### For Notifications (Optional)
- `SLACK_WEBHOOK_URL`: Slack webhook for notifications
- `DISCORD_WEBHOOK_URL`: Discord webhook for notifications

### Repository Settings

1. **Enable GitHub Actions**
   - Go to `Settings > Actions > General`
   - Select "Allow all actions and reusable workflows"

2. **Branch Protection Rules**
   ```
   Branch: main
   - Require status checks to pass before merging
   - Require branches to be up to date before merging
   - Required status checks:
     - lint
     - test (Python 3.10, 3.11, 3.12)
     - type-check
     - dependency-scan
     - code-scan
   - Require pull request reviews before merging (1 approval)
   - Dismiss stale pull request approvals when new commits are pushed
   ```

3. **Environments**
   Create these environments in `Settings > Environments`:
   - `pypi`: For production PyPI releases
   - `testpypi`: For TestPyPI releases

## Workflow Details

### 1. Tests Workflow (`tests.yml`)

**Purpose**: Automated testing, linting, and type checking

**Triggered by**:
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop` branches

**Jobs**:

#### 1.1 Lint Job
Performs code quality checks:
- **flake8**: Python syntax and style errors
- **black**: Code formatting verification
- **isort**: Import sorting verification
- **ruff**: Modern Python linter (fast, comprehensive)

**Configuration**:
```yaml
# Lint settings
Max line length: 100
Max complexity: 15
Python version: 3.11
```

#### 1.2 Test Job
Runs test suite across multiple Python versions:
- **Matrix strategy**: Python 3.10, 3.11, 3.12
- **Unit tests**: Fast, isolated tests
- **Integration tests**: End-to-end workflow tests
- **Coverage**: XML, HTML, and terminal reports
- **Timeout**: 300s for unit, 600s for integration

**Test commands**:
```bash
pytest tests/unit/ -v --cov=src --cov-report=xml
pytest tests/integration/ -v --cov=src --cov-append
```

**Artifacts**:
- Coverage reports (HTML)
- Uploaded to Codecov

#### 1.3 Type Check Job
Static type analysis with mypy:
- **Strict mode**: Maximum type safety
- **HTML report**: Detailed type error visualization
- **Error codes**: Shows specific mypy error codes

**Configuration**:
```yaml
mypy:
  strict: true
  ignore_missing_imports: true
  pretty: true
  show_error_codes: true
```

#### 1.4 Test Summary Job
Aggregates all test results:
- Reports overall success/failure
- Runs even if individual jobs fail
- Provides clear status summary

### 2. Security Workflow (`security.yml`)

**Purpose**: Comprehensive security scanning

**Triggered by**:
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop` branches
- Scheduled daily at 2 AM UTC
- Manual workflow dispatch

**Jobs**:

#### 2.1 Dependency Scan
Identifies vulnerable dependencies:
- **Safety**: Checks against known vulnerability databases
- **pip-audit**: Audits Python packages for security issues
- **Reports**: JSON format for analysis

**Output**:
```json
{
  "vulnerabilities": [...],
  "packages": [...],
  "summary": {...}
}
```

#### 2.2 Secret Scan
Detects accidentally committed secrets:
- **TruffleHog OSS**: Scans git history for secrets
- **Verified secrets only**: Reduces false positives
- **Full history**: Scans entire git history

**Detected types**:
- API keys
- Private keys
- Passwords
- Tokens
- Connection strings

#### 2.3 Code Scan
Static analysis for security issues:
- **Bandit**: Python security linter
  - Severity levels: Low, Medium, High
  - Confidence levels: Low, Medium, High
- **Semgrep**: Pattern-based code analysis
  - Security rules
  - Best practice rules

**Common findings**:
- SQL injection risks
- Command injection
- Hardcoded credentials
- Weak cryptography
- Insecure deserialization

#### 2.4 CodeQL Analysis
Advanced semantic code analysis:
- **GitHub's native scanner**
- **Security queries**: Extended security ruleset
- **Quality queries**: Code quality issues
- **SARIF output**: Uploaded to Security tab

#### 2.5 License Scan
Verifies dependency licenses:
- **pip-licenses**: Generates license report
- **Incompatible check**: Flags GPL/AGPL licenses
- **Reports**: JSON and Markdown formats

**Blocked licenses**:
- GPL-2.0, GPL-3.0
- AGPL-3.0
- (Configurable based on your policy)

#### 2.6 Container Scan (Optional)
Scans Docker images for vulnerabilities:
- **Trivy**: Multi-purpose security scanner
- **OS packages**: Ubuntu/Debian packages
- **Application dependencies**: Python packages
- **SARIF upload**: Results in Security tab

**Only runs if**:
- `Dockerfile` exists
- Push or scheduled event

### 3. Release Workflow (`release.yml`)

**Purpose**: Automated versioning, packaging, and distribution

**Triggered by**:
- Git tags matching `v*.*.*` (e.g., v1.0.0)
- Manual workflow dispatch with version input

**Jobs**:

#### 3.1 Validate
Pre-release validation:
- Runs full test suite
- Validates version format (semantic versioning)
- Ensures quality before release

**Version format**:
```regex
^v[0-9]+\.[0-9]+\.[0-9]+$
Example: v1.0.0, v2.1.3
```

#### 3.2 Build
Package creation:
- **Python package**: Wheel (.whl) and source (.tar.gz)
- **Build tools**: `build`, `twine`, `wheel`
- **Validation**: Checks package integrity
- **Artifacts**: Uploaded for other jobs

#### 3.3 Create Release
GitHub release creation:
- **Automatic changelog**: Generated from git commits
- **Comparison link**: Shows diff from previous version
- **Release notes**: Formatted changelog
- **Draft/Prerelease**: Configurable

**Changelog format**:
```markdown
## What's Changed
- feat: Add new feature (abc123)
- fix: Resolve bug (def456)
- docs: Update documentation (ghi789)

**Full Changelog**: https://github.com/user/repo/compare/v1.0.0...v1.1.0
```

#### 3.4 Upload Assets
Attach build artifacts to release:
- Python packages (.whl, .tar.gz)
- Additional assets (optional)

#### 3.5 Publish PyPI
Publishes to Python Package Index:
- **Production**: pypi.org
- **Test**: test.pypi.org (for prereleases)
- **Trusted publishing**: Uses OIDC token (recommended)
- **Skip existing**: Prevents duplicate uploads

**Environments**:
- `pypi`: Requires approval (optional)
- `testpypi`: Automatic for prereleases

#### 3.6 Docker Release (Optional)
Multi-platform Docker image:
- **Platforms**: linux/amd64, linux/arm64
- **Registries**: Docker Hub, GitHub Container Registry
- **Tags**:
  - `latest`: Most recent stable release
  - `1.0.0`: Specific version
  - `1.0`: Minor version
  - `1`: Major version

**Image naming**:
```
docker.io/username/research-assistant:latest
ghcr.io/username/research-assistant:1.0.0
```

#### 3.7 Notify
Post-release notifications:
- Status summary
- Results of all publishing jobs
- Optional: Slack/Discord webhooks

### 4. Pull Request Workflow (`pr.yml`)

**Purpose**: PR validation and automation

**Triggered by**:
- Pull request opened
- Pull request synchronized (new commits)
- Pull request reopened
- Pull request marked ready for review

**Jobs**:

#### 4.1 PR Validation
Enforces PR standards:
- **Title format**: Conventional commits
  ```
  feat(scope): description
  fix(api): resolve bug
  docs: update README
  ```
- **Size check**: Warns about large PRs
- **File count**: Monitors PR complexity

**Conventional commit types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting changes
- `refactor`: Code restructuring
- `perf`: Performance improvement
- `test`: Test additions/changes
- `chore`: Maintenance tasks
- `ci`: CI/CD changes
- `build`: Build system changes
- `revert`: Revert previous commit

#### 4.2 Size Labeling
Automatic size labels:
- `size/XS`: < 100 lines changed
- `size/S`: 100-300 lines
- `size/M`: 300-1000 lines
- `size/L`: 1000-3000 lines
- `size/XL`: > 3000 lines

**Benefits**:
- Helps reviewers prioritize
- Encourages smaller PRs
- Tracks PR complexity

#### 4.3 Dependency Review
Analyzes dependency changes:
- **Security vulnerabilities**: Blocks PRs with vulnerable deps
- **License compliance**: Checks for incompatible licenses
- **Severity threshold**: Configurable (default: moderate)

#### 4.4 Code Coverage
Coverage reporting on PRs:
- **Diff coverage**: New code coverage
- **Total coverage**: Overall project coverage
- **Comment**: Posts results as PR comment
- **Thresholds**:
  - Green: ≥80%
  - Orange: 70-80%
  - Red: <70%

#### 4.5 Auto-labeling
Automatic label assignment:
- `code`: Changes in `src/`
- `tests`: Changes in `tests/`
- `documentation`: Changes in docs/README
- `ci/cd`: Changes in `.github/workflows/`
- `dependencies`: Changes in requirements files

#### 4.6 PR Comment
Automated status comment:
- Validation results
- Coverage summary
- Next steps for author
- Links to failed checks

## Secrets Configuration

### Setting up Secrets

1. **Navigate to Secrets**:
   ```
   Your Repo > Settings > Secrets and variables > Actions
   ```

2. **Add Repository Secrets**:
   Click "New repository secret" and add each required secret

3. **Add Environment Secrets** (for releases):
   ```
   Your Repo > Settings > Environments
   ```
   - Create `pypi` environment
   - Add `PYPI_API_TOKEN` to environment secrets
   - Repeat for `testpypi`

### Obtaining Tokens

#### Codecov Token
```bash
# Sign up at codecov.io
# Add your repository
# Copy token from repository settings
```

#### PyPI Token
```bash
# 1. Create account at pypi.org
# 2. Go to Account Settings > API tokens
# 3. Create token with scope "Entire account" or specific project
# 4. Copy token (starts with `pypi-`)
```

#### Docker Hub Token
```bash
# 1. Log in to hub.docker.com
# 2. Account Settings > Security > New Access Token
# 3. Name: "GitHub Actions"
# 4. Permissions: Read, Write, Delete
# 5. Copy token
```

## Best Practices

### 1. Development Workflow

**Feature branches**:
```bash
git checkout -b feat/new-feature
# Make changes
git commit -m "feat(api): add new endpoint"
git push origin feat/new-feature
# Create PR to develop
```

**Release process**:
```bash
# 1. Merge develop to main
git checkout main
git merge develop

# 2. Create tag
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0

# 3. Workflow automatically creates release
```

### 2. Writing Good Commits

Follow conventional commits:
```bash
# Good
git commit -m "feat(auth): add JWT authentication"
git commit -m "fix(api): resolve race condition in user creation"
git commit -m "docs: update API documentation"

# Bad
git commit -m "updates"
git commit -m "fix stuff"
git commit -m "wip"
```

### 3. Managing Failing Checks

**Local testing before push**:
```bash
# Run linters
black src scripts tests --check
isort src scripts tests --check-only
flake8 src scripts tests
ruff check src scripts tests

# Run tests
pytest tests/ -v --cov=src

# Type checking
mypy src
```

**Fix common issues**:
```bash
# Auto-fix formatting
black src scripts tests
isort src scripts tests

# Fix imports
isort src scripts tests --force-single-line-imports

# View specific errors
pytest tests/unit/test_nodes.py::test_create_analysts -vv
```

### 4. Security Best Practices

**Never commit secrets**:
```bash
# Use environment variables
export OPENAI_API_KEY="sk-..."

# Use .env files (gitignored)
echo "OPENAI_API_KEY=sk-..." > .env

# In code
from dotenv import load_dotenv
load_dotenv()
```

**Review security findings**:
```bash
# Check Security tab regularly
# Your Repo > Security > Code scanning alerts
# Address High and Critical findings immediately
```

### 5. Optimizing CI/CD Performance

**Cache dependencies**:
```yaml
- uses: actions/cache@v4
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-lint-${{ hashFiles('pyproject.toml', 'pdm.lock', 'poetry.lock', 'poetry.toml', 'setup.cfg') }}
```

**Run tests in parallel**:
```yaml
strategy:
  matrix:
    python-version: ['3.10', '3.11', '3.12']
```

**Skip unnecessary runs**:
```yaml
on:
  push:
    paths-ignore:
      - '**.md'
      - 'docs/**'
```

## Troubleshooting

### Common Issues

#### 1. Tests Failing Locally But Passing in CI
```bash
# Ensure same Python version
python --version

# Clear pytest cache
pytest --cache-clear

# Check for file system case sensitivity
# (Windows vs Linux)
```

#### 2. Coverage Drops Unexpectedly
```bash
# Check coverage report
pytest --cov=src --cov-report=html
open htmlcov/index.html

# Add missing tests
```

#### 3. Linting Errors
```bash
# Auto-fix most issues
black src scripts tests
isort src scripts tests

# Check remaining issues
flake8 src scripts tests
```

#### 4. Type Checking Errors
```bash
# Run mypy locally
mypy src --pretty

# Add type hints
def my_function(arg: str) -> int:
    return len(arg)

# Use type: ignore for third-party issues
import third_party  # type: ignore
```

#### 5. Security Scan False Positives
```yaml
# In security.yml, add exceptions
- name: Run Bandit
  run: |
    bandit -r src --skip B101,B601  # Skip specific checks
```

#### 6. Release Workflow Not Triggering
```bash
# Ensure tag format is correct
git tag v1.0.0  # ✓ Correct
git tag 1.0.0   # ✗ Wrong (missing 'v')

# Push tags
git push origin --tags
```

## Monitoring and Metrics

### Key Metrics to Track

1. **Test Success Rate**: Should be >95%
2. **Average Build Time**: Target <10 minutes
3. **Coverage Trend**: Should maintain or increase
4. **Security Findings**: Track and reduce over time
5. **Release Frequency**: Indicates development velocity

### Dashboard Setup

Use GitHub Insights:
```
Your Repo > Insights > Actions
```

Monitor:
- Workflow runs
- Success/failure rates
- Execution times
- Billable minutes

## Further Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Python Testing Best Practices](https://docs.pytest.org/en/latest/goodpractices.html)
- [Security Scanning Tools](https://github.com/marketplace?category=security&type=actions)

---

**Last Updated**: 2025-10-24  
**Maintained by**: Development Team
