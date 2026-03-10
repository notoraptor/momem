"""Dependency parsing for momem snippets (detect momem.* imports via ast)."""

import ast
from pathlib import Path


def find_momem_imports(file_path: Path) -> set[str]:
    """Parse a Python file and return relative paths of momem.* dependencies.

    For example, 'from momem.utils.foo import bar' yields 'utils/foo.py'.
    """
    source = file_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(file_path))
    deps = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            parts = node.module.split(".")
            if parts[0] == "momem" and len(parts) > 1:
                rel_path = "/".join(parts[1:]) + ".py"
                deps.add(rel_path)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                parts = alias.name.split(".")
                if parts[0] == "momem" and len(parts) > 1:
                    rel_path = "/".join(parts[1:]) + ".py"
                    deps.add(rel_path)

    return deps


def resolve_dependencies(file_path: Path, codebase_dir: Path) -> list[str]:
    """Recursively resolve all momem.* dependencies for a file.

    Returns a list of relative paths (within the codebase) of all dependencies,
    in depth-first order. Detects cycles.
    """
    # file_path is relative to codebase_dir
    visited: set[str] = set()
    result: list[str] = []

    def _resolve(rel_path: str) -> None:
        if rel_path in visited:
            return
        visited.add(rel_path)
        full_path = codebase_dir / rel_path
        if not full_path.exists():
            return
        for dep in find_momem_imports(full_path):
            _resolve(dep)
        result.append(rel_path)

    source_full = codebase_dir / file_path
    for dep in find_momem_imports(source_full):
        _resolve(dep)

    return result


def validate_dependencies(file_path: Path, codebase_dir: Path) -> list[str]:
    """Check that all momem.* imports in a file exist in the codebase.

    Returns a list of missing dependency paths.
    """
    deps = find_momem_imports(file_path)
    missing = []
    for dep in sorted(deps):
        if not (codebase_dir / dep).exists():
            missing.append(dep)
    return missing
