import base64
import secrets

import argon2
import pyotp
import qrcode
import typer


def install_login(username: str, config_path: str):
    password = secrets.token_urlsafe(32)
    password_hash = argon2.PasswordHasher().hash(password)
    totp_secret = base64.b32encode(secrets.token_bytes(32)).decode()
    with open(config_path, "w") as f:
        f.write("api_logins:\n")
        f.write(f'  - username: "{username}"\n')
        f.write(f'    password_hash: "{password_hash}"\n')
        f.write(f'    totp_secret: "{totp_secret}"\n')
    typer.echo(f"Login credentials written to {config_path}")
    typer.echo(f"Username: {username}")
    typer.echo(f"Password: {password}")
    typer.echo(f"TOTP secret: {totp_secret}")
    typer.echo("Please store these credentials securely.")
    uri = pyotp.TOTP(
        totp_secret, name=username, issuer="RedPepper API"
    ).provisioning_uri()
    qr = qrcode.QRCode()  # type: ignore
    qr.add_data(uri)
    qr.print_ascii(invert=True)
