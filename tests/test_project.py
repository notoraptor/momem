"""Tests for momem.project."""

import pytest

from momem import codebase, project
from momem.config import get_codebase_dir, resolve_install_dir


class TestInstall:
    def test_install_simple(self, setup_env, sample_script):
        codebase.memorize(str(sample_script), "simple.py")
        installed = project.install("simple.py")
        assert installed == ["simple.py"]
        install_dir = resolve_install_dir()
        assert (install_dir / "simple.py").exists()
        assert (install_dir / "__init__.py").exists()

    def test_install_with_deps(self, setup_env, sample_script_with_dep):
        main_script, dep_script = sample_script_with_dep
        codebase.memorize(str(dep_script), "helper.py")
        codebase.memorize(str(main_script), "main.py")
        installed = project.install("main.py")
        assert "helper.py" in installed
        assert "main.py" in installed
        install_dir = resolve_install_dir()
        assert (install_dir / "helper.py").exists()
        assert (install_dir / "main.py").exists()

    def test_install_conflict_no_force(self, setup_env, sample_script):
        codebase.memorize(str(sample_script), "dup.py")
        project.install("dup.py")
        with pytest.raises(FileExistsError, match="Use --force"):
            project.install("dup.py")

    def test_install_conflict_with_force(self, setup_env, sample_script):
        codebase.memorize(str(sample_script), "dup.py")
        project.install("dup.py")
        installed = project.install("dup.py", force=True)
        assert installed == ["dup.py"]

    def test_install_nonexistent(self, setup_env):
        with pytest.raises(FileNotFoundError):
            project.install("nope.py")

    def test_install_creates_init_files(self, setup_env, sample_script):
        codebase.memorize(str(sample_script), "sub/deep/script.py")
        project.install("sub/deep/script.py")
        install_dir = resolve_install_dir()
        assert (install_dir / "__init__.py").exists()
        assert (install_dir / "sub" / "__init__.py").exists()
        assert (install_dir / "sub" / "deep" / "__init__.py").exists()


class TestUninstall:
    def test_uninstall_single(self, setup_env, sample_script):
        codebase.memorize(str(sample_script), "rem.py")
        project.install("rem.py")
        removed = project.uninstall("rem.py")
        assert removed == ["rem.py"]
        assert not (resolve_install_dir() / "rem.py").exists()

    def test_uninstall_all(self, setup_env, sample_script):
        codebase.memorize(str(sample_script), "a.py")
        codebase.memorize(str(sample_script), "b.py", force=True)
        project.install("a.py")
        project.install("b.py")
        removed = project.uninstall(all_=True)
        assert set(removed) == {"a.py", "b.py"}
        assert not resolve_install_dir().exists()

    def test_uninstall_nonexistent(self, setup_env, sample_script):
        codebase.memorize(str(sample_script), "x.py")
        project.install("x.py")
        with pytest.raises(FileNotFoundError):
            project.uninstall("nope.py")

    def test_uninstall_no_install_dir(self, setup_env):
        with pytest.raises(FileNotFoundError):
            project.uninstall("anything.py")

    def test_uninstall_no_path_no_all(self, setup_env, sample_script):
        codebase.memorize(str(sample_script), "x.py")
        project.install("x.py")
        with pytest.raises(ValueError, match="Specify a path"):
            project.uninstall()

    def test_uninstall_cleans_nested_dirs(self, setup_env, sample_script):
        codebase.memorize(str(sample_script), "sub/deep/nested.py")
        project.install("sub/deep/nested.py")
        project.uninstall("sub/deep/nested.py")
        install_dir = resolve_install_dir()
        # Nested dirs should be cleaned up
        assert not (install_dir / "sub" / "deep").exists()
        assert not (install_dir / "sub").exists()

    def test_uninstall_keeps_non_empty_parent(self, setup_env, sample_script):
        codebase.memorize(str(sample_script), "pkg/a.py")
        codebase.memorize(str(sample_script), "pkg/b.py", force=True)
        project.install("pkg/a.py")
        project.install("pkg/b.py")
        project.uninstall("pkg/a.py")
        install_dir = resolve_install_dir()
        # pkg/ should still exist because b.py is there
        assert (install_dir / "pkg" / "b.py").exists()


class TestUpdate:
    def test_update_no_changes(self, setup_env, sample_script):
        codebase.memorize(str(sample_script), "upd.py")
        project.install("upd.py")
        result = project.update()
        assert result["updated"] == []
        assert result["conflicts"] == []

    def test_update_with_changes_force(self, setup_env, sample_script):
        codebase.memorize(str(sample_script), "upd.py")
        project.install("upd.py")
        # Modify in codebase
        cb_file = get_codebase_dir() / "upd.py"
        cb_file.write_text("def hello():\n    return 'updated'\n")
        result = project.update(force=True)
        assert result["updated"] == ["upd.py"]

    def test_update_conflict_without_force(self, setup_env, sample_script):
        codebase.memorize(str(sample_script), "upd.py")
        project.install("upd.py")
        # Modify in codebase
        cb_file = get_codebase_dir() / "upd.py"
        cb_file.write_text("def hello():\n    return 'updated'\n")
        result = project.update()
        assert result["conflicts"] == ["upd.py"]
        assert result["updated"] == []

    def test_update_detects_new_deps(self, setup_env, sample_script):
        codebase.memorize(str(sample_script), "base.py")
        project.install("base.py")
        # Now add a dependency in codebase and update base.py to import it
        helper = get_codebase_dir() / "helper.py"
        helper.write_text("x = 1\n")
        cb_file = get_codebase_dir() / "base.py"
        cb_file.write_text("from momem.helper import x\n")
        result = project.update(force=True)
        assert "helper.py" in result["new_deps"]

    def test_update_detects_obsolete(self, setup_env, sample_script):
        codebase.memorize(str(sample_script), "old.py")
        project.install("old.py")
        # Remove from codebase
        (get_codebase_dir() / "old.py").unlink()
        result = project.update()
        assert "old.py" in result["obsolete_deps"]

    def test_update_no_install_dir(self, setup_env):
        with pytest.raises(FileNotFoundError):
            project.update()


class TestShowLocal:
    def test_empty(self, setup_env):
        assert project.show_local() == []

    def test_with_installed(self, setup_env, sample_script):
        codebase.memorize(str(sample_script), "vis.py")
        project.install("vis.py")
        assert project.show_local() == ["vis.py"]
