### Authentication

Agents are authenticated by the following things:

- the SHA256 hash of their TLS certificate
- the SHA256 hash of a pre-shared secret
- (optional but recommended) client certificate validation
- an allowed IP address range (or ranges)

If all of these authentication tests succeed, the agent's claimed name is accepted.

Each agent that wishes to connect to the manager must have
a corresponding entry in `agents.yml`
which defines security parameters for that agent.
Each entry must include the following items:

- `cert_hash`: the SHA256 hash of the client's DER-encoded TLS certificate
- `secret_hash`: the SHA256 hash of the pre-shared secret associated with the agent
- `allowed_ips`: an IP range (or a list of them) in CIDR notation specifying the allowed IP address ranges for the agent

Client certificate validation is controlled by the `tls_*` settings in `manager.yml`.
