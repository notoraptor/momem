"""Tests for momem.codebase."""

from pathlib import Path

import pytest

from momemcli import codebase
from momemcli.config import get_codebase_dir


class TestMemorize:
    def test_memorize_relative(self, setup_env, sample_script):
        target = codebase.memorize(str(sample_script), "sample.py")
        assert target.exists()
        assert target.read_text() == sample_script.read_text()

    def test_memorize_with_dest(self, setup_env, sample_script):
        target = codebase.memorize(str(sample_script), "custom/path.py")
        codebase_dir = get_codebase_dir()
        assert target == codebase_dir / "custom" / "path.py"
        assert target.exists()

    def test_memorize_outside_cwd_requires_dest(self, setup_env, sample_script):
        abs_path = sample_script.resolve()
        with pytest.raises(ValueError, match="outside the current directory"):
            codebase.memorize(str(abs_path))

    def test_memorize_outside_cwd_with_dest(self, setup_env, sample_script):
        abs_path = sample_script.resolve()
        target = codebase.memorize(str(abs_path), "placed.py")
        assert target.exists()

    def test_memorize_dest_with_dotdot(self, setup_env, sample_script):
        with pytest.raises(ValueError, match="purely relative"):
            codebase.memorize(str(sample_script), "../evil.py")

    def test_memorize_dest_absolute(self, setup_env, sample_script):
        with pytest.raises(ValueError, match="purely relative"):
            codebase.memorize(str(sample_script), "/etc/evil.py")

    def test_memorize_conflict_no_force(self, setup_env, sample_script):
        codebase.memorize(str(sample_script), "conflict.py")
        with pytest.raises(FileExistsError, match="Use --force"):
            codebase.memorize(str(sample_script), "conflict.py")

    def test_memorize_conflict_with_force(self, setup_env, sample_script):
        codebase.memorize(str(sample_script), "conflict.py")
        target = codebase.memorize(str(sample_script), "conflict.py", force=True)
        assert target.exists()

    def test_memorize_nonexistent(self, setup_env):
        with pytest.raises(FileNotFoundError):
            codebase.memorize("/nonexistent/file.py", "dest.py")

    def test_memorize_non_python(self, setup_env, tmp_path):
        txt = tmp_path / "file.txt"
        txt.write_text("hello")
        with pytest.raises(ValueError, match="Only Python files"):
            codebase.memorize(str(txt))

    def test_memorize_not_a_file(self, setup_env, tmp_path):
        d = tmp_path / "adir"
        d.mkdir()
        with pytest.raises(ValueError, match="not a file"):
            codebase.memorize(str(d))

    def test_memorize_relative_outside_cwd_requires_dest(self, setup_env, tmp_path):
        # CWD is tmp_path/myproject, script is in tmp_path (parent)
        script = tmp_path / "outside.py"
        script.write_text("x = 1\n", encoding="utf-8")
        with pytest.raises(ValueError, match="outside the current directory"):
            codebase.memorize("../outside.py")

    def test_memorize_relative_outside_cwd_with_dest(self, setup_env, tmp_path):
        script = tmp_path / "outside.py"
        script.write_text("x = 1\n", encoding="utf-8")
        target = codebase.memorize("../outside.py", "outside.py")
        assert target.exists()

    def test_memorize_in_cwd_without_dest(self, setup_env):
        """Script in CWD is memorized using its relative path as dest."""
        cwd = Path.cwd()
        script = cwd / "local.py"
        script.write_text("x = 1\n", encoding="utf-8")
        target = codebase.memorize("local.py")
        assert target.exists()
        assert target == get_codebase_dir() / "local.py"

    def test_memorize_in_subdir_without_dest(self, setup_env):
        """Script in a subdirectory of CWD is memorized with subdir path."""
        cwd = Path.cwd()
        sub = cwd / "pkg"
        sub.mkdir()
        script = sub / "mod.py"
        script.write_text("x = 1\n", encoding="utf-8")
        target = codebase.memorize("pkg/mod.py")
        assert target.exists()
        assert target == get_codebase_dir() / "pkg" / "mod.py"

    def test_memorize_dotdot_within_cwd(self, setup_env):
        """Path with .. that still resolves inside CWD is accepted."""
        cwd = Path.cwd()
        sub = cwd / "a" / "b"
        sub.mkdir(parents=True)
        script = sub / "script.py"
        script.write_text("x = 1\n", encoding="utf-8")
        target = codebase.memorize("a/b/../b/script.py")
        assert target.exists()
        assert target == get_codebase_dir() / "a" / "b" / "script.py"

    def test_memorize_rewrites_imports(self, setup_env, tmp_path):
        script = tmp_path / "uses_momem.py"
        script.write_text("from momem.helper import x\nimport os\n", encoding="utf-8")
        target = codebase.memorize(str(script), "uses_momem.py")
        content = target.read_text(encoding="utf-8")
        assert "from .helper import x" in content
        assert "from momem." not in content
        assert "import os" in content

    def test_memorize_rewrites_imports_nested(self, setup_env, tmp_path):
        script = tmp_path / "deep.py"
        script.write_text("from momem.helper import x\n", encoding="utf-8")
        target = codebase.memorize(str(script), "sub/deep.py")
        content = target.read_text(encoding="utf-8")
        assert "from ..helper import x" in content

    def test_memorize_creates_init_files(self, setup_env, tmp_path):
        """Memorizing into a subdirectory creates __init__.py files."""
        script = tmp_path / "mod.py"
        script.write_text("x = 1\n", encoding="utf-8")
        codebase.memorize(str(script), "pkg/sub/mod.py")
        codebase_dir = get_codebase_dir()
        assert (codebase_dir / "pkg" / "__init__.py").exists()
        assert (codebase_dir / "pkg" / "sub" / "__init__.py").exists()

    def test_memorize_root_no_init(self, setup_env, tmp_path):
        """Memorizing at root level does not create __init__.py."""
        script = tmp_path / "mod.py"
        script.write_text("x = 1\n", encoding="utf-8")
        codebase.memorize(str(script), "mod.py")
        codebase_dir = get_codebase_dir()
        assert not (codebase_dir / "__init__.py").exists()


