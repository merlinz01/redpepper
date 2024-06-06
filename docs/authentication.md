### Authentication

Agents are authenticated by the following things:

- the SHA256 hash of a pre-shared secret
- (optional but highly recommended) client certificate validation
- an allowed IP address range (or ranges)

If all of these authentication tests succeed, the agent's claimed name is accepted.

Each agent that wishes to connect to the manager must have
a corresponding entry in `agents.yml`
which defines agent-specific parameters.
Each entry must include the following items:

- `secret_hash`: the SHA256 hash of the pre-shared secret associated with the agent
- `allowed_ips`: an IP range (or a list of them) in CIDR notation specifying the allowed IP address ranges for the agent

Client certificate validation is controlled by the `tls_*` settings in `manager.yml`.

You can set up your own private Certificate Authority using [Smallstep CA](https://github.com/smallstep/certificates)
for a fairly simple and reliable agent certificate provisioning process.
See [Installation](installation.md) for how to do this.
