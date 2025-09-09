# Default recipe - show available commands
default:
    @just --list

src:
    source .venv/bin/activate

# Install all dependencies
venv:
    uv venv --allow-existing
    source .venv/bin/activate 

install: compile
    uv venv --allow-existing
    uv pip sync requirements.txt requirements-dev.txt
    uv pip install -e .

# Compile requirements files
compile: venv
    uv pip compile requirements-in.txt -o requirements.txt
    uv pip compile requirements-dev-in.txt -o requirements-dev.txt
    uv pip sync requirements.txt requirements-dev.txt

# Run tests
test:
    uv run pytest tests/

# Fix all issues (lint + format)
style:
    uv run ruff check --fix src/ tests/
    uv run ruff format src/ tests/

# Run all checks (format check and lint)
check: style test

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
