# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "typer",
#     "redpepper",
# ]
# ///
import enum
import subprocess

import typer


class VersionPart(enum.StrEnum):
    major = "major"
    minor = "minor"
    patch = "patch"


cli = typer.Typer()


@cli.command()
def bump_version(part: VersionPart = VersionPart.patch, dry_run: bool = False):
    if not dry_run and subprocess.call(["git", "diff", "--quiet"]) != 0:
        typer.secho("You have uncommitted changes. Commit first.", fg=typer.colors.RED)
        raise typer.Abort()
    if not dry_run and subprocess.call(["git", "diff", "--staged", "--quiet"]) != 0:
        typer.secho("You have staged changes. Commit first.", fg=typer.colors.RED)
        raise typer.Abort()
    import redpepper.version

    version = redpepper.version.__version__
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

    if not dry_run:
        with open("src/redpepper/version.py", "w") as version_file:
            version_file.write(f'__version__ = "{version}"\n')

        subprocess.check_call(["git", "add", "src/redpepper/version.py"])
        subprocess.check_call(["git", "commit", "-m", f"Bump version to {version}"])
        subprocess.check_call(["git", "tag", version])


if __name__ == "__main__":
    cli()
