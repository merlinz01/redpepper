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

## RedPepper API authentication

The Manager's REST API requires two-factor login using a username/password and a Time-based One-Time Password.
Usernames and passwords are configured in `manager.yml`.

The API attempts to take a constant time when checking usernames and passwords in order to prevent timing attacks.

Authentication status is stored in a session cookie which must be passed along with all API requests.

> RedPepper does _not_ currently enforce any password complexity requirements, but that would be a good feature to be added in the future.

> RedPepper does _not_ currently integrate with external authentication systems (like SAML SSO, LDAP, etc.). That could be added if needed.

## Best practices

To ensure the security of your RedPepper setup, we recommend following these best practices:

- Keep your TLS private keys secure (`chmod 0600`).
- Don't use self-signed certificates.
- DO NOT use the sample certificates and keys from this repository in production.
- Assign strict IP address ranges for each agent.
- Use a sufficiently large and securely generated pre-shared secret for each agent.
- Make sure you trust all your custom state modules.
- Make sure to change the API session secret key to a securely generated random value of sufficient length.
- Make sure to change the API TOTP secret to a securely generated random value of sufficient length.
- Keep all dependencies up to date.
- Regularly backup your data.

You can set up your own private Certificate Authority using [Smallstep CA](https://github.com/smallstep/certificates)
for a fairly simple and reliable agent certificate provisioning process.
