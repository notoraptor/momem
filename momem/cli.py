"""CLI interface for momem using click."""

import click
import yaml

from momem import codebase, config, project


@click.group()
def main() -> None:
    """Manage reusable Python code snippets across projects."""


@main.command()
@click.argument("source")
@click.argument("dest", required=False)
@click.option("--force", is_flag=True, help="Overwrite if file already exists.")
def memorize(source: str, dest: str | None, force: bool) -> None:
    """Add a Python file to the momem codebase."""
    try:
        target = codebase.memorize(source, dest, force=force)
        click.echo(f"Memorized: {target}")
    except (FileNotFoundError, FileExistsError, ValueError) as e:
        raise click.ClickException(str(e))


@main.command()
@click.argument("path")
@click.option(
    "--force", is_flag=True, help="Remove even if other snippets depend on it."
)
def forget(path: str, force: bool) -> None:
    """Remove a file from the momem codebase."""
    try:
        codebase.forget(path, force=force)
        click.echo(f"Forgotten: {path}")
    except (FileNotFoundError, ValueError) as e:
        raise click.ClickException(str(e))


@main.command()
@click.argument("path")
@click.option("--force", is_flag=True, help="Overwrite existing local files.")
def install(path: str, force: bool) -> None:
    """Install a snippet from the codebase into the local project."""
    try:
        installed = project.install(path, force=force)
        for f in installed:
            click.echo(f"Installed: {f}")
    except (FileNotFoundError, FileExistsError) as e:
        raise click.ClickException(str(e))


@main.command()
@click.argument("path", required=False)
@click.option("--all", "all_", is_flag=True, help="Remove all installed snippets.")
def uninstall(path: str | None, all_: bool) -> None:
    """Remove installed snippet(s) from the local project."""
    try:
        removed = project.uninstall(path, all_=all_)
        for f in removed:
            click.echo(f"Uninstalled: {f}")
    except (FileNotFoundError, ValueError) as e:
        raise click.ClickException(str(e))


@main.command()
@click.option("--force", is_flag=True, help="Overwrite conflicting local files.")
def update(force: bool) -> None:
    """Update all installed snippets from the codebase."""
    try:
        result = project.update(force=force)
    except FileNotFoundError as e:
        raise click.ClickException(str(e))

    for f in result["updated"]:
        click.echo(f"Updated: {f}")
    for f in result["new_deps"]:
        click.echo(f"New dependency installed: {f}")
    for f in result["conflicts"]:
        click.echo(f"Conflict (use --force to overwrite): {f}", err=True)
    for f in result["obsolete_deps"]:
        click.echo(f"Warning: no longer in codebase: {f}", err=True)

    if not any(result.values()):
        click.echo("Everything is up to date.")


@main.command()
@click.option("--memory", is_flag=True, help="Show files in the codebase.")
@click.option("--local", "local_", is_flag=True, help="Show files installed locally.")
def show(memory: bool, local_: bool) -> None:
    """Show available snippets (--memory for codebase, --local for project)."""
    if memory and local_:
        raise click.ClickException("Use either --memory or --local, not both.")

    if memory:
        files = codebase.show_memory()
        if not files:
            click.echo("Codebase is empty.")
        else:
            click.echo("Codebase:")
            for f in files:
                click.echo(f"  {f}")
    else:
        # Default to --local
        files = project.show_local()
        if not files:
            click.echo("No snippets installed in this project.")
        else:
            click.echo("Installed snippets:")
            for f in files:
                click.echo(f"  {f}")


@main.group(name="config")
def config_cmd() -> None:
    """Manage momem configuration."""


@config_cmd.command(name="set")
@click.argument("key")
@click.argument("value")
@click.option("--global", "is_global", is_flag=True, help="Set in global config.")
@click.option("--local", "is_local", is_flag=True, help="Set in local config.")
def config_set(key: str, value: str, is_global: bool, is_local: bool) -> None:
    """Set a configuration value."""
    if is_global == is_local:
        raise click.ClickException("Specify exactly one of --global or --local.")
    try:
        config.set_config(key, value, is_global=is_global)
        scope = "global" if is_global else "local"
        click.echo(f"Set {scope} config: {key} = {value}")
    except ValueError as e:
        raise click.ClickException(str(e))


@config_cmd.command(name="show")
def config_show() -> None:
    """Show the effective configuration."""
    effective = config.show_config()
    click.echo(yaml.dump(effective, default_flow_style=False).strip())
