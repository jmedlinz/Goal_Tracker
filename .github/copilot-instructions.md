
---
description: "Use when: working on Python development. Covers interaction style, coding standards, naming conventions, testing, documentation, error handling, logging, toolchain configuration, and folder structure."
---

# Copilot Instructions

## Project Scope

This is a Python project. The codebase is organized under `hq-util4/<repo_name>/programs/`. See the README for project-specific context.

---

## Interaction Behavior

- Ask clarifying questions when the request is ambiguous or incomplete. Use the answers to refine understanding **before** generating code.
- Be concise and clear. Do not make assumptions or speculate without clear evidence.
- If a question is beyond your knowledge, say so and suggest where the user might find the answer.
- For **large or complex changes (> 300 lines)**, present a plan and require explicit user approval before implementing.
- Alert the user when switching modes (for example: plan, ask, or agent), switching LLMs, or otherwise changing the VS Code configuration would likely produce a better result, and include a brief rationale plus expected benefit.
- Always ask before reading the contents of a `.env` file — it may contain secrets. `.env.example` files are safe to read without asking.
- When referencing code in any response, always include the **filename and line number**.
---

## Role & Expertise

Act as an expert Python developer with strong skills in command-line tools, file system operations, data pipeline architecture and database integration. Apply debugging depth and performance optimization throughout. Prioritize correctness, security, and maintainability.

### Preferred Runtime Patterns

- Prefer using `report.py` functions for runtime output and logging instead of using `rich` directly in feature code.
- Use `rich` directly only when implementing or maintaining `report.py` itself.
- Prefer `pandas` for tabular data handling, `pyodbc` for SQL Server connectivity, and `tqdm` for long-running progress indicators.

---

## Database Guidelines

- Use the MSSQL extension in **read-only** mode — query and inspect the database, never modify it directly.
- **Never execute DDL or DML** (CREATE, ALTER, DROP, INSERT, UPDATE, DELETE) against a live database.
- All database changes must be handed off to the user for execution.
- Every database change must be documented in a `.sql` file in the `/database/` folder before the user applies it.

---

## Environment & Configuration

- Drive environment-specific behavior using config constants (e.g., `APPENV`, `DEV_ENV`, `TEST_ENV`, `PROD_ENV`) rather than magic strings.
- Do not introduce new environment schemes when existing config values already define behavior.
- In tests, initialize environment variables predictably in `conftest.py` so test behavior is deterministic.

---

## Python Coding Standards

### Naming Conventions

| Context | Convention |
|---------|------------|
| Variables, functions, modules | `snake_case` |
| Classes | `PascalCase` |
| Constants | `ALL_CAPS` |
| Private module functions | `_leading_underscore` |

- Use descriptive, explicit variable names — prefer clarity over brevity.
- Strongly prefer **named constants over hardcoded values**.
- Never use camelCase for any identifier.

### Function & Module Structure

- `main()` is always the **last function** in the file, guarded by `if __name__ == "__main__":`.
- Place helper functions above the functions that call them:
  - Used by one function → directly above that function.
  - Used by multiple functions → above all callers.
  - Larger than ~10 lines → move to a separate module from `main()`.
- Avoid code duplication; extract reusable logic into named functions.
- Adhere to the existing coding style in the file being edited.

### Type Hints & Return Types

- Add type hints to all function parameters.
- Add return type annotations only when the return value is non-obvious or important for the caller.
- Do not annotate `-> None` unless it meaningfully improves clarity.

### Imports & Dependencies

- Suggest helpful packages when they meaningfully improve the solution; do not add unused imports.
- Use a `.env` file for environment variables; load with `python-dotenv`.

---

## Testing & Quality

- Use **pytest** (never `unittest`) and pytest plugins for all tests.
- Place all tests in the designated test directory (typically `hq-util4/<repo_name>/programs/tests/`). Create `__init__.py` files where needed.
- Follow the **Arrange, Act, Assert** (AAA) pattern.
- All test functions must have type annotations and docstrings.
- Prefer tests that avoid direct database, file, or folder manipulation whenever possible.
- When filesystem interaction improves test quality, use temporary locations and ensure cleanup after tests.
- Mark code with `# pragma: no cover` when it is effectively untestable or when testing it would add brittle, low-value tests.
- Let the user make all git decisions and git commits.
- `vulture` detects dead code. Add intentionally unused symbols to `whitelist.py`.

