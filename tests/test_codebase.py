"""Tests for momem.codebase."""

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

    def test_memorize_absolute_requires_dest(self, setup_env, sample_script):
        abs_path = sample_script.resolve()
        with pytest.raises(ValueError, match="relative destination path is required"):
            codebase.memorize(str(abs_path))

    def test_memorize_absolute_with_dest(self, setup_env, sample_script):
        abs_path = sample_script.resolve()
        target = codebase.memorize(str(abs_path), "placed.py")
        assert target.exists()

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

    def test_nonexistent_codebase(self, tmp_home):
        """show_memory returns [] when codebase dir doesn't exist."""
        assert codebase.show_memory() == []
