# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "typer",
# ]
# ///
import enum
import subprocess
import tomllib

import typer


class VersionPart(enum.StrEnum):
    major = "major"
    minor = "minor"
    patch = "patch"


cli = typer.Typer()


@cli.command()
def bump_version(
    part: VersionPart = VersionPart.patch, dry_run: bool = False, commit=False
):
    # Check for uncommitted changes
    if not dry_run and subprocess.call(["git", "diff", "--quiet"]) != 0:
        typer.secho("You have uncommitted changes. Commit first.", fg=typer.colors.RED)
        raise typer.Abort()
    if not dry_run and subprocess.call(["git", "diff", "--staged", "--quiet"]) != 0:
        typer.secho("You have staged changes. Commit first.", fg=typer.colors.RED)
        raise typer.Abort()

    # Read current version
    env = {}
    with open("src/redpepper/version.py") as f:
        exec(f.read(), env)
    version: str = env["__version__"]

    # Bump version
    typer.echo(f'Current version: "{version}"')
    major, minor, patch = map(int, version.split("."))
    if part == VersionPart.major:
        major += 1
        minor = 0
        patch = 0
    elif part == VersionPart.minor:
        minor += 1
        patch = 0
    elif part == VersionPart.patch:
        patch += 1
    else:
        raise ValueError("Invalid part. Use major, minor or patch")
    version = f"{major}.{minor}.{patch}"
    typer.echo(f'New version: "{version}"')

    # Update changelog
    with open("CHANGELOG.md") as f:
        content = f.read()
    if content.count("## [Unreleased]") != 1:
        typer.secho(
            "Could not find '## [Unreleased]' in CHANGELOG.md", fg=typer.colors.RED
        )
        raise typer.Abort()
    content = content.replace("## [Unreleased]", f"## [{version}]")
    if not dry_run:
        typer.echo("Updating changelog")
        with open("CHANGELOG.md", "w") as f:
            f.write(content)
    else:
        typer.echo_via_pager(content)

    # Update version file
    if not dry_run:
        typer.echo("Writing version file")
        with open("src/redpepper/version.py", "w") as version_file:
            version_file.write(f'__version__ = "{version}"\n')

    # Sync lockfile
    typer.echo("Upgrading package versions in lockfile")
    lockfile = tomllib.load(open("pyproject.toml", "rb"))
    args = ["uv", "lock"]
    for package, packageconf in lockfile["tool"]["uv"]["sources"].items():
        if packageconf.get("workspace"):
            args.append("--upgrade-package")
            args.append(package)
    if not dry_run:
        subprocess.check_call(args)
    else:
        typer.echo("Would run " + " ".join(args))

    # Commit changes
    if not dry_run and commit:
        subprocess.check_call(
            ["git", "add", "CHANGELOG.md", "src/redpepper/version.py", "uv.lock"]
        )
        subprocess.check_call(["git", "commit", "-m", f"Bump version to {version}"])
        subprocess.check_call(["git", "tag", version])

    return version


if __name__ == "__main__":
    cli()
