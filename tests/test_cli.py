"""Integration tests for the momem CLI."""

import subprocess
import sys

import pytest
from click.testing import CliRunner

from momemcli.cli import main


class TestMainModule:
    def test_python_m_momem(self):
        result = subprocess.run(
            [sys.executable, "-m", "momemcli", "--help"], capture_output=True, text=True
        )
        assert result.returncode == 0
        assert "Usage" in result.stdout


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def cli_env(setup_env, runner):
    """Provide runner + environment."""
    return runner, setup_env


class TestCLIMemorize:
    def test_memorize(self, cli_env, sample_script):
        runner, _ = cli_env
        result = runner.invoke(main, ["memorize", str(sample_script), "test.py"])
        assert result.exit_code == 0
        assert "Memorized" in result.output

    def test_memorize_conflict(self, cli_env, sample_script):
        runner, _ = cli_env
        runner.invoke(main, ["memorize", str(sample_script), "test.py"])
        result = runner.invoke(main, ["memorize", str(sample_script), "test.py"])
        assert result.exit_code != 0
        assert "already exists" in result.output

    def test_memorize_force(self, cli_env, sample_script):
        runner, _ = cli_env
        runner.invoke(main, ["memorize", str(sample_script), "test.py"])
        result = runner.invoke(
            main, ["memorize", str(sample_script), "test.py", "--force"]
        )
        assert result.exit_code == 0


class TestCLIForget:
    def test_forget(self, cli_env, sample_script):
        runner, _ = cli_env
        runner.invoke(main, ["memorize", str(sample_script), "f.py"])
        result = runner.invoke(main, ["forget", "f.py"])
        assert result.exit_code == 0
        assert "Forgotten" in result.output

    def test_forget_nonexistent(self, cli_env):
        runner, _ = cli_env
        result = runner.invoke(main, ["forget", "nope.py"])
        assert result.exit_code != 0

    def test_forget_blocked_by_dependents(self, cli_env, tmp_path):
        runner, _ = cli_env
        helper = tmp_path / "helper.py"
        helper.write_text("x = 1\n", encoding="utf-8")
        runner.invoke(main, ["memorize", str(helper), "helper.py"])
        main_script = tmp_path / "main.py"
        main_script.write_text("from momem.helper import x\n", encoding="utf-8")
        runner.invoke(main, ["memorize", str(main_script), "main.py"])
        result = runner.invoke(main, ["forget", "helper.py"])
        assert result.exit_code != 0
        assert "used by" in result.output

    def test_forget_force_with_dependents(self, cli_env, tmp_path):
        runner, _ = cli_env
        helper = tmp_path / "helper.py"
        helper.write_text("x = 1\n", encoding="utf-8")
        runner.invoke(main, ["memorize", str(helper), "helper.py"])
        main_script = tmp_path / "main.py"
        main_script.write_text("from momem.helper import x\n", encoding="utf-8")
        runner.invoke(main, ["memorize", str(main_script), "main.py"])
        result = runner.invoke(main, ["forget", "helper.py", "--force"])
        assert result.exit_code == 0
        assert "Forgotten" in result.output


class TestCLIInstallUninstall:
    def test_install_and_uninstall(self, cli_env, sample_script):
        runner, _ = cli_env
        runner.invoke(main, ["memorize", str(sample_script), "s.py"])
        result = runner.invoke(main, ["install", "s.py"])
        assert result.exit_code == 0
        assert "Installed" in result.output

        result = runner.invoke(main, ["uninstall", "s.py"])
        assert result.exit_code == 0
        assert "Uninstalled" in result.output

    def test_uninstall_all(self, cli_env, sample_script):
        runner, _ = cli_env
        runner.invoke(main, ["memorize", str(sample_script), "a.py"])
        runner.invoke(main, ["memorize", str(sample_script), "b.py"])
        runner.invoke(main, ["install", "a.py"])
        runner.invoke(main, ["install", "b.py"])
        result = runner.invoke(main, ["uninstall", "--all"])
        assert result.exit_code == 0


class TestCLIInstallError:
    def test_install_nonexistent(self, cli_env):
        runner, _ = cli_env
        result = runner.invoke(main, ["install", "nope.py"])
        assert result.exit_code != 0

    def test_uninstall_error(self, cli_env):
        runner, _ = cli_env
        result = runner.invoke(main, ["uninstall", "nope.py"])
        assert result.exit_code != 0


