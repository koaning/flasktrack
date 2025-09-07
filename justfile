# Default recipe - show available commands
default:
    @just --list

# Install all dependencies
install:
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
    pytest tests/

# Run tests with coverage
test-cov:
    pytest tests/ --cov=flasktrack --cov-report=term-missing

# Format code with black
format:
    black src/ tests/

# Check formatting without making changes
format-check:
    black --check src/ tests/

# Run linter
lint:
    ruff check src/ tests/

# Fix linting issues
lint-fix:
    ruff check --fix src/ tests/

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

# Build the package
build: clean
    python -m build

# Create a new virtual environment with uv
venv:
    uv venv
    echo "Run 'source .venv/bin/activate' to activate the virtual environment"

# Update dependencies
update:
    uv pip compile --upgrade requirements-in.txt -o requirements.txt
    uv pip compile --upgrade requirements-dev-in.txt -o requirements-dev.txt
    uv pip sync requirements.txt requirements-dev.txt