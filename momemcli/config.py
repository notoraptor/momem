"""Configuration management for momem (global and local)."""

from pathlib import Path

import yaml

TOOL_DIR = Path.home() / ".momem"
GLOBAL_CONFIG_FILE = TOOL_DIR / ".momem.yaml"
LOCAL_CONFIG_FILE = ".momem.yaml"

# Global config keys and defaults
DEFAULT_CODEBASE = TOOL_DIR / "momem"
GLOBAL_KEYS = {"codebase", "default_project_dir"}
LOCAL_KEYS = {"momemdir"}


def ensure_tool_dir() -> None:
    """Create ~/.momem/ and default codebase directory if they don't exist."""
    TOOL_DIR.mkdir(parents=True, exist_ok=True)
    DEFAULT_CODEBASE.mkdir(parents=True, exist_ok=True)


def load_global_config() -> dict:
    """Load the global configuration from ~/.momem/.momem.yaml."""
    if not GLOBAL_CONFIG_FILE.exists():
        return {}
    with open(GLOBAL_CONFIG_FILE) as f:
        data = yaml.safe_load(f)
    return data if isinstance(data, dict) else {}


def save_global_config(config: dict) -> None:
    """Save the global configuration to ~/.momem/.momem.yaml."""
    ensure_tool_dir()
    with open(GLOBAL_CONFIG_FILE, "w") as f:
        yaml.dump(config, f, default_flow_style=False)


def load_local_config() -> dict:
    """Load the local configuration from .momem.yaml in the current directory."""
    local_path = Path.cwd() / LOCAL_CONFIG_FILE
    if not local_path.exists():
        return {}
    with open(local_path) as f:
        data = yaml.safe_load(f)
    return data if isinstance(data, dict) else {}


def save_local_config(config: dict) -> None:
    """Save the local configuration to .momem.yaml in the current directory."""
    local_path = Path.cwd() / LOCAL_CONFIG_FILE
    with open(local_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False)


def get_codebase_dir() -> Path:
    """Return the path to the codebase directory."""
    global_config = load_global_config()
    codebase = global_config.get("codebase")
    if codebase:
        return Path(codebase).expanduser() / "momem"
    return DEFAULT_CODEBASE


def resolve_install_dir() -> Path:
    """Resolve the local installation directory for snippets.

    Resolution order:
    1. Local config 'momemdir' -> used as-is
    2. Global config 'default_project_dir' -> PROJECT_DIR/<value>/momem
    3. Default -> PROJECT_DIR/<project_dir_name>/momem
    """
    local_config = load_local_config()
    momemdir = local_config.get("momemdir")
    if momemdir:
        return Path.cwd() / momemdir

    global_config = load_global_config()
    default_project_dir = global_config.get("default_project_dir")
    if default_project_dir:
        return Path.cwd() / default_project_dir / "momem"

    project_name = Path.cwd().name
    return Path.cwd() / project_name / "momem"


def set_config(key: str, value: str, *, is_global: bool) -> None:
    """Set a configuration key in global or local config."""
    if is_global:
        if key not in GLOBAL_KEYS:
            raise ValueError(
                f"Unknown global config key: {key!r}. "
                f"Valid keys: {', '.join(sorted(GLOBAL_KEYS))}"
            )
        config = load_global_config()
        config[key] = value
        save_global_config(config)
    else:
        if key not in LOCAL_KEYS:
            raise ValueError(
                f"Unknown local config key: {key!r}. "
                f"Valid keys: {', '.join(sorted(LOCAL_KEYS))}"
            )
        config = load_local_config()
        config[key] = value
        save_local_config(config)


def show_config() -> dict:
    """Return the effective configuration (merged global + local)."""
    global_config = load_global_config()
    local_config = load_local_config()
    return {
        "codebase": str(get_codebase_dir()),
        "default_project_dir": global_config.get("default_project_dir"),
        "momemdir": local_config.get("momemdir"),
        "resolved_install_dir": str(resolve_install_dir()),
    }
