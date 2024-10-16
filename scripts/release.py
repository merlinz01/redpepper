# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "typer",
#     "redpepper",
# ]
# ///
import glob
import subprocess

import typer

cli = typer.Typer()


@cli.command()
def release(dry_run: bool = False):
    if not dry_run and subprocess.call(["git", "diff", "--quiet"]) != 0:
        typer.secho("You have uncommitted changes. Commit first.", fg=typer.colors.RED)
        raise typer.Abort()
    if not dry_run and subprocess.call(["git", "diff", "--staged", "--quiet"]) != 0:
        typer.secho("You have staged changes. Commit first.", fg=typer.colors.RED)
        raise typer.Abort()
    from redpepper.version import __version__ as version

    typer.echo(f'Releasing version: "{version}"')

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

    if not typer.confirm("Do the changes look OK?", default=False):
        raise typer.Abort()

    if not dry_run:
        typer.echo("Outputting changes to dist/.changelog")
        with open("dist/.changelog", "w") as f:
            f.write(changes)

    files = glob.glob("dist/*.whl") + glob.glob("dist/*.tar.gz")
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
        typer.secho("Would create Github release with:", fg=typer.colors.GREEN)
        for file in files:
            typer.echo(f"  - {file}")

    typer.secho("All done!", fg=typer.colors.GREEN)


if __name__ == "__main__":
    cli()
