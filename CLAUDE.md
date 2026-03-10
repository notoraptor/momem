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

# Run tests with coverage
uv run pytest --cov=momemcli --cov-report=term-missing
```

## Architecture

The main package is in `momemcli/`.

### Core Concepts

- **Code repository (base de code)**: stored in `~/.momem/momem/` by default, configurable via `momem config --global --set codebase <path>` (path is used directly)
- **Global config**: `~/.momem/.momem.yaml`
- **Local project config**: `.momem.yaml` in project root, configurable via `momem config --local --set momemdir <path>`. Also stores install hashes for 3-way update comparison.
- **Installation target**: by default `PROJECT_DIR/PROJECT_DIR/momem/` — follows Python convention where directory name matches the main package name

### Path Management

When memorizing without a `dest` argument, the source path is resolved to an absolute path and then made relative to the current working directory. If the source is outside the CWD, a `dest` argument is required. The `dest` argument must be purely relative (no `..`, no absolute paths). `Path` normalizes `.` automatically.

### Dependency Resolution

Imports between snippets are detected via AST parsing (`deps.py`). Absolute `momem.*` imports are rewritten to relative imports at `memorize` time. Dependencies are resolved recursively at `install` time, with cycle detection. Both module files (`name.py`) and packages (`name/__init__.py`) are supported via `resolve_dep_path()`.

### `__init__.py` Management

`memorize` creates `__init__.py` files in codebase subdirectories. `install` creates them in the project install directory. `forget` and `uninstall` clean up directories that only contain `__init__.py`. `show_memory` and `show_local` exclude `__init__.py` from listings.

## Language

The README and docs are in French, but all code, docstrings, and comments must be in English.
