import json
import os
import subprocess
import sys

import typer


def ensure_bootstrapped(
    steppath: str, stepbinary: str, ca_url: str, root_fingerprint: str
):
    ca_config_file = os.path.join(
        steppath, "authorities", "redpepper", "config", "defaults.json"
    )
    if os.path.exists(ca_config_file):
        with open(ca_config_file) as f:
            config = json.load(f)
        if (
            config.get("fingerprint") == root_fingerprint
            and config.get("ca-url") == ca_url
        ):
            typer.echo("CA config already bootstrapped")
            return
    typer.secho("Bootstrapping the CA config", fg=typer.colors.GREEN)
    if subprocess.run(
        [
            stepbinary,
            "ca",
            "bootstrap",
            "--ca-url",
            ca_url,
            "--fingerprint",
            root_fingerprint,
            "--context",
            "redpepper",
            "--force",
        ],
        env={"STEPPATH": steppath},
    ).returncode:
        typer.secho("Error bootstrapping the CA config", fg=typer.colors.RED)
        raise typer.Abort()


def create_step_ca_keypair(
    steppath: str,
    stepbinary: str,
    subject: str,
    cert_file: str,
    key_file: str,
    ca_url: str,
    root_fingerprint: str,
    password_file: str | None = None,
):
    """
    Create a keypair for the Step CA.
    """
    ensure_bootstrapped(steppath, stepbinary, ca_url, root_fingerprint)

    typer.echo("Creating the keypair...")
    args = [
        stepbinary,
        "ca",
        "certificate",
        subject,
        cert_file,
        key_file,
        "--context",
        "redpepper",
        "--force",
    ]
    if password_file:
        args.extend(["--password-file", password_file])
    if subprocess.run(
        args,
        env={"STEPPATH": steppath},
    ).returncode:
        typer.secho("Error creating the keypair", fg=typer.colors.RED)
        raise typer.Abort()
    typer.echo("Keypair created")


def get_step_ca_root_fingerprint(steppath: str, stepbinary: str) -> str:
    typer.echo("Getting the root fingerprint...")
    fingerprint = (
        subprocess.check_output(
            [
                stepbinary,
                "certificate",
                "fingerprint",
                os.path.join(steppath, "certs", "root_ca.crt"),
            ]
        )
        .decode()
        .strip()
    )
    typer.echo(f"Root fingerprint: {fingerprint}")
    return fingerprint


def install_cert_renew_cron_job(
    steppath: str,
    stepbinary: str,
    cert_file: str,
    key_file: str,
    jobname: str,
    schedule: str,
    post_renew_cmd: str,
):
    if sys.platform != "linux":
        typer.secho("Cron jobs are only supported on Linux", fg=typer.colors.RED)
        raise typer.Abort()
    typer.echo("Installing the cron job to renew the certificate...")
    task = f'{schedule} root STEPPATH={steppath} {stepbinary} ca renew {cert_file} {key_file} --exec "{post_renew_cmd}" --force --expires-in 3h >> /var/log/redpepper-cert-renew.log 2>&1\n'
    with open(f"/etc/cron.d/{jobname}", "w") as f:
        f.write(task)
    typer.echo("Cron job installed")
