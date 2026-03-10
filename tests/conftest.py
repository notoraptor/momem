"""Shared fixtures for momem tests."""

import os
from pathlib import Path

import pytest

from momem import config


@pytest.fixture
def tmp_home(tmp_path, monkeypatch):
    """Set up a temporary home directory with ~/.momem structure."""
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setattr(config, "TOOL_DIR", home / ".momem")
    monkeypatch.setattr(config, "GLOBAL_CONFIG_FILE", home / ".momem" / ".momem.yaml")
    monkeypatch.setattr(config, "DEFAULT_CODEBASE", home / ".momem" / "momem")
    return home


@pytest.fixture
def tmp_project(tmp_path, monkeypatch):
    """Set up a temporary project directory."""
    project = tmp_path / "myproject"
    project.mkdir()
    monkeypatch.chdir(project)
    return project


@pytest.fixture
def setup_env(tmp_home, tmp_project):
    """Combined fixture: temporary home + project directory."""
    config.ensure_tool_dir()
    return tmp_home, tmp_project


@pytest.fixture
def sample_script(tmp_path):
    """Create a sample Python script and return its path."""
    script = tmp_path / "sample.py"
    script.write_text('def hello():\n    return "hello"\n', encoding="utf-8")
    return script


@pytest.fixture
def sample_script_with_dep(tmp_path):
    """Create two scripts where one depends on the other."""
    dep = tmp_path / "helper.py"
    dep.write_text('def assist():\n    return "help"\n', encoding="utf-8")

    main = tmp_path / "main.py"
    main.write_text(
        'from momem.helper import assist\n\ndef run():\n    return assist()\n',
        encoding="utf-8",
    )
    return main, dep
