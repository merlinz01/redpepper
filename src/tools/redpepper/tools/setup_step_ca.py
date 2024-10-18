import os
import secrets
import subprocess

import typer


def setup_step_ca(steppath: str, stepbinary: str, hostname: str):
    # Create the config directory if it doesn't exist
    if not os.path.exists(steppath):
        typer.echo(f"Creating config directory: {steppath}")
        os.makedirs(steppath, mode=0o700, exist_ok=True)

    # Create the secrets directory if it doesn't exist
    secrets_dir = os.path.join(steppath, "secrets")
    if not os.path.exists(secrets_dir):
        typer.echo("Creating secrets directory")
        os.mkdir(secrets_dir, mode=0o700)

    # Create the certs directory if it doesn't exist
    certs_dir = os.path.join(steppath, "certs")
    if not os.path.exists(certs_dir):
        typer.echo("Creating certs directory")
        os.mkdir(certs_dir, mode=0o700)

    # Generate the provisioning token
    token_file = os.path.join(secrets_dir, "provisioner-password")
    if not os.path.exists(token_file):
        typer.echo("Generating provisioning token")
        with open(token_file, "w") as f:
            token = secrets.token_hex(32)
            f.write(token)

    # Generate the root certificate password
    password_file_root = os.path.join(secrets_dir, "key-password-root")
    if not os.path.exists(password_file_root):
        typer.echo("Generating root key password")
        with open(password_file_root, "w") as f:
            password = secrets.token_hex(32)
            f.write(password)

    # Generate the intermediate certificate password
    password_file_intermediate = os.path.join(secrets_dir, "key-password-intermediate")
    if not os.path.exists(password_file_intermediate):
        typer.echo("Generating intermediate key password")
        with open(password_file_intermediate, "w") as f:
            password = secrets.token_hex(32)
            f.write(password)

    # Initialize the CA
    typer.echo("Initializing the CA")
    if subprocess.run(
        [
            stepbinary,
            "ca",
            "init",
            "--name",
            "RedPepper CA",
            "--dns",
            hostname,
            "--dns",
            "localhost",
            "--address",
            ":5003",
            "--password-file",
            password_file_root,
            "--provisioner",
            "redpepper",
            "--provisioner-password-file",
            token_file,
        ],
        env={"STEPPATH": steppath},
    ).returncode:
        raise typer.Abort()

    # Change the intermediate key password
    typer.echo("Changing the intermediate key password")
    if subprocess.run(
        [
            stepbinary,
            "crypto",
            "change-pass",
            os.path.join(secrets_dir, "intermediate_ca_key"),
            "--password-file",
            password_file_root,
            "--new-password-file",
            password_file_intermediate,
            "--force",
        ],
    ).returncode:
        raise typer.Abort()

    typer.secho(
        f"\nThe CA has been initialized at {os.path.abspath(steppath)}.\n",
        fg=typer.colors.BRIGHT_GREEN,
    )
    typer.echo("The root CA certificate fingerprint is ", nl=False)
    typer.secho(
        subprocess.check_output(
            [
                stepbinary,
                "certificate",
                "fingerprint",
                os.path.join(certs_dir, "root_ca.crt"),
            ]
        )
        .decode()
        .strip(),
        fg=typer.colors.BRIGHT_YELLOW,
    )
    typer.echo(f"The provisioner password is at {token_file}\n")
    typer.secho("#" * 103, fg=typer.colors.BRIGHT_RED)
    typer.secho(
        "\nYou must now remove the root CA key and its password from the server and store it in a secure location.\n",
        fg=typer.colors.BRIGHT_RED,
    )
    typer.secho("#" * 103, fg=typer.colors.BRIGHT_RED)

    typer.secho(
        "\nFor increased security, generate the root CA key on an air-gapped machine"
        " and use it to bootstrap the CA according to the documentation.",
        fg=typer.colors.BRIGHT_BLUE,
    )
    typer.secho(
        "https://smallstep.com/docs/step-ca/certificate-authority-server-production/#safeguard-your-root-and-intermediate-keys",
        fg=typer.colors.BRIGHT_BLUE,
    )


SYSTEMD_SERVICE_FILE = """
; This file is based on the service file in the step-ca documentation.

[Unit]
Description=Step CA service for RedPepper
Documentation=https://smallstep.com/docs/step-ca
Documentation=https://smallstep.com/docs/step-ca/certificate-authority-server-production
Documentation=https://github.com/merlinz01/redpepper
After=network-online.target
Wants=network-online.target
StartLimitIntervalSec=30
StartLimitBurst=3
ConditionFileNotEmpty={steppath}/config/ca.json
ConditionFileNotEmpty={steppath}/secrets/key-password-intermediate

[Service]
Type=simple
User={stepuser}
Group={stepuser}
Environment=STEPPATH={steppath}
WorkingDirectory={steppath}
ExecStart={stepcabinary} config/ca.json --password-file secrets/key-password-intermediate
ExecReload=/bin/kill --signal HUP $MAINPID
Restart=on-failure
RestartSec=5
TimeoutStopSec=30
StartLimitInterval=30
StartLimitBurst=3

; Process capabilities & privileges
AmbientCapabilities=CAP_NET_BIND_SERVICE
CapabilityBoundingSet=CAP_NET_BIND_SERVICE
SecureBits=keep-caps
NoNewPrivileges=yes

; Sandboxing
ProtectSystem=full
ProtectHome=true
RestrictNamespaces=true
RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6
PrivateTmp=true
PrivateDevices=true
ProtectClock=true
ProtectControlGroups=true
ProtectKernelTunables=true
ProtectKernelLogs=true
ProtectKernelModules=true
LockPersonality=true
RestrictSUIDSGID=true
RemoveIPC=true
RestrictRealtime=true
SystemCallFilter=@system-service
SystemCallArchitectures=native
MemoryDenyWriteExecute=true
ReadWriteDirectories={steppath}/db

[Install]
WantedBy=multi-user.target
"""


def install_step_ca_systemd_service(
    steppath: str,
    stepcabinary: str,
    stepuser: str,
):
    # Write the systemd service file
    systemd_dir = "/etc/systemd/system"
    service_file = os.path.join(systemd_dir, "redpepper-step-ca.service")
    typer.echo(f"Writing the systemd service file to {service_file}")
    with open(service_file, "w") as f:
        f.write(
            SYSTEMD_SERVICE_FILE.format(
                steppath=steppath,
                stepcabinary=stepcabinary,
                stepuser=stepuser,
            )
        )
    typer.secho(
        "The redpepper-step-ca service is now installed.", fg=typer.colors.BRIGHT_GREEN
    )
