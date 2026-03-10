# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**momem** is a CLI tool for managing reusable Python code snippets across independent projects. It maintains a local code repository (`~/.momem/`) and allows installing/updating snippets into projects automatically.

Key commands: `memorize`, `forget`, `show`, `install`, `uninstall`, `update`, `diff`, `config`.

## Tech Stack

- Python 3.13+
- UV for package/dependency management
- click (CLI framework), pyyaml (config files)

## Development Commands

```bash
# Install dependencies
uv sync

# Run the tool
uv run momem

# Run tests
uv run pytest

# Run a single test file or test
uv run pytest tests/test_deps.py
uv run pytest tests/test_project.py::TestUpdate::test_update_codebase_changed -v

# Run tests with coverage
uv run pytest --cov=momemcli --cov-report=term-missing

# Lint and format
uv run ruff check momemcli/ tests/
uv run ruff format momemcli/ tests/
```

## Architecture

The main package is in `momemcli/`. Layered architecture: `cli.py` (Click commands) → core modules (`codebase.py`, `project.py`, `config.py`, `deps.py`) → file system. The CLI catches exceptions from core modules and wraps them in `ClickException`.

### Core Concepts

- **Code repository (base de code)**: stored in `~/.momem/momem/` by default, configurable via `momem config --global --set codebase <path>` (path is used directly)
- **Global config**: `~/.momem/.momem.yaml`
- **Local project config**: `.momem.yaml` in project root, configurable via `momem config --local --set momemdir <path>`. Also stores install hashes for 3-way update comparison.
- **Installation target**: by default `PROJECT_DIR/PROJECT_DIR/momem/` — follows Python convention where directory name matches the main package name

### Path Management

When memorizing without a `dest` argument, the source path is resolved to an absolute path and then made relative to the current working directory. If the source is outside the CWD, a `dest` argument is required. The `dest` argument must be purely relative (no `..`, no absolute paths). `Path` normalizes `.` automatically.

### Dependency Resolution

Imports between snippets are detected via AST parsing (`deps.py`). Absolute `momem.*` imports are rewritten to relative imports at `memorize` time (regex-based, dot count determined by file depth). Dependencies are resolved recursively at `install` time, with cycle detection via visited set. Both module files (`name.py`) and packages (`name/__init__.py`) are supported via `resolve_dep_path()`.

### 3-Way Update Logic

`project.update()` compares three SHA-256 hashes per installed file: the original hash (stored at install time in `.momem.yaml`), the current local version, and the current codebase version. Only codebase-changed files are auto-updated; local-only changes are preserved; both-changed files are flagged as conflicts (unless `--force`).

### `__init__.py` Management

`memorize` creates `__init__.py` files in codebase subdirectories. `install` creates them in the project install directory. `forget` and `uninstall` clean up directories that only contain `__init__.py`. `show_memory` and `show_local` exclude `__init__.py` from listings.

## Testing

Tests use `tmp_home` and `tmp_project` fixtures (`conftest.py`) that monkeypatch `config.TOOL_DIR` and related constants, isolating all tests from the real `~/.momem/`. CLI tests use Click's `CliRunner().invoke()`. The `setup_env` fixture combines both home and project isolation.

## Language

The README and docs are in French, but all code, docstrings, and comments must be in English.