class TestMemorizeWarnings:
    def test_warns_missing_deps(self, setup_env, tmp_path):
        script = tmp_path / "needs_dep.py"
        script.write_text("from momem.nonexistent import x\n", encoding="utf-8")
        target = codebase.memorize(str(script), "needs_dep.py")
        assert target.exists()


class TestForget:
    def test_forget(self, setup_env, sample_script):
        codebase.memorize(str(sample_script), "to_forget.py")
        codebase.forget("to_forget.py")
        assert not (get_codebase_dir() / "to_forget.py").exists()

    def test_forget_cleans_empty_dirs(self, setup_env, sample_script):
        codebase.memorize(str(sample_script), "deep/nested/script.py")
        codebase.forget("deep/nested/script.py")
        assert not (get_codebase_dir() / "deep").exists()

    def test_forget_cleans_init_only_dirs(self, setup_env, sample_script):
        """Directories with only __init__.py are cleaned up on forget."""
        codebase.memorize(str(sample_script), "pkg/sub/script.py")
        codebase_dir = get_codebase_dir()
        assert (codebase_dir / "pkg" / "__init__.py").exists()
        codebase.forget("pkg/sub/script.py")
        assert not (codebase_dir / "pkg").exists()

    def test_forget_cleans_empty_dir_no_init(self, setup_env, sample_script):
        """Directories that are truly empty (no __init__.py) are also cleaned."""
        codebase_dir = get_codebase_dir()
        sub = codebase_dir / "bare"
        sub.mkdir(parents=True)
        script = sub / "script.py"
        script.write_text('def hello():\n    return "hello"\n', encoding="utf-8")
        # No __init__.py in "bare/" — forget should still clean up
        codebase.forget("bare/script.py")
        assert not (codebase_dir / "bare").exists()

    def test_forget_keeps_non_empty_parent(self, setup_env, sample_script):
        codebase.memorize(str(sample_script), "dir/a.py")
        codebase.memorize(str(sample_script), "dir/b.py", force=True)
        codebase.forget("dir/a.py")
        # dir/ should still exist because b.py is still there
        assert (get_codebase_dir() / "dir" / "b.py").exists()

    def test_forget_nonexistent(self, setup_env):
        with pytest.raises(FileNotFoundError):
            codebase.forget("nope.py")

    def test_forget_blocked_by_dependents(self, setup_env, tmp_path):
        helper = tmp_path / "helper.py"
        helper.write_text("x = 1\n", encoding="utf-8")
        codebase.memorize(str(helper), "helper.py")
        main = tmp_path / "main.py"
        main.write_text("from momem.helper import x\n", encoding="utf-8")
        codebase.memorize(str(main), "main.py")
        with pytest.raises(ValueError, match="used by"):
            codebase.forget("helper.py")

    def test_forget_force_with_dependents(self, setup_env, tmp_path):
        helper = tmp_path / "helper.py"
        helper.write_text("x = 1\n", encoding="utf-8")
        codebase.memorize(str(helper), "helper.py")
        main = tmp_path / "main.py"
        main.write_text("from momem.helper import x\n", encoding="utf-8")
        codebase.memorize(str(main), "main.py")
        codebase.forget("helper.py", force=True)
        assert not (get_codebase_dir() / "helper.py").exists()


class TestShowMemory:
    def test_empty(self, setup_env):
        assert codebase.show_memory() == []

    def test_with_files(self, setup_env, sample_script):
        codebase.memorize(str(sample_script), "a.py")
        codebase.memorize(str(sample_script), "b.py", force=True)
        files = codebase.show_memory()
        assert files == ["a.py", "b.py"]

    def test_excludes_init_files(self, setup_env, sample_script):
        """show_memory does not list __init__.py files."""
        codebase.memorize(str(sample_script), "pkg/mod.py")
        files = codebase.show_memory()
        assert files == ["pkg/mod.py"]

    def test_nonexistent_codebase(self, tmp_home):
        """show_memory returns [] when codebase dir doesn't exist."""
        assert codebase.show_memory() == []
