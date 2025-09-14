# Default recipe - show available commands
default:
    @just --list

# Install all dependencies
install:
    uv venv --allow-existing
    uv pip compile requirements-in.txt -o requirements.txt
    uv pip compile requirements-dev-in.txt -o requirements-dev.txt
    uv pip sync requirements.txt requirements-dev.txt
    uv pip install -e .

# Compile requirements files
compile:
    uv pip compile requirements-in.txt -o requirements.txt
    uv pip compile requirements-dev-in.txt -o requirements-dev.txt

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

anew name="demo":
    rm -rf {{name}}
    uv run ft init {{name}}
    cd {{name}} && just install 
    cd {{name}} && uv pip install "-e" "../."
    cd {{name}} && uv run ft scaffold Post user:references title:string contents:text 
    cd {{name}} && uv run ft add-admin john "john@example.com" --password john
    cd {{name}} && just run
