# Claude Development Guide for FlaskTrack

## Project Overview
FlaskTrack is a Rails-inspired Flask framework with scaffolding and auto-discovery capabilities.

## Environment Setup
This project uses **uv** for Python dependency management. All dependency operations should be performed using `uv` commands.

## Quick Start
```bash
# Create and activate virtual environment
just venv

# Install all dependencies
just install

# Compile requirements files from .in files
just compile
```

## Development Workflow

### Dependency Management
- **Always use `uv`** for managing Python dependencies
- Dependencies are defined in `requirements-in.txt` and `requirements-dev-in.txt`
- Run `just compile` to generate locked requirements files
- Run `just install` to sync and install all dependencies

### Common Commands
```bash
# Run tests
just test

# Format and lint code
just style

# Run all checks (style + tests)
just check

# Clean build artifacts
just clean
```

## Important Notes
- Virtual environment is managed with `uv venv`
- All package installations use `uv pip`
- The project uses Ruff for linting and formatting
- Tests are run with pytest via `uv run`

## Code Quality
Before committing changes:
1. Run `just style` to format and fix linting issues
2. Run `just test` to ensure all tests pass
3. Run `just check` for a complete validation

## Project Structure
- `/src/flasktrack/` - Main package source code
- `/tests/` - Test files
- `justfile` - Task automation commands
- `pyproject.toml` - Project configuration and metadata