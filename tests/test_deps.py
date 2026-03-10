"""Tests for momem.deps."""

from pathlib import Path

from momemcli.deps import (
    find_dependents,
    find_momem_imports,
    resolve_dep_path,
    resolve_dependencies,
    rewrite_momem_imports,
    validate_dependencies,
)


class TestResolveDepPath:
    def test_module_file(self, tmp_path):
        codebase = tmp_path / "codebase"
        codebase.mkdir()
        (codebase / "utils.py").write_text("x = 1\n")
        assert resolve_dep_path("utils.py", codebase) == "utils.py"

    def test_package_init(self, tmp_path):
        codebase = tmp_path / "codebase"
        codebase.mkdir()
        pkg = codebase / "utils"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("x = 1\n")
        assert resolve_dep_path("utils.py", codebase) == "utils/__init__.py"

    def test_module_preferred_over_package(self, tmp_path):
        """When both utils.py and utils/__init__.py exist, module wins."""
        codebase = tmp_path / "codebase"
        codebase.mkdir()
        (codebase / "utils.py").write_text("x = 1\n")
        pkg = codebase / "utils"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("y = 2\n")
        assert resolve_dep_path("utils.py", codebase) == "utils.py"

    def test_neither_exists(self, tmp_path):
        codebase = tmp_path / "codebase"
        codebase.mkdir()
        assert resolve_dep_path("utils.py", codebase) is None


class TestRewriteMomemImports:
    def test_from_import_root(self):
        source = "from momem.helper import x\n"
        result = rewrite_momem_imports(source, "main.py")
        assert result == "from .helper import x\n"

    def test_from_import_nested(self):
        source = "from momem.helper import x\n"
        result = rewrite_momem_imports(source, "sub/main.py")
        assert result == "from ..helper import x\n"

    def test_from_import_deep_nested(self):
        source = "from momem.helper import x\n"
        result = rewrite_momem_imports(source, "a/b/main.py")
        assert result == "from ...helper import x\n"

    def test_from_import_dotted_module(self):
        source = "from momem.utils.helpers import foo\n"
        result = rewrite_momem_imports(source, "main.py")
        assert result == "from .utils.helpers import foo\n"

    def test_import_single(self):
        source = "import momem.helper\n"
        result = rewrite_momem_imports(source, "main.py")
        assert result == "from . import helper\n"

    def test_import_dotted(self):
        source = "import momem.utils.deep\n"
        result = rewrite_momem_imports(source, "main.py")
        assert result == "from .utils import deep\n"

    def test_non_momem_unchanged(self):
        source = "import os\nfrom pathlib import Path\n"
        result = rewrite_momem_imports(source, "main.py")
        assert result == source

    def test_mixed_imports(self):
        source = "import os\nfrom momem.helper import x\nx = 1\n"
        result = rewrite_momem_imports(source, "main.py")
        assert result == "import os\nfrom .helper import x\nx = 1\n"


class TestFindMomemImports:
    def test_absolute_from_import(self, tmp_path):
        script = tmp_path / "a.py"
        script.write_text("from momem.utils.helpers import foo\n")
        assert find_momem_imports(script) == {"utils/helpers.py"}

    def test_absolute_import_statement(self, tmp_path):
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
        script.write_text("from momem.foo import bar\nimport momem.baz\nimport os\n")
        assert find_momem_imports(script) == {"foo.py", "baz.py"}

    def test_relative_from_import_root(self, tmp_path):
        script = tmp_path / "main.py"
        script.write_text("from .helper import x\n")
        assert find_momem_imports(script, "main.py") == {"helper.py"}

    def test_relative_from_import_nested(self, tmp_path):
        script = tmp_path / "main.py"
        script.write_text("from ..helper import x\n")
        assert find_momem_imports(script, "sub/main.py") == {"helper.py"}

    def test_relative_bare_import(self, tmp_path):
        script = tmp_path / "main.py"
        script.write_text("from . import helper\n")
        assert find_momem_imports(script, "main.py") == {"helper.py"}

    def test_relative_bare_import_nested(self, tmp_path):
        script = tmp_path / "main.py"
        script.write_text("from . import helper\n")
        assert find_momem_imports(script, "sub/main.py") == {"sub/helper.py"}

    def test_relative_ignored_without_rel_path(self, tmp_path):
        script = tmp_path / "main.py"
        script.write_text("from .helper import x\n")
        assert find_momem_imports(script) == set()


