# CI/CD Quick Setup Guide

Get your CI/CD pipelines running in 15 minutes!

## Prerequisites

- [ ] GitHub repository
- [ ] Admin access to repository
- [ ] PyPI account (for releases)
- [ ] Docker Hub account (optional, for container releases)

## Step-by-Step Setup

### Step 1: Copy Workflow Files (2 minutes)

Copy all workflow files to your repository:

```bash
# Create workflows directory
mkdir -p .github/workflows

# Copy the workflow files
cp path/to/tests.yml .github/workflows/
cp path/to/security.yml .github/workflows/
cp path/to/release.yml .github/workflows/
cp path/to/pr.yml .github/workflows/
cp path/to/dependabot.yml .github/

# Commit and push
git add .github/
git commit -m "ci: add GitHub Actions workflows"
git push origin main
```

### Step 2: Enable GitHub Actions (1 minute)

1. Go to your repository on GitHub
2. Click `Settings` > `Actions` > `General`
3. Under "Actions permissions", select:
   - ✅ **Allow all actions and reusable workflows**
4. Click **Save**

### Step 3: Configure Branch Protection (3 minutes)

1. Go to `Settings` > `Branches`
2. Click **Add branch protection rule**
3. Branch name pattern: `main`
4. Configure:
   - ✅ Require status checks to pass before merging
   - ✅ Require branches to be up to date before merging
   - Select status checks:
     - `lint`
     - `test (3.10)`
     - `test (3.11)`
     - `test (3.12)`
     - `type-check`
     - `dependency-scan`
     - `code-scan`
   - ✅ Require pull request reviews before merging
   - Required approvals: `1`
5. Click **Create**

### Step 4: Add Secrets (5 minutes)

#### Essential Secrets

Go to `Settings` > `Secrets and variables` > `Actions` > `New repository secret`

##### For Testing (Optional)
```
Name: CODECOV_TOKEN
Value: <your-codecov-token>
```

##### For Releases (Required for publishing)
```
Name: PYPI_API_TOKEN
Value: <your-pypi-token>

Name: TEST_PYPI_API_TOKEN
Value: <your-test-pypi-token>
```

##### For Docker (Optional)
```
Name: DOCKER_USERNAME
Value: <your-docker-username>

Name: DOCKER_PASSWORD
Value: <your-docker-token>
```

#### How to Get Tokens

**Codecov** (Optional, for coverage reports):
1. Sign up at https://codecov.io
2. Add your repository
3. Copy the upload token from repository settings

**PyPI** (Required for package publishing):
1. Create account at https://pypi.org
2. Go to Account Settings > API tokens
3. Click "Add API token"
   - Token name: `GitHub Actions`
   - Scope: `Entire account` (or specific project)
4. Copy the token (starts with `pypi-`)

**Docker Hub** (Optional, for container images):
1. Log in to https://hub.docker.com
2. Account Settings > Security > New Access Token
3. Description: `GitHub Actions`
4. Access permissions: `Read, Write, Delete`
5. Copy the token

### Step 5: Create Release Environments (3 minutes)

1. Go to `Settings` > `Environments`
2. Click **New environment**

#### Create `pypi` environment:
- Name: `pypi`
- Protection rules (optional):
  - ✅ Required reviewers: Add yourself
- Secrets:
  - Name: `PYPI_API_TOKEN`
  - Value: <your-pypi-token>

#### Create `testpypi` environment:
- Name: `testpypi`
- Secrets:
  - Name: `TEST_PYPI_API_TOKEN`
  - Value: <your-test-pypi-token>

### Step 6: Test Your Setup (1 minute)

Create a test branch and PR:

```bash
# Create test branch
git checkout -b test/ci-setup

# Make a small change
echo "# Testing CI/CD" >> README.md

# Commit with conventional commit format
git add README.md
git commit -m "docs: test CI/CD setup"

# Push and create PR
git push origin test/ci-setup
```

Then on GitHub:
1. Create a Pull Request from `test/ci-setup` to `main`
2. Check that all workflows run
3. Review the automated comments and labels
4. Merge if all checks pass

## Verification Checklist

After setup, verify everything works:

### Tests Workflow ✅
- [ ] Lint job passes
- [ ] Tests run on Python 3.10, 3.11, 3.12
- [ ] Type checking passes
- [ ] Coverage report generated