---

## Documentation & Comments

### Docstrings

- Every function must have a docstring — including private helpers — describing its purpose, parameters, and return value.
- Write in **present tense, active voice, second person** (e.g., "Returns the filtered DataFrame.").

### File Headers

- Each file must start with a header comment describing its purpose and any important context.

### Inline Comments

- Keep all existing comments. Add new comments where they add value.
- Comments explain **why**, not just what. Avoid restating what the code does.
- Always add comments for non-obvious logic or complex algorithms.
- Use comment markers consistently:
  - `#!` for very important notes and high-risk troubleshooting context you must not miss.
  - `# *` for important notes that are lower priority than `#!` notes.
  - `# TODO:` for deferred work, follow-up checks, or future improvements.
  - `# @param` for parameter-specific inline notes when needed.
- Add a `# Sources:` block with URLs when implementation details are adapted from external references.

### README & Other Docs

- Use README files and docstrings as primary documentation artifacts.
- Format all documentation in proper Markdown: present tense, active voice, second person.

### Accessibility

- Ensure any web-facing components or reports comply with **WCAG 2.1 AA+** standards.

---

## Error Handling & Logging

- Use `try/except` blocks consistently. Capture context in every exception handler (e.g., the input that triggered the error, the operation that failed).
- Provide user-friendly error messages. Log full technical detail separately.
- Implement detailed structured logging and reporting using the `report.py` module at:
  ```
  hq-util4/<repo_name>/programs/report.py
  ```
  `<repo_name>` is the repository name in `lowercase_with_underscores`.
- Prefer this `report.py` function intent:
  - `report_info()` for routine status.
  - `report_comment()` for supporting details.
  - `report_section()` and `report_subsection()` for structure.
  - `report_warning()` for warnings.
  - `report_error()` for errors.
  - `report_exception()` when handling exceptions.
  - `*_continue` variants (for example, `report_warning_continue`) to continue a prior warning/error line or add follow-on detail to the parent message.

---

## Toolchain Configuration

The pre-commit pipeline enforces the following. Apply these settings consistently when generating code:

| Tool | Purpose | Config location |
|------|---------|----------------|
| **Black** | Code formatting | `pyproject.toml` (`line-length = 115`) |
| **isort** | Import sorting | `pyproject.toml` (`profile = "black"`) |
| **autoflake** | Remove unused imports & variables | `.pre-commit-config.yaml` |
| **Flake8** | Linting and style | `.flake8` |
| **pyupgrade** | Modernize Python syntax | `.pre-commit-config.yaml` |
| **vulture** | Dead code detection | `pyproject.toml` (`paths = ["hq-util4", "whitelist.py"]`) |
| **Pre-commit hooks** | YAML/TOML validation, trailing whitespace, file size | `.pre-commit-config.yaml` |

- Use **Poetry** for all dependency and virtual environment management.
- **MyPy** is required for static type checking — add it to the pre-commit pipeline if not yet present.

---

## Temporary Artifacts

- Any temporary artifact created by Copilot (files, folders, or other working objects) must use the `_tmp` prefix.
- Create temporary artifacts only under the `/temp/` folder at the repository root.
- Treat temporary artifacts as Copilot working objects intended for short-term use, not long-term repository assets.
- Do not create temporary artifacts outside `/temp/` unless the user explicitly asks for a different location.

---

## Project Folder Structure

Follow this directory layout. `<repo_name>` is the repository name in `lowercase_with_underscores`:

```
.github/
.vscode/
database/
deploy/
    deployment_logs/
documentation/
temp/
hq-util4/
    <repo_name>/
        data/
            archive/
            test_data/
        programs/
            tests/
tests/
```

---

## Coding Standards Quick Reference

| Concern | Requirement |
|---------|------------|
| Type hints | Required on all parameters |
| Return types | Add when non-obvious or important for callers |
| Unit tests | Must pass (`poetry run pytest --cov`) before any commit |
| Security | Follow OWASP Top 10 best practices |
| API design | Follow RESTful conventions |
| Line length | 115 characters (Black-enforced) |
| Naming | `snake_case` / `PascalCase` / `ALL_CAPS` as appropriate |
