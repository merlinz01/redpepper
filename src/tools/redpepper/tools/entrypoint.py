import os
import sys
from typing import Annotated

import typer

cli = typer.Typer()


@cli.command()
def basic_agent_config(
    output: typer.FileTextWrite,
    manager_host: Annotated[str, typer.Option(prompt=True)],
    manager_port: Annotated[int, typer.Option(prompt=True)],
    agent_id: Annotated[str, typer.Option(prompt=True)],
):
    """
    Output an agent config file with basic settings.
    """
    import hashlib
    import secrets

    agent_secret = secrets.token_hex(32)
    typer.echo()
    typer.secho("Generated agent secret hash: ", fg=typer.colors.BRIGHT_GREEN, nl=False)
    typer.secho(
        hashlib.sha256(agent_secret.encode()).hexdigest(), fg=typer.colors.BRIGHT_YELLOW
    )
    typer.echo()

    output.write(f"manager_host: {manager_host}\n")
    output.write(f"manager_port: {manager_port}\n")
    output.write(f"agent_id: {agent_id}\n")
    output.write(f"agent_secret: {agent_secret}\n")

    typer.secho(f"Agent config written to {output.name}", fg=typer.colors.BRIGHT_GREEN)


@cli.command()
def basic_manager_config():
    pass


@cli.command()
def install_redpepper_console(
    dest: str | None = None,
    cleanup: bool = False,
):
    """
    Install the RedPepper Console binary into the current directory.
    """
    from .install_redpepper_console import install_or_update_redpepper_console

    install_or_update_redpepper_console(dest, cleanup)


@cli.command()
def install_step_cli(
    version: Annotated[str | None, typer.Argument()] = None,
    dest: str | None = None,
    cleanup: bool = False,
):
    """
    Install the Step CLI binary into the current directory.
    """
    from .install_step_binaries import install_step_binary

    install_step_binary("cli", version, dest, cleanup)


@cli.command()
def install_step_ca(
    version: Annotated[str | None, typer.Argument()] = None,
    dest: str | None = "/usr/local/bin/step-ca" if sys.platform == "linux" else None,
    cleanup: bool = False,
):
    """
    Install the Step CA binary into the current directory.
    """
    from .install_step_binaries import install_step_binary

    install_step_binary("certificates", version, dest, cleanup)


@cli.command()
def setup_step_ca(
    steppath: Annotated[str, typer.Argument()],
    hostname: Annotated[str, typer.Option(prompt=True)] = os.environ.get(
        "HOSTNAME", ""
    ),
):
    """
    Setup a Step CA configuration.
    """
    from .setup_step_ca import setup_step_ca

    setup_step_ca(steppath, hostname)


if sys.platform == "linux":

    @cli.command()
    def install_step_ca_systemd_service(
        steppath: str,
        stepbinary: str = "/usr/local/bin/step-ca",
        stepuser: str = "redpepper",
    ):
        """
        Install the Step CA systemd service.
        """
        from .setup_step_ca import install_step_ca_systemd_service

        install_step_ca_systemd_service(steppath, stepbinary, stepuser)


@cli.command()
def install_step_keypair_agent(
    steppath: str,
    ca_url: str,
    root_fingerprint: str,
    cert_file: str = "/etc/redpepper/agent.pem" if sys.platform == "linux" else "",
    key_file: str = "/etc/redpepper/agent-key.pem" if sys.platform == "linux" else "",
    config_file: str = (
        "/etc/redpepper/agent.d/01-step-ca-certificate.yaml"
        if sys.platform == "linux"
        else ""
    ),
    check_hostname: bool = False,
    install_renew_cron_job: bool = sys.platform == "linux",
    renew_schedule: str = "0 */2 * * *",
    renew_post_cmd: str = "systemctl restart redpepper-agent",
):
    """
    Create a keypair for Redpepper Agent using the Step CA.
    """
    from .step_ca_keypair import create_step_ca_keypair, install_cert_renew_cron_job

    create_step_ca_keypair(
        steppath, "RedPepper Agent", cert_file, key_file, ca_url, root_fingerprint
    )
    with open(config_file, "w") as f:
        f.write(f'tls_cert_file: "{cert_file}"\n')
        f.write(f'tls_key_file: "{key_file}"\n')
        f.write("tls_key_password:\n")
        f.write(f'tls_ca_file: "{steppath}/authorities/redpepper/certs/root_ca.crt"\n')
        f.write(f"tls_check_hostname: {str(check_hostname).lower()}\n")

    if install_renew_cron_job:
        install_cert_renew_cron_job(
            steppath,
            cert_file,
            key_file,
            "redpepper-renew-agent-cert",
            renew_schedule,
            renew_post_cmd,
        )


