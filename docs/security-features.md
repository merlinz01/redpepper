# Security Features

RedPepper aims to be fully secure by default where possible.

## TLS key permissions

RedPepper errors if TLS keys provided have insecure permissions.

## Agent authentication

RedPepper has a multi-factor method of authenticating agents. See [Agent Authentication](authentication.md).

## Group-based agent access control

Agents can only access data and states for the groups to which they belong. Groups are defined on the manager in `groups.yml`.

## Requested filename checking

Agents requests for data files with path components starting in `.` or which contain a backslash will fail in order to prevent asking for files outside the data directory.

## RedPepper API authentication

The Manager's REST API (and therefore the web console also) requires two-factor login using a username/password and a user-specific time-based one-time password (TOTP).
Usernames, passwords, and TOTP secrets are configured in the manager configuration under the `api_logins` key.

The API attempts to take a constant time when checking usernames and passwords in order to prevent timing attacks.

Authentication status is stored in a session cookie which must be passed along with all API requests.

> RedPepper does _not_ currently enforce any password complexity requirements, but that would be a good feature to be added in the future.

> RedPepper does _not_ currently integrate with external authentication systems (like SAML SSO, LDAP, etc.). That could be added if needed.

> RedPepper does _not_ currently have any per-user access-control functionality. That could be added if needed.

## Best practices

To ensure the security of your RedPepper setup, we recommend following these best practices:

- Keep your TLS private keys secure (`chmod 0600`).
- Don't use self-signed certificates.
- Assign strict IP address ranges for each agent.
- The setup script generates an authentication secret on the agent's machine. If you change this, make sure it is a securely generated random value of sufficient length.
- Make sure you trust all your custom operation modules.
- The setup script generates an API session secret key. If you change this key, make sure to use a securely generated random value of sufficient length.
- The setup script generates a default "admin" login for the API. If you edit the logins, make sure to use suffiently strong passwords.
- Make sure to set each API user's TOTP secret to a securely generated random value of sufficient length.
- Keep all dependencies up to date.
- Regularly backup your data.
