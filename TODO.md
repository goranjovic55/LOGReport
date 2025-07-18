# TODO List

## Editor Configuration
- [ ] Configure VS Code with recommended extensions and settings for Python/Qt development
- [ ] Establish consistent code formatting rules (black, flake8, etc.)

## Linting/Static Analysis
- [ ] Implement automated linting with pylint/flake8
- [ ] Set up pre-commit hooks for code quality checks
- [ ] Add type hints throughout codebase

## Developer Awareness/Code Review
- [ ] Create code review checklist focusing on Pythonic syntax and idioms
- [ ] Document common debugging patterns and anti-patterns
- [ ] Establish naming convention guidelines

## Initial Setup & Environment Configuration
- [ ] Document development environment setup requirements
- [ ] Create automated setup script for new developers
- [ ] Verify all dependencies are properly versioned

## Code Structure & Design Patterns
- [ ] Review and document current architecture patterns
- [ ] Identify opportunities for better separation of concerns
- [ ] Standardize module organization and imports

## Debugging Techniques & Tools
- [ ] Implement configurable logging levels
- [ ] Add debug logging for critical workflows
- [ ] Document debugging workflow and tools

## Testing Practices
- [ ] Expand unit test coverage for file I/O operations
- [ ] Add integration tests for critical paths
- [ ] Implement test data generation utilities

## Version Control Enhancements
- [ ] Document git workflow best practices
- [ ] Create commit message guidelines
- [ ] Set up branch protection rules

## Code Optimization Opportunities
- [ ] Consolidate Log Writing Logic in commander_window.py
- [ ] Improve `current_token` Handling in commander_window.py
- [ ] Centralize Status Message Emitting in commander_window.py
- [ ] Add Error Handling for Missing Node Definitions in commander_window.py
- [ ] Convert Path Operations to use `pathlib` in commander_window.py
- [ ] Add Type Hinting and Docstrings in commander_window.py