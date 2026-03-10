"""Tests for momem.config."""

from pathlib import Path

import pytest

from momemcli import config


class TestEnsureToolDir:
    def test_creates_directories(self, tmp_home):
        config.ensure_tool_dir()
        assert config.TOOL_DIR.exists()
        assert config.DEFAULT_CODEBASE.exists()


class TestGlobalConfig:
    def test_load_empty(self, tmp_home):
        assert config.load_global_config() == {}

    def test_save_and_load(self, tmp_home):
        config.save_global_config({"codebase": "/my/path"})
        loaded = config.load_global_config()
        assert loaded == {"codebase": "/my/path"}

    def test_set_valid_key(self, tmp_home):
        config.set_config("codebase", "/new/path", is_global=True)
        loaded = config.load_global_config()
        assert loaded["codebase"] == "/new/path"

    def test_set_invalid_key(self, tmp_home):
        with pytest.raises(ValueError, match="Unknown global config key"):
            config.set_config("bad_key", "value", is_global=True)


class TestLocalConfig:
    def test_load_empty(self, tmp_project):
        assert config.load_local_config() == {}

    def test_save_and_load(self, tmp_project):
        config.save_local_config({"momemdir": "my/dir"})
        loaded = config.load_local_config()
        assert loaded == {"momemdir": "my/dir"}

    def test_set_valid_key(self, tmp_project):
        config.set_config("momemdir", "custom/dir", is_global=False)
        loaded = config.load_local_config()
        assert loaded["momemdir"] == "custom/dir"

    def test_set_invalid_key(self, tmp_project):
        with pytest.raises(ValueError, match="Unknown local config key"):
            config.set_config("bad_key", "value", is_global=False)


class TestGetCodebaseDir:
    def test_default(self, tmp_home):
        assert config.get_codebase_dir() == config.DEFAULT_CODEBASE

    def test_custom(self, tmp_home):
        config.save_global_config({"codebase": "/custom/base"})
        assert config.get_codebase_dir() == Path("/custom/base/momem")


class TestResolveInstallDir:
    def test_default_uses_project_name(self, setup_env):
        _, project = setup_env
        expected = project / "myproject" / "momem"
        assert config.resolve_install_dir() == expected

    def test_global_default_project_dir(self, setup_env):
        _, project = setup_env
        config.save_global_config({"default_project_dir": "src"})
        expected = project / "src" / "momem"
        assert config.resolve_install_dir() == expected

    def test_local_momemdir_takes_priority(self, setup_env):
        _, project = setup_env
        config.save_global_config({"default_project_dir": "src"})
        config.save_local_config({"momemdir": "lib/shared"})
        expected = project / "lib" / "shared"
        assert config.resolve_install_dir() == expected


class TestShowConfig:
    def test_shows_effective_config(self, setup_env):
        result = config.show_config()
        assert "codebase" in result
        assert "resolved_install_dir" in result
        assert "default_project_dir" in result
        assert "momemdir" in result
