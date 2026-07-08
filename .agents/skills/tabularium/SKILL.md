```markdown
# tabularium Development Patterns

> Auto-generated skill from repository analysis

## Overview
This skill teaches the core development patterns and conventions used in the `tabularium` Python codebase. You'll learn how to structure files, write imports and exports, follow commit and test conventions, and apply common workflows for contributing and maintaining code in this repository.

## Coding Conventions

### File Naming
- Use **snake_case** for all file names.
  - Example: `data_loader.py`, `process_utils.py`

### Import Style
- Prefer **relative imports** within the package.
  - Example:
    ```python
    from .utils import parse_table
    from .models import TableModel
    ```

### Export Style
- Use **named exports** (explicitly define what is exported from a module).
  - Example:
    ```python
    __all__ = ['TableModel', 'parse_table']
    ```

### Commit Patterns
- Commit messages are **freeform** (no enforced prefixes).
- Typical commit message is short (average 11 characters).
  - Example:  
    ```
    fix bug
    add tests
    update docs
    ```

## Workflows

### Adding a New Module
**Trigger:** When you need to add new functionality as a separate module.
**Command:** `/add-module`

1. Create a new Python file using snake_case (e.g., `my_feature.py`).
2. Use relative imports to access existing utilities or models.
3. Define `__all__` to specify exported functions/classes.
4. Write corresponding tests in a `*.test.*` file.

### Running Tests
**Trigger:** To verify code correctness after changes.
**Command:** `/run-tests`

1. Locate all test files matching the pattern `*.test.*`.
2. Run tests using your preferred Python test runner (e.g., `pytest`, `unittest`).
   - Example:
     ```bash
     pytest
     ```
3. Review the output and fix any failing tests.

### Refactoring Code
**Trigger:** When improving or restructuring existing code.
**Command:** `/refactor`

1. Update file and function names to follow snake_case.
2. Change imports to use relative style if not already.
3. Adjust `__all__` as needed for named exports.
4. Update or add tests to cover refactored code.

## Testing Patterns

- Test files follow the pattern `*.test.*` (e.g., `data_loader.test.py`).
- The testing framework is **unknown**; use standard Python testing tools like `pytest` or `unittest`.
- Place tests alongside or near the modules they test.
- Example test file structure:
  ```python
  # data_loader.test.py
  from .data_loader import load_table

  def test_load_table():
      assert load_table("sample.csv") is not None
  ```

## Commands
| Command       | Purpose                                 |
|---------------|-----------------------------------------|
| /add-module   | Scaffold and add a new module           |
| /run-tests    | Run all test files in the repository    |
| /refactor     | Refactor code to match conventions      |
```