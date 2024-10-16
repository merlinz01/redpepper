import os
import sys
from typing import Annotated

import typer

cli = typer.Typer()

match sys.platform:
    case "linux":
        REDPEPPER_CONFIG_DIR = "/etc/redpepper"
        REDPEPPER_LIB_DIR = "/var/lib/redpepper"
    case _:
        typer.secho(
            "This script is currently only supported on Linux. Using ~/.config/redpepper as the config dir.",
            fg=typer.colors.RED,
        )
        REDPEPPER_CONFIG_DIR = os.path.expanduser("~/.config/redpepper")
        REDPEPPER_LIB_DIR = os.path.expanduser("~/.local/share/redpepper")

DEFAULT_STEP_PATH = os.path.join(REDPEPPER_LIB_DIR, "step")


@cli.command()
def basic_agent_config(
    manager_host: Annotated[str, typer.Option(prompt=True)],
    manager_port: Annotated[int, typer.Option(prompt=True)],
    agent_id: Annotated[str, typer.Option(prompt=True)],
    file: str = os.path.join(REDPEPPER_CONFIG_DIR, "agent.d/01-manager.yaml"),
):
    """
    Output an agent config file with basic settings.
    """
    import hashlib
    import secrets

    agent_secret = secrets.token_hex(32)
    typer.echo()
    typer.secho("Generated agent secret hash: ", fg=typer.colors.BRIGHT_CYAN, nl=False)
    typer.secho(
        hashlib.sha256(agent_secret.encode()).hexdigest(), fg=typer.colors.BRIGHT_YELLOW
    )
    typer.echo()

    with open(file, "w") as output:
        output.write(f"manager_host: {manager_host}\n")
        output.write(f"manager_port: {manager_port}\n")
        output.write(f"agent_id: {agent_id}\n")
        output.write(f"agent_secret: {agent_secret}\n")

    typer.secho(f"Agent config written to {output.name}", fg=typer.colors.BRIGHT_GREEN)


@cli.command()
def install_console(
    dest: str = os.path.join(REDPEPPER_LIB_DIR, "redpepper-console"),
    cleanup: bool = False,
    config_file: str = os.path.join(
        REDPEPPER_CONFIG_DIR, "manager.d", "01-console.yml"
    ),
):
    """
    Install the RedPepper Console binary into the current directory.
    """
    from .install_redpepper_console import install_or_update_redpepper_console

    install_or_update_redpepper_console(dest, cleanup)

    with open(config_file, "w") as f:
        f.write(f"api_static_dir: {dest}\n")


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
    dest: str = os.path.join(DEFAULT_STEP_PATH, "step-ca"),
    cleanup: bool = False,
):
    """
    Install the Step CA binary into the current directory.
    """
    from .install_step_binaries import install_step_binary

    install_step_binary("certificates", version, dest, cleanup)


@cli.command()
def setup_step_ca(
    steppath: str = DEFAULT_STEP_PATH,
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
    ca_url: str,
    root_fingerprint: str,
    cert_file: str = os.path.join(REDPEPPER_CONFIG_DIR, "agent.pem"),
    key_file: str = os.path.join(REDPEPPER_CONFIG_DIR, "agent-key.pem"),
    config_file: str = os.path.join(
        REDPEPPER_CONFIG_DIR, "agent.d", "01-step-ca-certificate.yaml"
    ),
    steppath: str = DEFAULT_STEP_PATH,
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
    root_fingerprint: str | None = None,
    ca_url: str = "https://localhost:5003",
    cert_file: str = os.path.join(REDPEPPER_CONFIG_DIR, "manager.pem"),
    key_file: str = os.path.join(REDPEPPER_CONFIG_DIR, "manager-key.pem"),
    config_file: str = os.path.join(
        REDPEPPER_CONFIG_DIR, "manager.d", "01-step-ca-certificate.yaml"
    ),
    steppath: str = DEFAULT_STEP_PATH,
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
    root_fingerprint: str | None = None,
    ca_url: str = "https://localhost:5003",
    cert_file: str = os.path.join(REDPEPPER_CONFIG_DIR, "api.pem"),
    key_file: str = os.path.join(REDPEPPER_CONFIG_DIR, "api-key.pem"),
    config_file: str = os.path.join(
        REDPEPPER_CONFIG_DIR, "manager.d", "01-step-ca-api-certificate.yaml"
    ),
    steppath: str = DEFAULT_STEP_PATH,
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