class TestResolveDependencies:
    def test_no_deps(self, tmp_path):
        codebase = tmp_path / "codebase"
        codebase.mkdir()
        script = codebase / "main.py"
        script.write_text("x = 1\n")
        assert resolve_dependencies(Path("main.py"), codebase) == []

    def test_single_dep_relative(self, tmp_path):
        codebase = tmp_path / "codebase"
        codebase.mkdir()
        (codebase / "helper.py").write_text("def h(): pass\n")
        (codebase / "main.py").write_text("from .helper import h\n")
        deps = resolve_dependencies(Path("main.py"), codebase)
        assert deps == ["helper.py"]

    def test_transitive_deps_relative(self, tmp_path):
        codebase = tmp_path / "codebase"
        codebase.mkdir()
        (codebase / "base.py").write_text("x = 1\n")
        (codebase / "mid.py").write_text("from .base import x\n")
        (codebase / "top.py").write_text("from .mid import x\n")
        deps = resolve_dependencies(Path("top.py"), codebase)
        assert deps == ["base.py", "mid.py"]

    def test_cycle_detection(self, tmp_path):
        codebase = tmp_path / "codebase"
        codebase.mkdir()
        (codebase / "a.py").write_text("from .b import x\n")
        (codebase / "b.py").write_text("from .a import y\n")
        deps = resolve_dependencies(Path("a.py"), codebase)
        assert set(deps) == {"a.py", "b.py"}

    def test_missing_dep_skipped(self, tmp_path):
        codebase = tmp_path / "codebase"
        codebase.mkdir()
        (codebase / "main.py").write_text("from .nonexistent import x\n")
        deps = resolve_dependencies(Path("main.py"), codebase)
        assert deps == []

    def test_legacy_absolute_imports(self, tmp_path):
        codebase = tmp_path / "codebase"
        codebase.mkdir()
        (codebase / "helper.py").write_text("def h(): pass\n")
        (codebase / "main.py").write_text("from momem.helper import h\n")
        deps = resolve_dependencies(Path("main.py"), codebase)
        assert deps == ["helper.py"]

    def test_package_dep(self, tmp_path):
        """from .utils import x resolves to utils/__init__.py when it's a package."""
        codebase = tmp_path / "codebase"
        codebase.mkdir()
        pkg = codebase / "utils"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("x = 1\n")
        (codebase / "main.py").write_text("from .utils import x\n")
        deps = resolve_dependencies(Path("main.py"), codebase)
        assert deps == ["utils/__init__.py"]

    def test_transitive_dep_missing_in_chain(self, tmp_path):
        """A resolved dep whose file was deleted is skipped in recursion."""
        codebase = tmp_path / "codebase"
        codebase.mkdir()
        (codebase / "mid.py").write_text("from .gone import x\n")
        (codebase / "top.py").write_text("from .mid import x\n")
        # gone.py does not exist — mid depends on it but it's missing
        deps = resolve_dependencies(Path("top.py"), codebase)
        assert deps == ["mid.py"]


class TestValidateDependencies:
    def test_all_present(self, tmp_path):
        codebase = tmp_path / "codebase"
        codebase.mkdir()
        (codebase / "helper.py").write_text("x = 1\n")
        script = tmp_path / "main.py"
        script.write_text("from .helper import x\n")
        assert validate_dependencies(script, codebase, "main.py") == []

    def test_missing(self, tmp_path):
        codebase = tmp_path / "codebase"
        codebase.mkdir()
        script = tmp_path / "main.py"
        script.write_text("from .missing import x\n")
        assert validate_dependencies(script, codebase, "main.py") == ["missing.py"]

    def test_package_present(self, tmp_path):
        codebase = tmp_path / "codebase"
        codebase.mkdir()
        pkg = codebase / "utils"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("x = 1\n")
        script = tmp_path / "main.py"
        script.write_text("from .utils import x\n")
        assert validate_dependencies(script, codebase, "main.py") == []


class TestFindDependents:
    def test_no_dependents(self, tmp_path):
        codebase = tmp_path / "codebase"
        codebase.mkdir()
        (codebase / "a.py").write_text("x = 1\n")
        (codebase / "b.py").write_text("y = 2\n")
        assert find_dependents("a.py", codebase) == []

    def test_has_dependents(self, tmp_path):
        codebase = tmp_path / "codebase"
        codebase.mkdir()
        (codebase / "helper.py").write_text("x = 1\n")
        (codebase / "main.py").write_text("from .helper import x\n")
        assert find_dependents("helper.py", codebase) == ["main.py"]

    def test_multiple_dependents(self, tmp_path):
        codebase = tmp_path / "codebase"
        codebase.mkdir()
        (codebase / "helper.py").write_text("x = 1\n")
        (codebase / "a.py").write_text("from .helper import x\n")
        (codebase / "b.py").write_text("from .helper import x\n")
        assert find_dependents("helper.py", codebase) == ["a.py", "b.py"]

    def test_ignores_init_files(self, tmp_path):
        codebase = tmp_path / "codebase"
        codebase.mkdir()
        (codebase / "helper.py").write_text("x = 1\n")
        (codebase / "__init__.py").write_text("from .helper import x\n")
        assert find_dependents("helper.py", codebase) == []

    def test_package_dependents(self, tmp_path):
        """find_dependents finds files that depend on a package __init__.py."""
        codebase = tmp_path / "codebase"
        codebase.mkdir()
        pkg = codebase / "utils"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("x = 1\n")
        (codebase / "main.py").write_text("from .utils import x\n")
        assert find_dependents("utils/__init__.py", codebase) == ["main.py"]
