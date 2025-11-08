# Contributing to Text Message Bot

Thank you for your interest in contributing to Text Message Bot! This document provides guidelines and instructions for contributing.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/your-username/Text_Message_Bot.git`
3. Create a virtual environment: `python -m venv venv`
4. Activate it: `source venv/bin/activate` (Linux/Mac) or `venv\Scripts\activate` (Windows)
5. Install dependencies: `pip install -r requirements-dev.txt`
6. Create a new branch: `git checkout -b feature/your-feature-name`

## Development Setup

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Run tests with coverage
pytest --cov=. --cov-report=html

# Format code
black .
isort .

# Lint code
flake8 .
mypy .
```

## Code Style

- Follow PEP 8 style guide
- Use type hints where possible
- Write docstrings for all functions and classes
- Keep functions focused and small
- Use meaningful variable and function names

## Testing

- Write tests for all new features
- Ensure all tests pass before submitting
- Aim for high test coverage
- Use pytest fixtures for test setup

## Submitting Changes

1. Make sure your code follows the style guidelines
2. Run all tests and ensure they pass
3. Update documentation if needed
4. Commit your changes with clear messages
5. Push to your fork
6. Create a Pull Request

## Commit Messages

Use clear, descriptive commit messages:
- `feat: Add new feature`
- `fix: Fix bug in X`
- `docs: Update documentation`
- `test: Add tests for X`
- `refactor: Refactor X module`

## Pull Request Process

1. Update README.md if needed
2. Update CHANGELOG.md with your changes
3. Ensure all CI checks pass
4. Request review from maintainers

## Questions?

Feel free to open an issue for questions or discussions.