@cli.command()
def install_step_keypair_manager(
    steppath: str,
    root_fingerprint: str | None = None,
    ca_url: str = "https://localhost:5003",
    cert_file: str = "/etc/redpepper/manager.pem" if sys.platform == "linux" else "",
    key_file: str = "/etc/redpepper/manager-key.pem" if sys.platform == "linux" else "",
    config_file: str = (
        "/etc/redpepper/manager.d/01-step-ca-certificate.yaml"
        if sys.platform == "linux"
        else ""
    ),
    check_hostname: bool = False,
    install_renew_cron_job: bool = sys.platform == "linux",
    renew_schedule: str = "0 */2 * * *",
    renew_post_cmd: str = "systemctl restart redpepper-manager",
):
    """
    Create a keypair for Redpepper Manager using the Step CA.
    """

    from .step_ca_keypair import (
        create_step_ca_keypair,
        get_step_ca_root_fingerprint,
        install_cert_renew_cron_job,
    )

    if root_fingerprint is None:
        root_fingerprint = get_step_ca_root_fingerprint(steppath)

    create_step_ca_keypair(
        steppath, "RedPepper Manager", cert_file, key_file, ca_url, root_fingerprint
    )
    with open(config_file, "w") as f:
        f.write(f'tls_cert_file: "{cert_file}"\n')
        f.write(f'tls_key_file: "{key_file}"\n')
        f.write("tls_key_password:\n")
        f.write(f'tls_ca_file: "{steppath}/authorities/redpepper/certs/root_ca.crt"\n')
        f.write(f"tls_check_hostname: {str(check_hostname).lower()}\n")

    if install_renew_cron_job:
        install_cert_renew_cron_job(
            steppath,
            cert_file,
            key_file,
            "redpepper-renew-manager-cert",
            renew_schedule,
            renew_post_cmd,
        )


@cli.command()
def install_step_keypair_manager_api(
    steppath: str,
    root_fingerprint: str | None = None,
    ca_url: str = "https://localhost:5003",
    cert_file: str = "/etc/redpepper/api.pem" if sys.platform == "linux" else "",
    key_file: str = "/etc/redpepper/api-key.pem" if sys.platform == "linux" else "",
    config_file: str = (
        "/etc/redpepper/manager.d/01-step-ca-api-certificate.yaml"
        if sys.platform == "linux"
        else ""
    ),
    check_hostname: bool = False,
    install_renew_cron_job: bool = sys.platform == "linux",
    renew_schedule: str = "0 */2 * * *",
    renew_post_cmd: str = "systemctl restart redpepper-manager",
):
    """
    Create a keypair for Redpepper Manager API using the Step CA.
    """

    from .step_ca_keypair import (
        create_step_ca_keypair,
        get_step_ca_root_fingerprint,
        install_cert_renew_cron_job,
    )

    if root_fingerprint is None:
        root_fingerprint = get_step_ca_root_fingerprint(steppath)

    create_step_ca_keypair(
        steppath, "RedPepper Manager API", cert_file, key_file, ca_url, root_fingerprint
    )
    with open(config_file, "w") as f:
        f.write(f'api_tls_cert_file: "{cert_file}"\n')
        f.write(f'api_tls_key_file: "{key_file}"\n')
        f.write("api_tls_key_password:\n")

    if install_renew_cron_job:
        install_cert_renew_cron_job(
            steppath,
            cert_file,
            key_file,
            "redpepper-renew-manager-api-cert",
            renew_schedule,
            renew_post_cmd,
        )


if __name__ == "__main__":
    cli()
