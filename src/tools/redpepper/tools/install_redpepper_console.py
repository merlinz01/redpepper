import hashlib
import os
import tarfile

import typer

import requests


def install_or_update_redpepper_console(
    dest: str | None, remove_download: bool = False
):
    # Get the latest version
    typer.echo(
        f"Getting the latest release...",
    )
    response = requests.get(
        f"https://api.github.com/repos/merlinz01/redpepper/releases/latest"
    )
    if response.status_code == 404:
        typer.secho("No releases found!", fg=typer.colors.RED)
        raise typer.Abort()
    response.raise_for_status()
    release = response.json()
    version = release["tag_name"]

    # Download the checksum file
    typer.echo(f"Downloading checksum...")
    checksum_url = f"https://github.com/merlinz01/redpepper/releases/download/{version}/checksums.txt"
    response = requests.get(checksum_url)
    response.raise_for_status()
    checksums = response.text.splitlines()
    for line in checksums:
        checksum, filename = line.split()
        if filename == f"console.tar.gz":
            break
    else:
        raise RuntimeError("Checksum for console archive not found in checksum file")

    gzfile = "console.tar.gz"

    # Verify the checksum of the archive if it exists
    download = True
    if os.path.exists(gzfile):
        try:
            verify_checksum(gzfile, checksum)
        except ValueError:
            typer.echo("Checksum mismatch, redownloading...")
        else:
            download = False
            typer.echo(f"Console archive already downloaded and checksum verified")

    # Otherwise download the archive from the release
    if download:
        download_url = f"https://github.com/merlinz01/redpepper/releases/download/{version}/console.tar.gz"

        # Download the tarball
        typer.echo(f"Downloading RedPepper Console {version}...")
        response = requests.get(download_url, stream=True)
        response.raise_for_status()

        # Write the tarball to a temporary file
        size = int(response.headers["Content-Length"])
        typer.echo(f"Total size: {size}")
        with (
            open(gzfile, "wb") as f,
            typer.progressbar(length=size, label="Downloading") as progress,
        ):
            for chunk in response.iter_content(chunk_size=1024):
                f.write(chunk)
                progress.update(len(chunk))

        # Verify the checksum
        verify_checksum(gzfile, checksum)

    else:
        typer.echo(f"RedPepper Console {version} already downloaded")

    dest = dest or f"./console"

    # Extract the archive
    typer.echo(f"Extracting the archive...")
    with tarfile.open(gzfile, "r:gz") as tar:
        with typer.progressbar(length=len(tar.getnames())) as progress:

            def filter(ti, n):
                progress.update(1)
                return ti

            tar.extractall(dest, filter=filter)

    # Clean up
    if remove_download:
        typer.echo("Removing the downloaded archive...")
        os.remove(gzfile)

    typer.echo(f"RedPepper installed successfully")


def verify_checksum(file: str, checksum: str):
    # Verify the checksum
    typer.echo("Verifying the checksum...")
    hasher = hashlib.sha256()
    with open(file, "rb") as f:
        while chunk := f.read(4096):
            hasher.update(chunk)
    if hasher.hexdigest() != checksum:
        raise ValueError("Checksum mismatch")
