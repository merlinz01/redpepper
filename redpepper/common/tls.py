import os
import ssl


def load_tls_context(
    purpose,
    cert_file,
    key_file,
    key_password,
    verify_mode=None,
    check_hostname=None,
    cafile=None,
    capath=None,
    cadata=None,
):
    if key_file and os.stat(key_file).st_mode & 0o77 != 0:
        raise ValueError(
            "TLS key file %s is insecure, please set permissions to 600" % key_file,
        )
    tls_context = ssl.create_default_context(purpose)
    if cert_file:
        tls_context.load_cert_chain(cert_file, keyfile=key_file, password=key_password)
    if not isinstance(check_hostname, bool):
        raise ValueError("tls_check_hostname must be a boolean")
    if check_hostname is not None:
        tls_context.check_hostname = check_hostname
    if verify_mode is None:
        pass
    elif verify_mode == "none":
        tls_context.verify_mode = ssl.CERT_NONE
    elif verify_mode == "optional":
        tls_context.verify_mode = ssl.CERT_OPTIONAL
    elif verify_mode == "required":
        tls_context.verify_mode = ssl.CERT_REQUIRED
    else:
        raise ValueError("Unknown TLS verify mode: %s" % verify_mode)
    if capath or cafile or cadata:
        tls_context.load_verify_locations(cafile=cafile, capath=capath, cadata=cadata)
    return tls_context
