# Data

"Data" in this context refers to data, intended to be distributed to agents, stored in the manager's configuration directory.
For Salt Stack users, this compares to the "pillar" and also files stored along with the state files.
Data includes but is not limited to configuration files for other services, passwords, and parameters for use in scripts.

An agent can only access data for the groups to which it belongs.

Data for a group is defined in a YAML file with the group's name in the `data` directory.
Any data you wish for the agent to be able to access can be defined in these files.
You can also put files you wish for the agent to access in a subdirectory of `data` with the group's name.
You can define data specific to a single agent by defining it under the `data` subkey of that agent's entry in `agents.yml`.

Any data defined in any group is overridden data with the same name in subsequently defined groups.
Agent-specific data overrrides any group-specific data.

Data is sent to authenticated agents upon request.
