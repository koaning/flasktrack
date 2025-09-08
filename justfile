# Default recipe - show available commands
default:
    @just --list

src:
    source .venv/bin/activate

# Install all dependencies
install: compile
    uv venv --allow-existing
    uv pip sync requirements.txt requirements-dev.txt
    uv pip install -e .

# Compile requirements files
compile:
    uv pip compile requirements-in.txt -o requirements.txt
    uv pip compile requirements-dev-in.txt -o requirements-dev.txt
    uv pip sync requirements.txt requirements-dev.txt

# Run tests
test:
    pytest tests/

# Run linter
lint:
    ruff check src/ tests/

# Fix linting issues
lint-fix:
    ruff check --fix src/ tests/

# Format code with ruff
format:
    ruff format src/ tests/

# Check code formatting
format-check:
    ruff format --check src/ tests/

# Fix all issues (lint + format)
fix:
    ruff check --fix src/ tests/
    ruff format src/ tests/

# Run all checks (format check and lint)
check: format-check lint

# Clean build artifacts
clean:
    rm -rf build/
    rm -rf dist/
    rm -rf *.egg-info
    rm -rf src/*.egg-info
    find . -type d -name __pycache__ -exec rm -rf {} +
    find . -type f -name "*.pyc" -delete
    find . -type f -name ".coverage" -delete
    find . -type d -name ".pytest_cache" -exec rm -rf {} +
    find . -type d -name ".ruff_cache" -exec rm -rf {} +
