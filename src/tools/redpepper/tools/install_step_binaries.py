import hashlib
import os
import platform
import re
import sys
import tarfile

import requests
import typer

platform_map = {
    "linux": "linux",
    "win32": "windows",
    "darwin": "darwin",
}

architecture_map = {
    "x86_64": "amd64",
    "i386": "386",
}

basic_version_re = re.compile(r"v(\d+\.\d+\.\d+)")


def install_step_binary(
    tool: str,
    version: str | None,
    archive_path: str,
    dest: str,
    remove_download: bool = False,
):
    if tool == "cli":
        suffix = ""
    elif tool == "certificates":
        suffix = "-ca"
    else:
        raise RuntimeError(f"Invalid Step tool: {tool}")

    # Get the latest version if none is provided
    page = 1
    while version is None:
        typer.echo(
            (
                f"Getting the latest version of step {tool}..." + f"(page {page})"
                if page > 1
                else ""
            ),
        )
        response = requests.get(
            f"https://api.github.com/repos/smallstep/{tool}/releases?per_page=10&page={page}"
        )
        response.raise_for_status()
        releases = response.json()
        if not releases:
            raise RuntimeError("No releases found")
        for release in releases:
            if basic_version_re.match(release["tag_name"]):
                version = release["tag_name"][1:]
                typer.echo(f"Found latest version: {version}")
                break
        page += 1

    # Get the platform
    try:
        plat = platform_map[sys.platform]
    except KeyError:
        raise RuntimeError(f"Unknown platform: {sys.platform}")

    # Get the architecture
    try:
        arch = architecture_map[platform.machine()]
    except KeyError:
        raise RuntimeError(f"Unknown architecture: {platform.machine()}")

    # Download the checksum file
    typer.echo(f"Downloading checksum for step {tool} v{version}...")
    checksum_url = f"https://github.com/smallstep/{tool}/releases/download/v{version}/checksums.txt"
    response = requests.get(checksum_url)
    response.raise_for_status()
    checksums = response.text.splitlines()
    for line in checksums:
        checksum, filename = line.split()
        if filename == f"step{suffix}_{plat}_{version}_{arch}.tar.gz":
            break
    else:
        raise RuntimeError("Checksum for step download not found in checksum file")

    # Verify the checksum of the archive if it exists
    download = True
    if os.path.exists(archive_path):
        try:
            verify_checksum(archive_path, checksum)
        except ValueError:
            typer.echo("Checksum mismatch, redownloading...")
        else:
            download = False
            typer.echo(
                f"Step {tool} v{version} for {plat} {arch} already downloaded and checksum verified"
            )

    # Otherwise download the archive from the release
    if download:
        download_url = f"https://github.com/smallstep/{tool}/releases/download/v{version}/step{suffix}_{plat}_{version}_{arch}.tar.gz"

        # Download the tarball
        typer.echo(f"Downloading step {tool} v{version} for {plat} {arch}...")
        response = requests.get(download_url, stream=True)
        response.raise_for_status()

        # Write the tarball to a temporary file
        size = int(response.headers["Content-Length"])
        typer.echo(f"Total size: {size}")
        with (
            open(archive_path, "wb") as f,
            typer.progressbar(length=size, label="Downloading") as progress,
        ):
            for chunk in response.iter_content(chunk_size=1024):
                f.write(chunk)
                progress.update(len(chunk))

        # Verify the checksum
        verify_checksum(archive_path, checksum)

    # Extract the step binary
    if not os.path.isdir(destdir := os.path.dirname(dest)):
        typer.echo(f"Creating directory {destdir}...")
        os.makedirs(destdir)
    typer.echo(f"Extracting the step {tool} binary...")
    with tarfile.open(archive_path, "r:gz") as tar, open(dest, "wb") as dst:
        if tool == "cli":
            srcfile = f"step{suffix}_{version}/bin/step{suffix}"
        else:
            srcfile = "step-ca"
        src = tar.extractfile(srcfile)
        if src is None:
            raise RuntimeError("step binary not found in tarball")
        dst.write(src.read())

    # Make the binary executable
    if sys.platform != "win32":
        os.chmod(dest, 0o755)

    # Clean up
    if remove_download:
        typer.echo("Removing the downloaded archive...")
        os.remove(archive_path)

    typer.echo(f"Step {tool} installed successfully")


def verify_checksum(file: str, checksum: str):
    # Verify the checksum
    typer.echo("Verifying the checksum...")
    hasher = hashlib.sha256()
    with open(file, "rb") as f:
        while chunk := f.read(4096):
            hasher.update(chunk)
    if hasher.hexdigest() != checksum:
        raise ValueError("Checksum mismatch")
