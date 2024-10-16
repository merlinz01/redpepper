# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "typer",
# ]
# ///
import glob
import subprocess

import typer

cli = typer.Typer()


@cli.command()
def release(dry_run: bool = False):
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
    # from redpepper.version import __version__ as version
    env = {}
    with open("src/redpepper/version.py") as f:
        exec(f.read(), env)
    version: str = env["__version__"]

    typer.secho(f'Releasing version: "{version}"', fg=typer.colors.BLUE, bold=True)

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
    typer.secho(changes, fg=typer.colors.YELLOW)

    typer.secho(
        "Will create Github release with these artifacts:",
        fg=typer.colors.BLUE,
        bold=True,
    )
    files = glob.glob("dist/*.whl") + glob.glob("dist/*.tar.gz")
    for file in files:
        typer.echo(f"  - {typer.style(file, fg=typer.colors.MAGENTA)}")

    if not typer.confirm(
        typer.style("OK to proceed?", fg=typer.colors.BRIGHT_CYAN, bold=True),
        default=False,
    ):
        raise typer.Abort()

    if not dry_run:
        typer.echo("Outputting changes to dist/.changelog")
        with open("dist/.changelog", "w") as f:
            f.write(changes)

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

    typer.secho("All done!", fg=typer.colors.GREEN)


if __name__ == "__main__":
    cli()
