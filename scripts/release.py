# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "typer",
# ]
# ///
import enum
import glob
import hashlib
import os
import subprocess
import tomllib

import typer

cli = typer.Typer()


class VersionPart(enum.StrEnum):
    major = "major"
    minor = "minor"
    patch = "patch"


@cli.command()
def release(
    dry_run: bool = False,
    bump_version_part: VersionPart = VersionPart.patch,
    force_push: bool = False,
):
    # Check for uncommitted changes
    if subprocess.call(["git", "diff", "--quiet"]) != 0:
        typer.secho("You have uncommitted changes. Commit first.", fg=typer.colors.RED)
        if not dry_run:
            raise typer.Abort()
    if subprocess.call(["git", "diff", "--staged", "--quiet"]) != 0:
        typer.secho("You have staged changes. Commit first.", fg=typer.colors.RED)
        if not dry_run:
            raise typer.Abort()

    # Read current version
    env = {}
    with open("src/redpepper/version.py") as f:
        exec(f.read(), env)
    version = env["__version__"]

    # Bump version
    typer.echo(f'Current version: "{version}"')
    major, minor, patch = map(int, version.split("."))
    if bump_version_part == VersionPart.major:
        major += 1
        minor = 0
        patch = 0
    elif bump_version_part == VersionPart.minor:
        minor += 1
        patch = 0
    elif bump_version_part == VersionPart.patch:
        patch += 1
    else:
        raise ValueError("Invalid part. Use major, minor or patch")
    version = f"{major}.{minor}.{patch}"
    typer.echo(f'New version: "{version}"')

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

    # Read changelog
    with open("CHANGELOG.md") as f:
        changelog = f.read()
    if changelog.count("## [Unreleased]") != 1:
        typer.secho(
            "Could not find '## [Unreleased]' in CHANGELOG.md", fg=typer.colors.RED
        )
        raise typer.Abort()
    changelog = changelog.replace("## [Unreleased]", f"## [{version}]")

    typer.secho(f'Releasing version: "{version}"', fg=typer.colors.BLUE, bold=True)

    # Extract release message from changelog
    changes = changelog.splitlines()
    while changes and not changes[0].startswith(f"## [{version}]"):
        changes.pop(0)
    if not changes:
        typer.secho("No changes found for this version", fg=typer.colors.RED)
        raise typer.Abort()
    changes.pop(0)
    for i, line in enumerate(changes):
        if line.startswith("## "):
            changes = changes[:i]
            break
    changes = "\n".join(changes)
    changes += """
---

You can find the Python packages on [PyPI](https://pypi.org/project/redpepper/).

The `checksums.txt` file contains SHA256 checksums for the release assets.
"""
    typer.secho(changes, fg=typer.colors.YELLOW)

    # Build the assets
    subprocess.check_call(["poe", "build"])
    subprocess.check_call(["poe", "buildconsole"])

    # Collect assets and calculate checksums
    typer.secho(
        "Will create Github release with these assets:",
        fg=typer.colors.BLUE,
        bold=True,
    )
    files = glob.glob("dist/*.whl") + glob.glob("dist/*.tar.gz")
    checksums = {}
    for file in files:
        typer.echo(f"  - {typer.style(file, fg=typer.colors.MAGENTA)}")
        with open(file, "rb") as f:
            hash = hashlib.sha256()
            while chunk := f.read(4096):
                hash.update(chunk)
            checksums[os.path.basename(file)] = hash.hexdigest()

    # Write checksums to a file
    if not dry_run:
        with open("dist/checksums.txt", "w") as f:
            for file, checksum in checksums.items():
                f.write(f"{checksum}  {file}\n")
        files.append("dist/checksums.txt")
        typer.echo(f"  - {typer.style('dist/checksums.txt', fg=typer.colors.MAGENTA)}")

    typer.secho("Checksums:", fg=typer.colors.BLUE, bold=True)
    for file, checksum in checksums.items():
        typer.echo(f"{checksum}  {file}")

    # Confirm before proceeding
    if not typer.confirm(
        typer.style("OK to proceed?", fg=typer.colors.BRIGHT_CYAN, bold=True),
        default=False,
    ):
        raise typer.Abort()

    # Update changelog
    if not dry_run:
        typer.echo("Updating changelog")
        with open("CHANGELOG.md", "w") as f:
            f.write(changelog)

    # Commit changes and push
    if not dry_run:
        subprocess.check_call(
            ["git", "add", "CHANGELOG.md", "src/redpepper/version.py", "uv.lock"]
        )
        subprocess.check_call(["git", "commit", "-m", f"Bump version to {version}"])
        subprocess.check_call(["git", "tag", version])
        if force_push:
            subprocess.check_call(["git", "push", "--force"])
            subprocess.check_call(["git", "push", "--tags", "--force"])
        else:
            subprocess.check_call(["git", "push"])
            subprocess.check_call(["git", "push", "--tags"])

    # Write changelog to a file for gh release command
    if not dry_run:
        typer.echo("Outputting changes to dist/.changelog")
        with open("dist/.changelog", "w") as f:
            f.write(changes)

    # Create Github release
    if not dry_run:
        typer.echo("Creating Github release")
        if (
            subprocess.call(
                [
                    "gh",
                    "release",
                    "create",
                    version,
                    *files,
                    "-F",
                    "dist/.changelog",
                ]
            )
            != 0
        ):
            raise typer.Abort()
    else:
        typer.echo("Would create Github release.")

    # Publish to PyPI
    if not dry_run:
        typer.echo("Publishing to PyPI")
        subprocess.check_call(["poe", "publishpypi"])
    else:
        typer.echo("Would publish to PyPI")

    typer.secho("All done!", fg=typer.colors.GREEN)


if __name__ == "__main__":
    cli()
