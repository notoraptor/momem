"""Integration tests for the momem CLI."""

import pytest
from click.testing import CliRunner

from momem.cli import main


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


class TestCLIUpdate:
    def test_update_up_to_date(self, cli_env, sample_script):
        runner, _ = cli_env
        runner.invoke(main, ["memorize", str(sample_script), "u.py"])
        runner.invoke(main, ["install", "u.py"])
        result = runner.invoke(main, ["update"])
        assert result.exit_code == 0
        assert "up to date" in result.output


class TestCLIShow:
    def test_show_memory(self, cli_env, sample_script):
        runner, _ = cli_env
        runner.invoke(main, ["memorize", str(sample_script), "v.py"])
        result = runner.invoke(main, ["show", "--memory"])
        assert result.exit_code == 0
        assert "v.py" in result.output

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

    def test_config_show(self, cli_env):
        runner, _ = cli_env
        result = runner.invoke(main, ["config", "show"])
        assert result.exit_code == 0
        assert "codebase" in result.output
