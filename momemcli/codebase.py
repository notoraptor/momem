"""Operations on the momem codebase (memorize, forget, show)."""

import shutil
from pathlib import Path

import click

from momemcli.config import ensure_tool_dir, get_codebase_dir
from momemcli.deps import find_dependents, rewrite_momem_imports, validate_dependencies


def memorize(source: str, dest: str | None = None, *, force: bool = False) -> Path:
    """Add a Python file to the momem codebase.

    Rewrites absolute momem.* imports to relative imports during the copy.

    Args:
        source: Path to the source file.
        dest: Relative path within the codebase. Required if source is outside
            the current working directory.
        force: Overwrite if the target already exists.

    Returns:
        The path where the file was stored in the codebase.
    """
    ensure_tool_dir()
    source_path = Path(source)

    if not source_path.exists():
        raise FileNotFoundError(f"Source file not found: {source}")

    if not source_path.is_file():
        raise ValueError(f"Source is not a file: {source}")

    if source_path.suffix != ".py":
        raise ValueError(f"Only Python files are supported: {source}")

    if dest is None:
        try:
            rel_dest = str(source_path.resolve().relative_to(Path.cwd()))
        except ValueError:
            raise ValueError(
                "A destination path is required when the source is outside the "
                "current directory. "
                "Usage: momem memorize <source> <dest>"
            )
    else:
        dest_path = Path(dest)
        if dest_path.is_absolute() or ".." in dest_path.parts:
            raise ValueError(
                "Destination must be a purely relative path without '.' or '..'. "
                f"Got: {dest}"
            )
        rel_dest = dest
    codebase_dir = get_codebase_dir()
    target = codebase_dir / rel_dest

    if target.exists() and not force:
        raise FileExistsError(
            f"File already exists in codebase: {rel_dest}. Use --force to overwrite."
        )

    target.parent.mkdir(parents=True, exist_ok=True)

    # Ensure __init__.py files in subdirectories within the codebase
    parts = Path(rel_dest).parent.parts
    current = codebase_dir
    for part in parts:
        current = current / part
        init = current / "__init__.py"
        if not init.exists():
            init.touch()

    # Read source, rewrite momem imports to relative, then write
    content = source_path.read_text(encoding="utf-8")
    content = rewrite_momem_imports(content, rel_dest)
    target.write_text(content, encoding="utf-8")
    # Preserve metadata
    shutil.copystat(source_path, target)

    # Warn about missing dependencies
    missing = validate_dependencies(target, codebase_dir, rel_dest)
    if missing:
        for m in missing:
            click.echo(f"Warning: dependency not found in codebase: {m}", err=True)

    return target


def forget(path: str, *, force: bool = False) -> None:
    """Remove a file from the momem codebase.

    Args:
        path: Relative path within the codebase.
        force: Remove even if other snippets depend on this file.
    """
    codebase_dir = get_codebase_dir()
    target = codebase_dir / path

    if not target.exists():
        raise FileNotFoundError(f"File not found in codebase: {path}")

    # Check if other snippets depend on this file
    dependents = find_dependents(path, codebase_dir)
    if dependents and not force:
        dep_list = ", ".join(dependents)
        raise ValueError(
            f"Cannot forget {path}: used by {dep_list}. Use --force to remove anyway."
        )

    if dependents:
        for d in dependents:
            click.echo(f"Warning: {d} depends on {path}", err=True)

    target.unlink()

    # Clean up parent directories that are empty or only contain __init__.py
    parent = target.parent
    while parent != codebase_dir:
        remaining = list(parent.iterdir())
        if not remaining:
            parent.rmdir()
            parent = parent.parent
        elif remaining == [parent / "__init__.py"]:
            (parent / "__init__.py").unlink()
            parent.rmdir()
            parent = parent.parent
        else:
            break


def show_memory() -> list[str]:
    """Return a sorted list of all files in the codebase (relative paths)."""
    codebase_dir = get_codebase_dir()
    if not codebase_dir.exists():
        return []
    return sorted(
        str(p.relative_to(codebase_dir))
        for p in codebase_dir.rglob("*.py")
        if p.is_file() and p.name != "__init__.py"
    )
