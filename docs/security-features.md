
# Security Features

RedPepper aims to be fully secure by default where possible.
You will still have to provide your own TLS key-pairs.

DO NOT use the certificates and keys in the `example` directory in production.

## TLS key permissions

RedPepper errors if the TLS keys provided have insecure permissions.

## Agent authentication

See [Agent Authentication](authentication.md).

## Group-based agent access control

Agents can only access data and states for the groups to which they belong. Groups are defined by the manager in `groups.yml`.

## Requested filename checking

Agents requests for data files with path components starting in `.` or which contain a backslash will fail in order to prevent asking for files outside the data directory.

## Best practices

To ensure the security of your RedPepper setup, we recommend following these best practices:

- Keep your TLS private keys secure (`chmod 0600`).
- Don't use self-signed certificates.
- DO NOT use the sample certificates and keys from this repository in production.
- Assign strict IP address ranges for each agent.
- Use a sufficiently large and securely generated pre-shared secret for each agent.
- Keep all dependencies up to date.
- Regularly backup your data.

You can set up your own private Certificate Authority using [Smallstep CA](https://github.com/smallstep/certificates)
for a fairly simple and reliable agent certificate provisioning process.
