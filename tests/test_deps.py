"""Tests for momem.deps."""

from pathlib import Path

from momem.deps import find_momem_imports, resolve_dependencies, validate_dependencies


class TestFindMomemImports:
    def test_from_import(self, tmp_path):
        script = tmp_path / "a.py"
        script.write_text("from momem.utils.helpers import foo\n")
        assert find_momem_imports(script) == {"utils/helpers.py"}

    def test_import_statement(self, tmp_path):
        script = tmp_path / "a.py"
        script.write_text("import momem.tools.parser\n")
        assert find_momem_imports(script) == {"tools/parser.py"}

    def test_ignores_non_momem_imports(self, tmp_path):
        script = tmp_path / "a.py"
        script.write_text("import os\nfrom pathlib import Path\n")
        assert find_momem_imports(script) == set()

    def test_ignores_bare_momem_import(self, tmp_path):
        script = tmp_path / "a.py"
        script.write_text("import momem\n")
        assert find_momem_imports(script) == set()

    def test_multiple_imports(self, tmp_path):
        script = tmp_path / "a.py"
        script.write_text(
            "from momem.foo import bar\nimport momem.baz\nimport os\n"
        )
        assert find_momem_imports(script) == {"foo.py", "baz.py"}


class TestResolveDependencies:
    def test_no_deps(self, tmp_path):
        codebase = tmp_path / "codebase"
        codebase.mkdir()
        script = codebase / "main.py"
        script.write_text("x = 1\n")
        assert resolve_dependencies(Path("main.py"), codebase) == []

    def test_single_dep(self, tmp_path):
        codebase = tmp_path / "codebase"
        codebase.mkdir()
        (codebase / "helper.py").write_text("def h(): pass\n")
        (codebase / "main.py").write_text("from momem.helper import h\n")
        deps = resolve_dependencies(Path("main.py"), codebase)
        assert deps == ["helper.py"]

    def test_transitive_deps(self, tmp_path):
        codebase = tmp_path / "codebase"
        codebase.mkdir()
        (codebase / "base.py").write_text("x = 1\n")
        (codebase / "mid.py").write_text("from momem.base import x\n")
        (codebase / "top.py").write_text("from momem.mid import x\n")
        deps = resolve_dependencies(Path("top.py"), codebase)
        assert deps == ["base.py", "mid.py"]

    def test_cycle_detection(self, tmp_path):
        codebase = tmp_path / "codebase"
        codebase.mkdir()
        (codebase / "a.py").write_text("from momem.b import x\n")
        (codebase / "b.py").write_text("from momem.a import y\n")
        # Should not infinite loop
        deps = resolve_dependencies(Path("a.py"), codebase)
        assert set(deps) == {"a.py", "b.py"}

    def test_missing_dep_skipped(self, tmp_path):
        codebase = tmp_path / "codebase"
        codebase.mkdir()
        (codebase / "main.py").write_text("from momem.nonexistent import x\n")
        deps = resolve_dependencies(Path("main.py"), codebase)
        assert deps == []


class TestValidateDependencies:
    def test_all_present(self, tmp_path):
        codebase = tmp_path / "codebase"
        codebase.mkdir()
        (codebase / "helper.py").write_text("x = 1\n")
        script = tmp_path / "main.py"
        script.write_text("from momem.helper import x\n")
        assert validate_dependencies(script, codebase) == []

    def test_missing(self, tmp_path):
        codebase = tmp_path / "codebase"
        codebase.mkdir()
        script = tmp_path / "main.py"
        script.write_text("from momem.missing import x\n")
        assert validate_dependencies(script, codebase) == ["missing.py"]
