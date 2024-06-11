# Requests

A "request" in the context of RedPepper refers to a procedure
that an agent can ask to be performed _by the manager_ and receive the results.

Requests are implemented as callable named `call` in a request module named after the request.
This callable can be async or non-async.
The parameters and return value of this callable are transmitted using JSON,
so they must be JSON-compatible.

Builtin requests are in submodules of `redpepper.requests`.
All agents can request these.

You can put custom request modules under group-named folders
in the `requests` subdirectory of the manager's agent-data directory.
Only the agents that belong to a group can request that group's requests.
