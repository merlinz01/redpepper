# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "typer",
# ]
# ///
import glob
import hashlib
import os
import subprocess

import bump_version
import typer

cli = typer.Typer()


@cli.command()
def release(
    dry_run: bool = False,
    bump_version_part: bump_version.VersionPart = bump_version.VersionPart.patch,
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
    if subprocess.call(["git", "diff", "origin/main", "--quiet"]) != 0:
        typer.secho(
            "Your branch is not up to date with 'origin/main'. Run git push first.",
            fg=typer.colors.RED,
        )
        if not dry_run:
            raise typer.Abort()

    version = bump_version.bump_version(
        part=bump_version_part, dry_run=dry_run, commit=False
    )

    typer.secho(f'Releasing version: "{version}"', fg=typer.colors.BLUE, bold=True)

    # Get changelog for this release
    with open("CHANGELOG.md") as f:
        changes = f.readlines()
    while changes and not changes[0].startswith(f"## [{version}]"):
        changes.pop(0)
    if not changes:
        typer.secho("No changes found for this version", fg=typer.colors.RED)
        raise typer.Abort()
    changes.pop(0)
    for i, line in enumerate(changes):
        if line.startswith("## "):
            break
    changes = "".join(changes[: i - 1])
    changes += """
---

You can find the Python packages on [PyPI](https://pypi.org/project/redpepper/).

The `checksums.txt` file contains SHA256 checksums for the release assets.
"""
    typer.secho(changes, fg=typer.colors.YELLOW)

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
    else:
        typer.secho("Checksums:", fg=typer.colors.BLUE, bold=True)
        for file, checksum in checksums.items():
            typer.echo(f"{checksum}  {file}")

    # Confirm before proceeding
    if not typer.confirm(
        typer.style("OK to proceed?", fg=typer.colors.BRIGHT_CYAN, bold=True),
        default=False,
    ):
        raise typer.Abort()

    # Write changelog to a file for gh release command
    if not dry_run:
        typer.echo("Outputting changes to dist/.changelog")
        with open("dist/.changelog", "w") as f:
            f.write(changes)

    # Commit version changes and push
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

    typer.secho("All done!", fg=typer.colors.GREEN)


if __name__ == "__main__":
    cli()
