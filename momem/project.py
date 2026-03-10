"""Operations on the local project (install, uninstall, update, show)."""

import shutil
from pathlib import Path

from momem.config import get_codebase_dir, resolve_install_dir
from momem.deps import resolve_dependencies


def _ensure_init_files(install_dir: Path, rel_path: str) -> None:
    """Ensure __init__.py files exist along the directory chain."""
    # Ensure __init__.py in the momem root
    init_file = install_dir / "__init__.py"
    if not init_file.exists():
        init_file.parent.mkdir(parents=True, exist_ok=True)
        init_file.touch()

    # Ensure __init__.py in each subdirectory leading to the file
    parts = Path(rel_path).parent.parts
    current = install_dir
    for part in parts:
        current = current / part
        current.mkdir(parents=True, exist_ok=True)
        init = current / "__init__.py"
        if not init.exists():
            init.touch()


def _clean_empty_dirs(path: Path, stop_at: Path) -> None:
    """Remove empty parent directories up to stop_at (exclusive)."""
    parent = path.parent
    while parent != stop_at and parent != stop_at.parent:
        if parent.exists() and not any(
            p for p in parent.iterdir() if p.name != "__init__.py"
        ):
            # Only __init__.py or empty — remove
            init = parent / "__init__.py"
            if init.exists():
                init.unlink()
            if not any(parent.iterdir()):
                parent.rmdir()
            parent = parent.parent
        else:
            break


def install(path: str, *, force: bool = False) -> list[str]:
    """Install a snippet and its dependencies from the codebase into the project.

    Args:
        path: Relative path within the codebase.
        force: Overwrite existing files.

    Returns:
        List of installed file paths (relative to install dir).
    """
    codebase_dir = get_codebase_dir()
    source = codebase_dir / path

    if not source.exists():
        raise FileNotFoundError(f"File not found in codebase: {path}")

    install_dir = resolve_install_dir()

    # Resolve dependencies (does not include the file itself)
    deps = resolve_dependencies(Path(path), codebase_dir)
    all_files = deps + [path]

    installed = []
    for rel_path in all_files:
        src = codebase_dir / rel_path
        dst = install_dir / rel_path

        if dst.exists() and not force:
            raise FileExistsError(
                f"File already exists locally: {rel_path}. Use --force to overwrite."
            )

        _ensure_init_files(install_dir, rel_path)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        installed.append(rel_path)

    return installed


def uninstall(path: str | None = None, *, all_: bool = False) -> list[str]:
    """Remove installed snippet(s) from the local project.

    Args:
        path: Relative path to uninstall. Ignored if all_ is True.
        all_: If True, remove all installed snippets.

    Returns:
        List of removed file paths.
    """
    install_dir = resolve_install_dir()

    if not install_dir.exists():
        raise FileNotFoundError("No momem install directory found in this project.")

    if all_:
        removed = []
        for f in install_dir.rglob("*.py"):
            if f.name == "__init__.py":
                continue
            removed.append(str(f.relative_to(install_dir)))
            f.unlink()

        # Clean up the entire directory tree
        shutil.rmtree(install_dir)
        return sorted(removed)

    if path is None:
        raise ValueError("Specify a path or use --all.")

    target = install_dir / path
    if not target.exists():
        raise FileNotFoundError(f"File not installed locally: {path}")

    target.unlink()
    _clean_empty_dirs(target, install_dir)

    return [path]


def update(*, force: bool = False) -> dict[str, list[str]]:
    """Update all locally installed snippets from the codebase.

    Returns:
        A dict with keys 'updated', 'conflicts', 'new_deps', 'obsolete_deps'.
    """
    install_dir = resolve_install_dir()
    codebase_dir = get_codebase_dir()

    if not install_dir.exists():
        raise FileNotFoundError("No momem install directory found in this project.")

    result: dict[str, list[str]] = {
        "updated": [],
        "conflicts": [],
        "new_deps": [],
        "obsolete_deps": [],
    }

    # Collect all installed snippet files (excluding __init__.py)
    installed_files = sorted(
        str(p.relative_to(install_dir))
        for p in install_dir.rglob("*.py")
        if p.is_file() and p.name != "__init__.py"
    )

    for rel_path in installed_files:
        src = codebase_dir / rel_path
        dst = install_dir / rel_path

        if not src.exists():
            result["obsolete_deps"].append(rel_path)
            continue

        src_content = src.read_text(encoding="utf-8")
        dst_content = dst.read_text(encoding="utf-8")

        if src_content != dst_content:
            if force:
                shutil.copy2(src, dst)
                result["updated"].append(rel_path)
            else:
                result["conflicts"].append(rel_path)

    # Check for new dependencies
    all_needed: set[str] = set()
    for rel_path in installed_files:
        src = codebase_dir / rel_path
        if src.exists():
            deps = resolve_dependencies(Path(rel_path), codebase_dir)
            all_needed.update(deps)

    installed_set = set(installed_files)
    for dep in sorted(all_needed - installed_set):
        src = codebase_dir / dep
        dst = install_dir / dep
        if src.exists():
            _ensure_init_files(install_dir, dep)
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            result["new_deps"].append(dep)

    return result


def show_local() -> list[str]:
    """Return a sorted list of all installed snippets in the local project."""
    install_dir = resolve_install_dir()
    if not install_dir.exists():
        return []
    return sorted(
        str(p.relative_to(install_dir))
        for p in install_dir.rglob("*.py")
        if p.is_file() and p.name != "__init__.py"
    )
