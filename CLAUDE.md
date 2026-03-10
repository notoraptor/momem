# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**momem** is a CLI tool for managing reusable Python code snippets across independent projects. It maintains a local code repository (`~/.momem/`) and allows installing/updating snippets into projects automatically.

Key commands the tool provides: `memorize`, `forget`, `show`, `install`, `uninstall`, `update`, `config`.

## Tech Stack

- Python 3.13+
- UV for package/dependency management
- No external dependencies yet

## Development Commands

```bash
# Install dependencies
uv sync

# Run the tool (once entry points are defined)
uv run momem

# Run tests (once tests exist)
uv run pytest
```

## Architecture

The project is in early initialization stage. The main package is in `momem/`.

### Core Concepts

- **Code repository (base de code)**: stored in `~/.momem/momem/` by default, configurable via `momem config --global --set codebase <path>`
- **Global config**: `~/.momem/.momem.yaml`
- **Local project config**: `.momem.yaml` in project root, configurable via `momem config --local --set momemdir <path>`
- **Installation target**: by default `PROJECT_DIR/PROJECT_DIR/momem/` — follows Python convention where directory name matches the main package name

### Path Management

When memorizing, file paths are reproduced in the code repository. A custom path can be specified as a second argument to `memorize`. That custom path is then the reference for `install`/`uninstall`.

## Language

The project documentation (README) is written in French. Follow the same language conventions for user-facing strings.
