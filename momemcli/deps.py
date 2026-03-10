"""Dependency parsing for momem snippets (detect momem.* imports via ast)."""

import ast
import re
from pathlib import Path


def rewrite_momem_imports(source: str, file_rel_path: str) -> str:
    """Rewrite absolute momem.* imports to relative imports.

    The number of dots is computed from the file's depth in the codebase.
    A root-level file gets 1 dot, a file one directory deep gets 2 dots, etc.
    """
    depth = len(Path(file_rel_path).parent.parts)
    dots = "." * (depth + 1)

    # from momem.xxx import yyy -> from <dots>xxx import yyy
    result = re.sub(
        r"^(\s*)from momem\.", rf"\1from {dots}", source, flags=re.MULTILINE
    )

    # import momem.xxx -> from <dots> import xxx
    # import momem.a.b -> from <dots>a import b
    def _rewrite_import(m: re.Match) -> str:
        indent = m.group(1)
        module_path = m.group(2)
        parts = module_path.split(".")
        if len(parts) == 1:
            return f"{indent}from {dots} import {parts[0]}"
        return f"{indent}from {dots}{'.'.join(parts[:-1])} import {parts[-1]}"

    result = re.sub(
        r"^(\s*)import momem\.([\w.]+)", _rewrite_import, result, flags=re.MULTILINE
    )
    return result


def find_momem_imports(file_path: Path, file_rel_path: str | None = None) -> set[str]:
    """Parse a Python file and return codebase-relative paths of dependencies.

    Detects both absolute momem.* imports (legacy) and relative imports.
    For relative imports, file_rel_path is required to resolve the target.
    """
    source = file_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(file_path))
    deps: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.level == 0 and node.module:
                # Absolute import: from momem.xxx import yyy
                parts = node.module.split(".")
                if parts[0] == "momem" and len(parts) > 1:
                    deps.add("/".join(parts[1:]) + ".py")
            elif node.level > 0 and file_rel_path is not None:
                # Relative import
                file_dir = Path(file_rel_path).parent
                base = file_dir
                for _ in range(node.level - 1):
                    base = base.parent
                if node.module:
                    # from .xxx.yyy import zzz
                    dep = base / node.module.replace(".", "/")
                    deps.add(str(dep) + ".py")
                else:
                    # from . import xxx, yyy
                    for alias in node.names:
                        dep = base / alias.name
                        deps.add(str(dep) + ".py")
        elif isinstance(node, ast.Import):
            for alias in node.names:
                parts = alias.name.split(".")
                if parts[0] == "momem" and len(parts) > 1:
                    deps.add("/".join(parts[1:]) + ".py")

    return deps


def resolve_dependencies(file_path: Path, codebase_dir: Path) -> list[str]:
    """Recursively resolve all dependencies for a file.

    Returns a list of relative paths (within the codebase) of all dependencies,
    in depth-first order. Detects cycles.
    """
    visited: set[str] = set()
    result: list[str] = []

    def _resolve(rel_path: str) -> None:
        if rel_path in visited:
            return
        visited.add(rel_path)
        full_path = codebase_dir / rel_path
        if not full_path.exists():
            return
        for dep in find_momem_imports(full_path, rel_path):
            _resolve(dep)
        result.append(rel_path)

    source_rel = str(file_path)
    source_full = codebase_dir / source_rel
    for dep in find_momem_imports(source_full, source_rel):
        _resolve(dep)

    return result


def validate_dependencies(
    file_path: Path, codebase_dir: Path, file_rel_path: str | None = None
) -> list[str]:
    """Check that all imports in a file exist in the codebase.

    Returns a list of missing dependency paths.
    """
    deps = find_momem_imports(file_path, file_rel_path)
    missing = []
    for dep in sorted(deps):
        if not (codebase_dir / dep).exists():
            missing.append(dep)
    return missing


def find_dependents(target_path: str, codebase_dir: Path) -> list[str]:
    """Find all files in the codebase that depend on target_path."""
    dependents = []
    for py_file in codebase_dir.rglob("*.py"):
        if py_file.name == "__init__.py":
            continue
        rel_path = str(py_file.relative_to(codebase_dir))
        if rel_path == target_path:
            continue
        imports = find_momem_imports(py_file, rel_path)
        if target_path in imports:
            dependents.append(rel_path)
    return sorted(dependents)