class TestCLIUpdate:
    def test_update_up_to_date(self, cli_env, sample_script):
        runner, _ = cli_env
        runner.invoke(main, ["memorize", str(sample_script), "u.py"])
        runner.invoke(main, ["install", "u.py"])
        result = runner.invoke(main, ["update"])
        assert result.exit_code == 0
        assert "up to date" in result.output

    def test_update_no_install_dir(self, cli_env):
        runner, _ = cli_env
        result = runner.invoke(main, ["update"])
        assert result.exit_code != 0

    def test_update_shows_all_categories(self, cli_env, sample_script):
        runner, _ = cli_env
        from momemcli.config import get_codebase_dir

        runner.invoke(main, ["memorize", str(sample_script), "up.py"])
        runner.invoke(main, ["install", "up.py"])
        # Modify codebase file to create conflict/update
        cb = get_codebase_dir() / "up.py"
        cb.write_text("changed = True\n")
        # Add a new dep
        helper = get_codebase_dir() / "helper.py"
        helper.write_text("from momem.up import changed\n")
        cb.write_text("from momem.helper import changed\n")
        result = runner.invoke(main, ["update", "--force"])
        assert result.exit_code == 0
        assert "Updated" in result.output or "New dependency" in result.output

    def test_update_auto_when_only_codebase_changed(self, cli_env, sample_script):
        runner, _ = cli_env
        from momemcli.config import get_codebase_dir

        runner.invoke(main, ["memorize", str(sample_script), "c.py"])
        runner.invoke(main, ["install", "c.py"])
        cb = get_codebase_dir() / "c.py"
        cb.write_text("changed = True\n")
        result = runner.invoke(main, ["update"])
        assert result.exit_code == 0
        assert "Updated" in result.output

    def test_update_conflict_when_both_changed(self, cli_env, sample_script):
        runner, _ = cli_env
        from momemcli.config import get_codebase_dir, resolve_install_dir

        runner.invoke(main, ["memorize", str(sample_script), "c.py"])
        runner.invoke(main, ["install", "c.py"])
        cb = get_codebase_dir() / "c.py"
        cb.write_text("changed = True\n")
        local = resolve_install_dir() / "c.py"
        local.write_text("local edit = True\n")
        result = runner.invoke(main, ["update"])
        assert "Conflict" in result.output

    def test_update_obsolete_output(self, cli_env, sample_script):
        runner, _ = cli_env
        from momemcli.config import get_codebase_dir

        runner.invoke(main, ["memorize", str(sample_script), "obs.py"])
        runner.invoke(main, ["install", "obs.py"])
        (get_codebase_dir() / "obs.py").unlink()
        result = runner.invoke(main, ["update"])
        assert "no longer in codebase" in result.output


class TestCLIDiff:
    def test_diff_no_changes(self, cli_env, sample_script):
        runner, _ = cli_env
        runner.invoke(main, ["memorize", str(sample_script), "d.py"])
        runner.invoke(main, ["install", "d.py"])
        result = runner.invoke(main, ["diff"])
        assert result.exit_code == 0
        assert "No differences" in result.output

    def test_diff_with_changes(self, cli_env, sample_script):
        runner, _ = cli_env
        from momemcli.config import resolve_install_dir

        runner.invoke(main, ["memorize", str(sample_script), "d.py"])
        runner.invoke(main, ["install", "d.py"])
        (resolve_install_dir() / "d.py").write_text("changed\n")
        result = runner.invoke(main, ["diff"])
        assert result.exit_code == 0
        assert "---" in result.output
        assert "+++" in result.output

    def test_diff_single_file(self, cli_env, sample_script):
        runner, _ = cli_env
        from momemcli.config import resolve_install_dir

        runner.invoke(main, ["memorize", str(sample_script), "d.py"])
        runner.invoke(main, ["install", "d.py"])
        (resolve_install_dir() / "d.py").write_text("changed\n")
        result = runner.invoke(main, ["diff", "d.py"])
        assert result.exit_code == 0
        assert "d.py" in result.output

    def test_diff_no_install_dir(self, cli_env):
        runner, _ = cli_env
        result = runner.invoke(main, ["diff"])
        assert result.exit_code != 0


class TestCLIShow:
    def test_show_memory(self, cli_env, sample_script):
        runner, _ = cli_env
        runner.invoke(main, ["memorize", str(sample_script), "v.py"])
        result = runner.invoke(main, ["show", "--memory"])
        assert result.exit_code == 0
        assert "v.py" in result.output

    def test_show_memory_empty(self, cli_env):
        runner, _ = cli_env
        result = runner.invoke(main, ["show", "--memory"])
        assert result.exit_code == 0
        assert "empty" in result.output

    def test_show_local_empty(self, cli_env):
        runner, _ = cli_env
        result = runner.invoke(main, ["show"])
        assert result.exit_code == 0
        assert "No snippets" in result.output

    def test_show_local_with_files(self, cli_env, sample_script):
        runner, _ = cli_env
        runner.invoke(main, ["memorize", str(sample_script), "w.py"])
        runner.invoke(main, ["install", "w.py"])
        result = runner.invoke(main, ["show", "--local"])
        assert result.exit_code == 0
        assert "w.py" in result.output

    def test_show_both_flags_error(self, cli_env):
        runner, _ = cli_env
        result = runner.invoke(main, ["show", "--memory", "--local"])
        assert result.exit_code != 0


class TestCLIConfig:
    def test_config_set_global(self, cli_env):
        runner, _ = cli_env
        result = runner.invoke(
            main, ["config", "set", "default_project_dir", "src", "--global"]
        )
        assert result.exit_code == 0
        assert "global" in result.output

    def test_config_set_local(self, cli_env):
        runner, _ = cli_env
        result = runner.invoke(
            main, ["config", "set", "momemdir", "lib/shared", "--local"]
        )
        assert result.exit_code == 0
        assert "local" in result.output

    def test_config_set_no_scope(self, cli_env):
        runner, _ = cli_env
        result = runner.invoke(main, ["config", "set", "codebase", "x"])
        assert result.exit_code != 0

    def test_config_set_invalid_key(self, cli_env):
        runner, _ = cli_env
        result = runner.invoke(main, ["config", "set", "bad_key", "val", "--global"])
        assert result.exit_code != 0

    def test_config_show(self, cli_env):
        runner, _ = cli_env
        result = runner.invoke(main, ["config", "show"])
        assert result.exit_code == 0
        assert "codebase" in result.output