### Security Workflow ✅
- [ ] Dependency scan completes
- [ ] Secret scan runs
- [ ] Code scan finishes
- [ ] CodeQL analysis completes

### PR Workflow ✅
- [ ] PR title validation works
- [ ] Size label added automatically
- [ ] Auto-labels applied
- [ ] Coverage comment posted

### Release Workflow ✅
- [ ] Tag triggers release (test with `v0.0.1`)
- [ ] GitHub release created
- [ ] Artifacts uploaded
- [ ] PyPI publish works (if configured)

## Quick Test Commands

Test workflows locally before pushing:

```bash
# Install dependencies
python -m pip install --upgrade pip
pip install -e ".[dev]"

# Run linters
black src scripts tests --check
isort src scripts tests --check-only
flake8 src scripts tests
ruff check src scripts tests

# Run tests
pytest tests/ -v --cov=src

# Type check
mypy src --ignore-missing-imports

# Security scans (optional)
pip install bandit safety
bandit -r src scripts
safety check
```

## Customization

### Adjust Test Matrix

Edit `.github/workflows/tests.yml`:

```yaml
strategy:
  matrix:
    python-version: ['3.10', '3.11', '3.12']  # Add or remove versions
```

### Change Coverage Threshold

Edit `.github/workflows/pr.yml`:

```yaml
- name: Coverage Comment
  uses: py-cov-action/python-coverage-comment-action@v3
  with:
    MINIMUM_GREEN: 80  # Change threshold
    MINIMUM_ORANGE: 70
```

### Modify Security Scan Frequency

Edit `.github/workflows/security.yml`:

```yaml
schedule:
  - cron: '0 2 * * *'  # Daily at 2 AM
  # Change to:
  - cron: '0 2 * * 1'  # Weekly on Monday
```

### Customize Release Tags

Edit `.github/workflows/release.yml`:

```yaml
on:
  push:
    tags:
      - 'v*.*.*'        # Standard: v1.0.0
      # Or use:
      - 'release-*'     # Custom: release-1.0.0
```

## Troubleshooting

### Workflows Not Running

**Problem**: Workflows don't trigger after push

**Solutions**:
1. Check Actions are enabled: `Settings` > `Actions` > `General`
2. Verify workflow syntax: Use GitHub's workflow validator
3. Check branch protection doesn't block Actions

### Tests Failing

**Problem**: Tests pass locally but fail in CI

**Solutions**:
1. Check Python version matches: `python --version`
2. Verify all dependencies in `pyproject.toml`
3. Check environment variables are set
4. Look at detailed logs in Actions tab

### Secrets Not Working

**Problem**: Secrets not accessible in workflow

**Solutions**:
1. Verify secret name exactly matches workflow usage
2. Check secret is in correct scope (repo vs environment)
3. For environment secrets, ensure job has `environment:` key
4. Secrets are not available in PR from forks (security feature)

### Coverage Not Uploading

**Problem**: Coverage report not visible

**Solutions**:
1. Check `CODECOV_TOKEN` is set correctly
2. Verify Codecov token is valid (check codecov.io)
3. Look for errors in coverage upload step
4. Try setting `fail_ci_if_error: false` temporarily

### Release Not Publishing

**Problem**: Release created but not published to PyPI

**Solutions**:
1. Check `PYPI_API_TOKEN` is correct
2. Verify PyPI token has correct permissions
3. Check package name doesn't conflict on PyPI
4. Review PyPI publish logs for errors
5. Ensure `pyproject.toml` or `setup.py` is valid

## Next Steps

After setup is complete:

1. **Read Full Documentation**: See `CI_CD_DOCUMENTATION.md`
2. **Customize Workflows**: Adapt to your team's needs
3. **Set Up Notifications**: Add Slack/Discord webhooks
4. **Monitor Dashboards**: Use GitHub Insights
5. **Regular Maintenance**: Update actions versions monthly

## Support

Need help?

- 📖 Full docs: `.github/CI_CD_DOCUMENTATION.md`
- 🐛 Issues: Check workflow logs in Actions tab
- 💬 Discuss: Use GitHub Discussions or team chat

---

**Setup Time**: ~15 minutes  
**Difficulty**: Beginner-friendly  
**Last Updated**: 2025-10-24
